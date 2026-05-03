"""Cloudflare bypass: curl_cffi (TLS fingerprint) or FlareSolverr (full browser)."""

from __future__ import annotations

from typing import Any

import requests

from .log import get_logger

log = get_logger()

_DEFAULT_TIMEOUT = 60000


def is_available(config: dict[str, Any]) -> bool:
    """Check if FlareSolverr is reachable."""
    url = config.get("flaresolverr_url", "")
    if not url:
        return False
    try:
        s = requests.Session()
        s.trust_env = False
        resp = s.get(url.replace("/v1", ""), timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def solve_url(
    url: str,
    config: dict[str, Any],
    *,
    max_timeout: int = _DEFAULT_TIMEOUT,
    session_id: str | None = None,
    skip_curl_cffi: bool = False,
) -> dict[str, Any] | None:
    """Solve anti-bot challenges.

    Priority: curl_cffi (fast, TLS fingerprint) → FlareSolverr (full browser, Docker).
    Set skip_curl_cffi=True when caller already knows TLS fingerprint won't work.
    """
    # curl_cffi first — pure HTTP, no browser, handles TLS fingerprint detection
    if not skip_curl_cffi:
        result = _solve_curl_cffi(url, config)
        if result:
            return result

    # FlareSolverr fallback — full headless browser, handles complex CAPTCHA
    result = _solve_flaresolverr(url, config, max_timeout=max_timeout, session_id=session_id)
    if result:
        return result

    return None


def _solve_curl_cffi(url: str, config: dict[str, Any]) -> dict[str, Any] | None:
    """Use curl_cffi to bypass TLS fingerprint-based Cloudflare detection."""
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        log.debug("curl_cffi not installed, skipping")
        return None

    try:
        log.info(f"curl_cffi: fetching {url}")
        resp = cffi_requests.get(url, impersonate="chrome", timeout=20)
        if resp.status_code >= 400:
            log.info(f"curl_cffi: HTTP {resp.status_code}")
            return None

        # Check if still blocked by Cloudflare
        if _is_cloudflare_block(resp):
            log.info("curl_cffi: still blocked by Cloudflare, trying FlareSolverr")
            return None

        cookies = [{"name": k, "value": v} for k, v in resp.cookies.items()]
        log.info(f"curl_cffi: ok, status={resp.status_code}")
        return {
            "status": "ok",
            "solution": {
                "url": str(resp.url),
                "status": resp.status_code,
                "response": resp.text,
                "cookies": cookies,
            },
        }
    except Exception as e:
        log.debug(f"curl_cffi: error - {e}")
        return None


def _is_cloudflare_block(resp: Any) -> bool:
    """Check if response is a Cloudflare block page."""
    if resp.status_code not in (403, 503):
        return False
    server = str(resp.headers.get("server", "")).lower()
    if "cloudflare" not in server:
        return False
    try:
        body = resp.text[:2000].lower()
        if "challenge-platform" in body or "cf-browser-verification" in body:
            return True
    except Exception:
        pass
    return True


def _solve_flaresolverr(
    url: str,
    config: dict[str, Any],
    *,
    max_timeout: int = _DEFAULT_TIMEOUT,
    session_id: str | None = None,
) -> dict[str, Any] | None:
    """Use FlareSolverr to solve anti-bot challenges."""
    flaresolverr_url = config.get("flaresolverr_url", "")
    if not flaresolverr_url:
        return None
    if not flaresolverr_url.endswith("/v1"):
        flaresolverr_url = flaresolverr_url.rstrip("/") + "/v1"

    payload: dict[str, Any] = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": max_timeout,
    }
    if session_id:
        payload["session"] = session_id

    try:
        log.info(f"FlareSolverr: solving {url}")
        resp = requests.post(flaresolverr_url, json=payload, timeout=max_timeout / 1000 + 10)
        if resp.status_code != 200:
            log.info(f"FlareSolverr: HTTP {resp.status_code}")
            return None
        data = resp.json()
        if data.get("status") != "ok":
            log.info(f"FlareSolverr: {data.get('status')} - {data.get('message', '')}")
            return None
        solution = data.get("solution", {})
        log.info(f"FlareSolverr: solved, status={solution.get('status')}")
        return data
    except Exception as e:
        log.info(f"FlareSolverr: unavailable ({type(e).__name__})")
        return None


def get_cookies(
    url: str,
    config: dict[str, Any],
    *,
    max_timeout: int = _DEFAULT_TIMEOUT,
) -> dict[str, str] | None:
    """Solve challenges and return cookies as a dict."""
    result = solve_url(url, config, max_timeout=max_timeout)
    if not result:
        return None
    solution = result.get("solution", {})
    cookies = solution.get("cookies", [])
    if isinstance(cookies, list):
        return {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}
    return None


def get_html(
    url: str,
    config: dict[str, Any],
    *,
    max_timeout: int = _DEFAULT_TIMEOUT,
) -> str | None:
    """Solve challenges and return the page HTML."""
    result = solve_url(url, config, max_timeout=max_timeout)
    if not result:
        return None
    solution = result.get("solution", {})
    return solution.get("response")


def create_session(config: dict[str, Any], session_id: str) -> bool:
    """Create a persistent FlareSolverr session for cookie reuse."""
    flaresolverr_url = config.get("flaresolverr_url", "")
    if not flaresolverr_url:
        return False
    try:
        resp = requests.post(flaresolverr_url, json={
            "cmd": "sessions.create",
            "session": session_id,
        }, timeout=10)
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except Exception:
        return False


def destroy_session(config: dict[str, Any], session_id: str) -> None:
    """Destroy a FlareSolverr session."""
    flaresolverr_url = config.get("flaresolverr_url", "")
    if not flaresolverr_url:
        return
    try:
        requests.post(flaresolverr_url, json={
            "cmd": "sessions.destroy",
            "session": session_id,
        }, timeout=5)
    except Exception:
        pass
