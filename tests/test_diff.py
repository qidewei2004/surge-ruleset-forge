"""构建 diff 逻辑测试。"""

from forge.diff import diff_category
from forge.models import Rule


def test_diff_new_file(tmp_path):
    out = tmp_path / "x.list"  # 不存在
    rules = [Rule("DOMAIN", "a.com")]
    d = diff_category(out, rules)
    assert d.is_new
    assert d.added == ["DOMAIN,a.com"]
    assert d.removed == []
    assert d.changed


def test_diff_added_and_removed(tmp_path):
    out = tmp_path / "x.list"
    out.write_text(
        "# header\nDOMAIN,keep.com\nDOMAIN,gone.com\n", encoding="utf-8"
    )
    new_rules = [Rule("DOMAIN", "keep.com"), Rule("DOMAIN", "new.com")]
    d = diff_category(out, new_rules)
    assert not d.is_new
    assert d.added == ["DOMAIN,new.com"]
    assert d.removed == ["DOMAIN,gone.com"]
    assert d.changed


def test_diff_no_change(tmp_path):
    out = tmp_path / "x.list"
    out.write_text("# header\nDOMAIN,a.com\nDOMAIN-SUFFIX,b.com\n", encoding="utf-8")
    new_rules = [Rule("DOMAIN", "a.com"), Rule("DOMAIN-SUFFIX", "b.com")]
    d = diff_category(out, new_rules)
    assert not d.is_new
    assert d.added == []
    assert d.removed == []
    assert not d.changed


def test_diff_ignores_comments_and_blanks(tmp_path):
    out = tmp_path / "x.list"
    out.write_text(
        "# comment\n\nDOMAIN,a.com\n# another\n", encoding="utf-8"
    )
    d = diff_category(out, [Rule("DOMAIN", "a.com")])
    assert d.added == []
    assert d.removed == []
