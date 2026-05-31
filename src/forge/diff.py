"""构建 diff:对比新旧产物的规则集,报告新增/移除。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Rule


@dataclass(slots=True)
class CategoryDiff:
    output: str
    added: list[str]  # 新增规则(渲染形式 TYPE,value)
    removed: list[str]  # 移除规则
    is_new: bool  # 该产物此前不存在(首次构建)

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed) or self.is_new


def _existing_rule_lines(path: Path) -> set[str]:
    """读取已有产物中的规则体行(去注释、去空行)。"""
    if not path.exists():
        return set()
    lines: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.add(s)
    return lines


def diff_category(path: Path, new_rules: list[Rule]) -> CategoryDiff:
    """对比 path 处的旧产物与 new_rules,返回新增/移除。"""
    is_new = not path.exists()
    old = _existing_rule_lines(path)
    new = {r.render() for r in new_rules}

    added = sorted(new - old)
    removed = sorted(old - new)
    return CategoryDiff(
        output=path.stem,
        added=added,
        removed=removed,
        is_new=is_new,
    )
