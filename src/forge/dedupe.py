"""规则去重与归并。

两层处理:
1. 精确去重:完全相同的 (type, value) 只保留一条。
2. 子域归并:若已有 DOMAIN-SUFFIX,a.com,则 DOMAIN/DOMAIN-SUFFIX 的
   子域(如 x.a.com)被其覆盖,可安全移除,缩小规则集体积。
"""

from __future__ import annotations

from .models import Rule


def _covered_by_suffix(domain: str, suffixes: set[str]) -> bool:
    """判断 domain 是否被 suffixes 中某个后缀覆盖。

    a.com 覆盖 a.com 本身以及 *.a.com;但不覆盖 xa.com。
    """
    labels = domain.split(".")
    # 逐级向上检查:x.y.a.com -> y.a.com -> a.com
    for i in range(len(labels)):
        candidate = ".".join(labels[i:])
        if candidate in suffixes:
            return True
    return False


def dedupe(rules: list[Rule]) -> list[Rule]:
    """精确去重 + 子域归并,保持原始相对顺序。"""
    # 第一层:精确去重。
    seen: set[tuple[str, str]] = set()
    unique: list[Rule] = []
    for r in rules:
        key = (r.rtype, r.value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    # 收集所有 DOMAIN-SUFFIX 值,作为覆盖判定基准。
    suffixes = {r.value for r in unique if r.rtype == "DOMAIN-SUFFIX"}

    # 第二层:剔除被后缀覆盖的 DOMAIN / DOMAIN-SUFFIX。
    result: list[Rule] = []
    for r in unique:
        if r.rtype == "DOMAIN" and _covered_by_suffix(r.value, suffixes):
            continue
        if r.rtype == "DOMAIN-SUFFIX":
            # 自身不参与覆盖自己;检查是否有更短的父后缀已覆盖它。
            parent = r.value.split(".", 1)
            if len(parent) == 2 and _covered_by_suffix(parent[1], suffixes):
                continue
        result.append(r)
    return result


def sort_rules(rules: list[Rule]) -> list[Rule]:
    """稳定排序:先按类型,再按域名反转标签(便于同源域名聚集)。"""

    def key(r: Rule) -> tuple[str, str]:
        if r.rtype in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD"}:
            reversed_domain = ".".join(reversed(r.value.split(".")))
            return (r.rtype, reversed_domain)
        return (r.rtype, r.value)

    return sorted(rules, key=key)
