"""规则数据模型与类型规范化。"""

from __future__ import annotations

from dataclasses import dataclass

# Surge 支持的非 IP(域名维度)规则类型。
DOMAIN_TYPES = frozenset(
    {
        "DOMAIN",
        "DOMAIN-SUFFIX",
        "DOMAIN-KEYWORD",
        "DOMAIN-WILDCARD",
        "DOMAIN-SET",
    }
)

# IP 维度规则类型,需配合 no-resolve,通常放在独立的 IP 规则层。
IP_TYPES = frozenset(
    {
        "IP-CIDR",
        "IP-CIDR6",
        "IP-ASN",
        "GEOIP",
    }
)

# 受支持的全部规则类型。其余类型(USER-AGENT / PROCESS-NAME / 逻辑规则等)
# 不适合放进可复用规则集,解析时丢弃。
SUPPORTED_TYPES = DOMAIN_TYPES | IP_TYPES


@dataclass(frozen=True, slots=True)
class Rule:
    """一条规范化后的规则。

    rtype: 规则类型(大写),如 DOMAIN-SUFFIX。
    value: 规则值(小写化的域名 / 原样保留的 IP 段)。
    """

    rtype: str
    value: str

    def render(self) -> str:
        """渲染为 Surge .list 中的一行。"""
        return f"{self.rtype},{self.value}"


def normalize(rtype: str, value: str) -> Rule | None:
    """规范化单条规则;无法识别或不受支持时返回 None。"""
    rtype = rtype.strip().upper()
    value = value.strip()
    if not rtype or not value:
        return None
    if rtype not in SUPPORTED_TYPES:
        return None
    # 域名统一小写,避免大小写导致的重复;IP/ASN 保持原样。
    if rtype in DOMAIN_TYPES:
        value = value.lower()
    return Rule(rtype=rtype, value=value)
