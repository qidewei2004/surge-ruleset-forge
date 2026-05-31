"""并发下载上游规则源,带重试与本地缓存。"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import httpx

CACHE_DIR = Path(".cache")
USER_AGENT = "surge-ruleset-forge/0.1 (+https://github.com/qidewei/surge-ruleset-forge)"


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.txt"


def fetch_one(
    client: httpx.Client,
    url: str,
    *,
    retries: int = 3,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> str:
    """下载单个 URL 的文本内容。

    失败时按指数退避重试;全部失败后若有可用缓存则回退到缓存,
    否则抛出最后一次异常。
    """
    cache = _cache_path(url)
    if use_cache and cache.exists():
        age = time.time() - cache.stat().st_mtime
        if age < cache_ttl:
            return cache.read_text(encoding="utf-8")

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = client.get(url, timeout=20.0, follow_redirects=True)
            resp.raise_for_status()
            text = resp.text
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(text, encoding="utf-8")
            return text
        except (httpx.HTTPError, httpx.StreamError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)

    # 网络彻底失败时,过期缓存也好过没有,保证构建不中断。
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    raise RuntimeError(f"下载失败: {url}") from last_exc


def fetch_all(urls: list[str], **kwargs) -> dict[str, str]:
    """串行下载多个 URL(共享连接)。返回 url -> 文本 的映射。

    单个源失败不会中断整体,记为返回值中缺失的键由调用方处理。
    """
    headers = {"User-Agent": USER_AGENT}
    results: dict[str, str] = {}
    with httpx.Client(headers=headers, http2=False) as client:
        for url in urls:
            try:
                results[url] = fetch_one(client, url, **kwargs)
            except RuntimeError as exc:
                print(f"  [warn] {exc}")
    return results
