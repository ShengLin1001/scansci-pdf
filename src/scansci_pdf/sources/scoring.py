"""Adaptive source scoring with exponential moving average (EMA).

Tracks per-source success rate and latency. Uses EMA so:
- Recent results have higher weight
- Temporary network blips don't permanently ruin a source's score
- Scores naturally recover when a source starts working again
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..config import DATA_DIR

_SCORES_FILE = DATA_DIR / "source_scores.json"

# EMA decay factor: higher = more weight on recent data (0.05-0.2 typical)
_ALPHA = 0.1

# Initial score for unknown sources (neutral)
_DEFAULT_SCORE = 0.5


def _load_scores() -> dict[str, dict[str, Any]]:
    if _SCORES_FILE.exists():
        try:
            with _SCORES_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_scores(scores: dict[str, dict[str, Any]]) -> None:
    _SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _SCORES_FILE.open("w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)


def record_result(source: str, success: bool, latency_ms: float = 0, error_type: str = "") -> None:
    """Record a download attempt result for adaptive scoring."""
    scores = _load_scores()
    entry = scores.get(source, {
        "success_ema": _DEFAULT_SCORE,
        "latency_ema": 5000.0,
        "attempts": 0,
        "last_error": "",
        "last_update": 0,
    })

    # Update success EMA
    success_val = 1.0 if success else 0.0
    entry["success_ema"] = _ALPHA * success_val + (1 - _ALPHA) * entry["success_ema"]

    # Update latency EMA (only on success)
    if success and latency_ms > 0:
        entry["latency_ema"] = _ALPHA * latency_ms + (1 - _ALPHA) * entry["latency_ema"]

    entry["attempts"] = entry.get("attempts", 0) + 1
    entry["last_error"] = error_type if not success else ""
    entry["last_update"] = int(time.time())

    scores[source] = entry
    _save_scores(scores)


def get_score(source: str) -> float:
    """Get adaptive score for a source (0.0-1.0, higher = better)."""
    scores = _load_scores()
    entry = scores.get(source)
    if not entry:
        return _DEFAULT_SCORE
    return entry.get("success_ema", _DEFAULT_SCORE)


def get_latency(source: str) -> float:
    """Get EMA latency for a source in ms."""
    scores = _load_scores()
    entry = scores.get(source)
    if not entry:
        return 5000.0
    return entry.get("latency_ema", 5000.0)


def sort_sources(sources: list[tuple[Any, str]]) -> list[tuple[Any, str]]:
    """Sort sources by adaptive score (best first), with latency as tiebreaker."""
    def _key(item: tuple[Any, str]) -> tuple[float, float]:
        _, label = item
        score = get_score(label)
        latency = get_latency(label)
        # Higher score first, lower latency first
        return (-score, latency)
    return sorted(sources, key=_key)


def classify_error(resp_status: int = 0, exception: Exception | None = None, html: str = "") -> str:
    """Classify download error into a category."""
    if resp_status == 404:
        return "not_found"
    if resp_status == 403:
        return "forbidden"
    if resp_status == 429:
        return "rate_limited"
    if resp_status >= 500:
        return "server_error"
    if exception and "timeout" in str(exception).lower():
        return "timeout"
    if exception and "ssl" in str(exception).lower():
        return "ssl_error"
    if html and ("captcha" in html.lower() or "challenge" in html.lower()):
        return "captcha"
    return "unknown"


def get_user_advice(error_type: str, source: str) -> str:
    """Return user-friendly advice based on error type."""
    advice = {
        "not_found": "论文在此源不存在（404），跳过",
        "forbidden": f"访问被拒绝（403），可能需要机构代理或 VPN",
        "rate_limited": f"请求过于频繁（429），稍后重试",
        "timeout": f"连接超时，可能是网络问题",
        "captcha": f"触发验证码/Cloudflare 防护，需要 FlareSolverr",
        "ssl_error": "SSL 连接错误，可能是网络代理问题",
        "server_error": "服务器错误（5xx），暂时不可用",
    }
    return advice.get(error_type, f"未知错误")


def get_all_scores() -> dict[str, dict[str, Any]]:
    """Return all source scores for diagnostics."""
    return _load_scores()
