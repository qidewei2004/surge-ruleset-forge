"""forge CLI 入口。

用法:
    forge build            # 构建全部分类到 dist/
    forge build --no-cache # 忽略本地缓存,强制重新下载
    forge stats            # 显示当前 dist/ 产物统计
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build

DEFAULT_CONFIG = Path("sources.yaml")
DEFAULT_DIST = Path("dist")


def _cmd_build(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"找不到配置文件: {config_path}", file=sys.stderr)
        return 1
    results = build(config_path, Path(args.dist), use_cache=not args.no_cache)
    total = sum(r.count for r in results)
    failed = [r for r in results if r.sources_ok < r.sources_total]
    print(f"\n完成: {len(results)} 个分类, 共 {total} 条规则.")
    if failed:
        print(f"注意: {len(failed)} 个分类存在下载失败的源,已用可用源继续构建.")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    dist = Path(args.dist)
    files = sorted(dist.glob("*.list"))
    if not files:
        print(f"{dist}/ 下没有产物,先运行 forge build.")
        return 0
    for f in files:
        rules = [
            ln
            for ln in f.read_text(encoding="utf-8").splitlines()
            if ln and not ln.startswith("#")
        ]
        print(f"{f.name:24} {len(rules):>6} rules")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="forge", description="Surge ruleset forge")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="构建全部分类到 dist/")
    p_build.add_argument("-c", "--config", default=str(DEFAULT_CONFIG))
    p_build.add_argument("-d", "--dist", default=str(DEFAULT_DIST))
    p_build.add_argument("--no-cache", action="store_true", help="忽略本地缓存")
    p_build.set_defaults(func=_cmd_build)

    p_stats = sub.add_parser("stats", help="显示 dist/ 产物统计")
    p_stats.add_argument("-d", "--dist", default=str(DEFAULT_DIST))
    p_stats.set_defaults(func=_cmd_stats)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
