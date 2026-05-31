"""构建编排:读取 sources.yaml,逐分类 fetch→parse→filter→dedupe→emit。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .dedupe import dedupe, sort_rules
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


def build(
    config_path: Path,
    dist_dir: Path,
    *,
    use_cache: bool = True,
) -> list[BuildResult]:
    """执行完整构建,返回每个分类的结果摘要。"""
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

        count = emit(
            dist_dir / f"{cat.output}.list",
            merged,
            desc=cat.desc,
            sources=cat.sources,
        )
        result = BuildResult(
            output=cat.output,
            count=count,
            sources_ok=len(fetched),
            sources_total=len(cat.sources),
        )
        results.append(result)
        print(
            f"  -> dist/{cat.output}.list  "
            f"({count} rules, {result.sources_ok}/{result.sources_total} sources)"
        )

    return results
