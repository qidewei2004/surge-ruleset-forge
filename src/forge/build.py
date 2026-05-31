"""构建编排:读取 sources.yaml,逐分类 fetch→parse→filter→dedupe→emit。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .dedupe import dedupe, sort_rules
from .diff import CategoryDiff, diff_category
from .emit import emit
from .fetch import fetch_all
from .models import Rule
from .parse import parse_text


@dataclass(slots=True)
class Category:
    output: str
    desc: str
    sources: list[str]
    keep_types: list[str] | None = None


@dataclass(slots=True)
class Config:
    categories: list[Category] = field(default_factory=list)


def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = data.get("defaults") or {}
    default_keep = defaults.get("keep_types")

    categories: list[Category] = []
    for raw in data.get("categories", []):
        categories.append(
            Category(
                output=raw["output"],
                desc=raw.get("desc", ""),
                sources=list(raw["sources"]),
                keep_types=raw.get("types", default_keep),
            )
        )
    return Config(categories=categories)


def _filter_types(rules: list[Rule], keep: list[str] | None) -> list[Rule]:
    if not keep:
        return rules
    allowed = {t.upper() for t in keep}
    return [r for r in rules if r.rtype in allowed]


@dataclass(slots=True)
class BuildResult:
    output: str
    count: int
    sources_ok: int
    sources_total: int
    diff: CategoryDiff | None = None


def build(
    config_path: Path,
    dist_dir: Path,
    *,
    use_cache: bool = True,
    show_diff: bool = False,
) -> list[BuildResult]:
    """执行完整构建,返回每个分类的结果摘要。

    show_diff: 为 True 时,对比旧产物并在日志中报告规则新增/移除。
    """
    config = load_config(config_path)
    results: list[BuildResult] = []

    for cat in config.categories:
        print(f"[build] {cat.output}  ({len(cat.sources)} sources)")
        fetched = fetch_all(cat.sources, use_cache=use_cache)

        merged: list[Rule] = []
        for url in cat.sources:
            text = fetched.get(url)
            if text is None:
                continue
            merged.extend(parse_text(text))

        merged = _filter_types(merged, cat.keep_types)
        merged = dedupe(merged)
        merged = sort_rules(merged)

        out_path = dist_dir / f"{cat.output}.list"
        # diff 必须在 emit 覆盖文件之前计算
        cat_diff = diff_category(out_path, merged) if show_diff else None

        count = emit(
            out_path,
            merged,
            desc=cat.desc,
            sources=cat.sources,
        )
        result = BuildResult(
            output=cat.output,
            count=count,
            sources_ok=len(fetched),
            sources_total=len(cat.sources),
            diff=cat_diff,
        )
        results.append(result)
        print(
            f"  -> dist/{cat.output}.list  "
            f"({count} rules, {result.sources_ok}/{result.sources_total} sources)"
        )
        if cat_diff is not None:
            _print_diff(cat_diff)

    return results


def _print_diff(d: CategoryDiff, *, max_show: int = 10) -> None:
    """打印单个分类的 diff 摘要。"""
    if d.is_new:
        print(f"     [diff] 新产物,{len(d.added)} 条规则")
        return
    if not d.added and not d.removed:
        print("     [diff] 无变化")
        return
    print(f"     [diff] +{len(d.added)} 新增, -{len(d.removed)} 移除")
    for line in d.added[:max_show]:
        print(f"       + {line}")
    if len(d.added) > max_show:
        print(f"       + ... 另有 {len(d.added) - max_show} 条")
    for line in d.removed[:max_show]:
        print(f"       - {line}")
    if len(d.removed) > max_show:
        print(f"       - ... 另有 {len(d.removed) - max_show} 条")
