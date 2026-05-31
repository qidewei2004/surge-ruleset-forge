"""emit 智能时间戳逻辑的单元测试。"""

from pathlib import Path

from forge.emit import emit
from forge.models import Rule


def _read_updated(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Updated:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("产物缺少 Updated 行")


def _body(path: Path) -> list[str]:
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]


def test_emit_writes_header_and_body(tmp_path):
    out = tmp_path / "x.list"
    rules = [Rule("DOMAIN-SUFFIX", "a.com"), Rule("DOMAIN", "b.com")]
    n = emit(out, rules, desc="test", sources=["http://src"], now="2026-01-01T00:00:00Z")
    assert n == 2
    assert _read_updated(out) == "2026-01-01T00:00:00Z"
    assert _body(out) == ["DOMAIN-SUFFIX,a.com", "DOMAIN,b.com"]


def test_timestamp_preserved_when_rules_unchanged(tmp_path):
    out = tmp_path / "x.list"
    rules = [Rule("DOMAIN", "a.com")]
    emit(out, rules, desc="d", sources=["s"], now="2026-01-01T00:00:00Z")
    first = out.read_bytes()

    # 规则不变,即使传入更晚的 now,也应沿用旧时间戳 -> 字节完全一致。
    emit(out, rules, desc="d", sources=["s"], now="2026-09-09T09:09:09Z")
    assert out.read_bytes() == first
    assert _read_updated(out) == "2026-01-01T00:00:00Z"


def test_timestamp_advances_when_rules_change(tmp_path):
    out = tmp_path / "x.list"
    emit(out, [Rule("DOMAIN", "a.com")], desc="d", sources=["s"], now="2026-01-01T00:00:00Z")

    # 规则变化 -> 时间戳推进到新的 now。
    emit(
        out,
        [Rule("DOMAIN", "a.com"), Rule("DOMAIN", "new.com")],
        desc="d",
        sources=["s"],
        now="2026-02-02T00:00:00Z",
    )
    assert _read_updated(out) == "2026-02-02T00:00:00Z"
    assert "DOMAIN,new.com" in _body(out)


def test_timestamp_not_affected_by_desc_or_sources_change(tmp_path):
    # 仅描述/来源变化(规则体不变)不应推进时间戳——判定基准是规则体。
    out = tmp_path / "x.list"
    rules = [Rule("DOMAIN", "a.com")]
    emit(out, rules, desc="old", sources=["s1"], now="2026-01-01T00:00:00Z")
    emit(out, rules, desc="new desc", sources=["s2"], now="2026-05-05T00:00:00Z")
    assert _read_updated(out) == "2026-01-01T00:00:00Z"


def test_new_file_uses_now(tmp_path):
    out = tmp_path / "fresh.list"
    emit(out, [Rule("DOMAIN", "a.com")], desc="d", sources=["s"], now="2026-03-03T00:00:00Z")
    assert _read_updated(out) == "2026-03-03T00:00:00Z"
