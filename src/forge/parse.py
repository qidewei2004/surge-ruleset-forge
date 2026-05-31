"""解析上游规则文本为规范化的 Rule 列表。"""

from __future__ import annotations

from collections.abc import Iterable

from .models import Rule, normalize

# skk.moe 在规则体里植入的防盗版哨兵域名,需要剔除。
_SENTINEL_MARKERS = ("this_ruleset_is_made_by", "rul35et", "5ukk4w", "sukkaw-ruleset")


def _is_sentinel(value: str) -> bool:
    low = value.lower()
    return any(marker in low for marker in _SENTINEL_MARKERS)


def parse_text(text: str) -> list[Rule]:
    """解析单个上游源文本。

    逐行处理:跳过空行、注释(# 或 ;)、行内注释,
    剥离 Surge 规则参数(如 no-resolve / extended-matching),
    丢弃不受支持的类型与哨兵行。
    """
    rules: list[Rule] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        # 去掉行尾的 // 注释。
        if "//" in line:
            line = line.split("//", 1)[0].strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        rtype, value = parts[0], parts[1]
        rule = normalize(rtype, value)
        if rule is None or _is_sentinel(rule.value):
            continue
        rules.append(rule)
    return rules


def parse_many(texts: Iterable[str]) -> list[Rule]:
    """解析多个源文本,拼成单一规则列表(未去重)。"""
    out: list[Rule] = []
    for text in texts:
        out.extend(parse_text(text))
    return out
