"""parse 与 dedupe 核心逻辑的单元测试。"""

from forge.dedupe import dedupe, sort_rules
from forge.models import Rule
from forge.parse import parse_text


def test_parse_basic_types():
    text = "\n".join(
        [
            "DOMAIN-SUFFIX,example.com",
            "DOMAIN,a.example.com",
            "DOMAIN-KEYWORD,track",
            "IP-CIDR,1.1.1.0/24,no-resolve",
        ]
    )
    rules = parse_text(text)
    assert Rule("DOMAIN-SUFFIX", "example.com") in rules
    assert Rule("DOMAIN", "a.example.com") in rules
    assert Rule("DOMAIN-KEYWORD", "track") in rules
    # IP-CIDR 受支持,参数 no-resolve 被剥离。
    assert Rule("IP-CIDR", "1.1.1.0/24") in rules


def test_parse_skips_comments_and_blank():
    text = "# comment\n\n; another\n// slash\nDOMAIN,keep.com\n"
    rules = parse_text(text)
    assert rules == [Rule("DOMAIN", "keep.com")]


def test_parse_strips_inline_comment():
    rules = parse_text("DOMAIN,keep.com // 保留这个")
    assert rules == [Rule("DOMAIN", "keep.com")]


def test_parse_drops_unsupported_types():
    text = "USER-AGENT,bili*\nPROCESS-NAME,/Applications/X.app,DIRECT\nDOMAIN,ok.com"
    rules = parse_text(text)
    assert rules == [Rule("DOMAIN", "ok.com")]


def test_parse_filters_sukka_sentinel():
    text = "DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe\nDOMAIN,real.com"
    rules = parse_text(text)
    assert rules == [Rule("DOMAIN", "real.com")]


def test_parse_lowercases_domain():
    rules = parse_text("DOMAIN-SUFFIX,Example.COM")
    assert rules == [Rule("DOMAIN-SUFFIX", "example.com")]


def test_dedupe_exact_duplicates():
    rules = [
        Rule("DOMAIN", "a.com"),
        Rule("DOMAIN", "a.com"),
        Rule("DOMAIN-SUFFIX", "b.com"),
    ]
    result = dedupe(rules)
    assert result.count(Rule("DOMAIN", "a.com")) == 1
    assert Rule("DOMAIN-SUFFIX", "b.com") in result


def test_dedupe_subdomain_covered_by_suffix():
    # DOMAIN-SUFFIX,a.com 覆盖 DOMAIN,x.a.com,后者应被移除。
    rules = [
        Rule("DOMAIN-SUFFIX", "a.com"),
        Rule("DOMAIN", "x.a.com"),
        Rule("DOMAIN", "standalone.org"),
    ]
    result = dedupe(rules)
    assert Rule("DOMAIN", "x.a.com") not in result
    assert Rule("DOMAIN-SUFFIX", "a.com") in result
    assert Rule("DOMAIN", "standalone.org") in result


def test_dedupe_child_suffix_collapsed_into_parent():
    # DOMAIN-SUFFIX,a.com 已覆盖 *.a.com,故 DOMAIN-SUFFIX,sub.a.com 冗余。
    rules = [
        Rule("DOMAIN-SUFFIX", "a.com"),
        Rule("DOMAIN-SUFFIX", "sub.a.com"),
    ]
    result = dedupe(rules)
    assert Rule("DOMAIN-SUFFIX", "a.com") in result
    assert Rule("DOMAIN-SUFFIX", "sub.a.com") not in result


def test_dedupe_does_not_overmatch_similar_domain():
    # xa.com 不应被 a.com 覆盖。
    rules = [
        Rule("DOMAIN-SUFFIX", "a.com"),
        Rule("DOMAIN", "xa.com"),
    ]
    result = dedupe(rules)
    assert Rule("DOMAIN", "xa.com") in result


def test_sort_groups_same_apex_domain():
    rules = [
        Rule("DOMAIN-SUFFIX", "z.com"),
        Rule("DOMAIN-SUFFIX", "a.com"),
        Rule("DOMAIN-SUFFIX", "api.a.com"),
    ]
    ordered = [r.value for r in sort_rules(rules)]
    # a.com 系列应聚集相邻。
    assert ordered.index("a.com") + 1 == ordered.index("api.a.com")
