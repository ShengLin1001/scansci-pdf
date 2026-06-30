"""Official-source-only download via a visible browser.

Opens the publisher's REAL site (no WebVPN URL rewriting) in a visible
CloakBrowser and lets you clear any human-verification (Cloudflare) by
hand. PDFs are taken strictly from the publisher — there is no Sci-Hub /
LibGen fallback — so the result is guaranteed to be the official version.

Requires the machine to already have institutional access (on-campus
network or a full-tunnel VPN client); otherwise you will clear the
human-check but hit the publisher paywall.
"""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

from ..identifiers import normalize_doi, safe_filename
from ..log import get_logger
from ..pdf_utils import (
    extract_pdf_url_from_html,
    is_pdf_file,
    is_plausible_pdf_url,
    success,
)
from .instsci import (
    _construct_publisher_pdf_url,
    _extract_inline_pdf,
    _find_pdf_link,
    _is_inline_pdf_page,
    _resolve_doi_url,
)

log = get_logger()

_CHALLENGE_MARKERS = (
    "just a moment",
    "attention required",
    "checking your browser",
    "请稍候",
    "请稍后",
    "正在验证",
    "安全验证",
    "浏览器不支持",
)


def _looks_like_challenge(title: str) -> bool:
    low = title.lower()
    return any(m in low or m in title for m in _CHALLENGE_MARKERS)


# URL fragments that mark a Supplementary-Information / media PDF rather than
# the main article. These must NEVER be saved as the official article PDF.
_SUPPL_MARKERS = (
    "moesm", "mediaobjects", "/media/", "supplementary", "supplement",
    "supp-", "-supp", "_supp", "/suppl", "/esm", "_esm", "si.pdf", "_si.", "/si/",
)


def _is_supplementary(url: str) -> bool:
    low = url.lower()
    return any(m in low for m in _SUPPL_MARKERS)


def _matches_main(url: str, doi: str, pdf_url: str) -> bool:
    """True if `url` looks like the MAIN article PDF (not an SI / wrong PDF)."""
    low = url.lower()
    if _is_supplementary(low):
        return False
    base = low.split("?", 1)[0]
    if pdf_url and base == pdf_url.lower().split("?", 1)[0]:
        return True
    suffix = (doi.split("/", 1)[-1] if "/" in doi else doi).lower()
    if suffix and suffix in low:
        return True
    # Last resort: a plain (non-SI) PDF endpoint — after SI is excluded the
    # article PDF is the only realistic match.
    return (
        base.endswith(".pdf")
        or "/pdf/" in low or "/doi/pdf/" in low
        or "/pdfdirect/" in low or "/articlepdf/" in low
    )


def _make_on_response(captured: list[tuple[str, bytes]]):
    """Capture PDF bodies flowing through the network as (url, body) pairs.

    Supplementary-Information PDFs are dropped here so they can never be
    mistaken for the article.
    """

    def on_response(response: Any) -> None:
        try:
            ct = response.headers.get("content-type", "")
            url = response.url
            is_pdf_ct = "pdf" in ct.lower() or "octet-stream" in ct.lower()
            is_pdf_url = url.lower().endswith(".pdf") or "/pdf/" in url or "/pdfdirect/" in url
            if not (is_pdf_ct or is_pdf_url) or response.status >= 400:
                return
            if _is_supplementary(url):
                log.info(f"   [Browser-Official] skipped supplementary PDF: {url[:70]}")
                return
            body = response.body()
            if len(body) > 5000 and body[:5] == b"%PDF-":
                captured.append((url, body))
                log.info(f"   [Browser-Official] captured PDF {len(body)}B from {url[:60]}")
        except Exception:
            pass

    return on_response


def _make_on_download(captured: list[tuple[str, bytes]]):
    """Capture attachment-style PDF downloads as (url, body) pairs.

    Many publishers (Nature's "Download PDF", IEEE, ACM…) serve the PDF with
    Content-Disposition: attachment, so the browser turns it into a download
    rather than an inline page. For a download the `response` body is no longer
    readable, so without this the PDF is invisible in manual mode. Supplementary
    files are dropped, same as for inline responses.
    """
    import tempfile

    def on_download(download: Any) -> None:
        try:
            url = download.url
            if _is_supplementary(url):
                log.info(f"   [Browser-Official] skipped supplementary download: {url[:70]}")
                return
            tmp = Path(tempfile.gettempdir()) / f"scansci_dl_{int(time.time() * 1000)}.pdf"
            download.save_as(str(tmp))
            body = tmp.read_bytes()
            try:
                tmp.unlink()
            except OSError:
                pass
            if len(body) > 5000 and body[:5] == b"%PDF-":
                captured.append((url, body))
                log.info(f"   [Browser-Official] captured download {len(body)}B from {url[:60]}")
        except Exception:
            pass

    return on_download


def _save_bytes(data: bytes, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return is_pdf_file(output_path)


def _save_best(
    captured: list[tuple[str, bytes]], output_path: Path, doi: str, pdf_url: str
) -> bool:
    """Save the captured PDF that matches the MAIN article; ignore everything else."""
    chosen = None
    for url, body in captured:
        if _matches_main(url, doi, pdf_url):
            chosen = body  # keep the last matching response
    if chosen is None:
        return False
    return _save_bytes(chosen, output_path)


def _fetch_pdf_in_page(page: Any, pdf_url: str) -> bytes | None:
    """Fetch the exact main PDF URL from inside the page (same-origin, credentialed).

    This is the authoritative path: it uses the logged-in session cookies, so it
    returns the article PDF when the user has access and fails cleanly (no SI,
    no paywall HTML) when they don't. Cross-origin URLs (e.g. APS link.aps.org ->
    journals.aps.org) are blocked by CORS and fall through to capture/inline.
    """
    try:
        result = page.evaluate(
            """
            async (url) => {
                try {
                    const resp = await fetch(url, {credentials: 'include'});
                    if (!resp.ok) return {ok: false, status: resp.status};
                    const buf = await resp.arrayBuffer();
                    const b = new Uint8Array(buf);
                    if (b.length < 5000) return {ok: false, status: 'too_small'};
                    if (b[0]!==0x25||b[1]!==0x50||b[2]!==0x44||b[3]!==0x46)
                        return {ok: false, status: 'not_pdf'};
                    let s = '';
                    const chunk = 0x8000;
                    for (let i = 0; i < b.length; i += chunk)
                        s += String.fromCharCode.apply(null, b.subarray(i, i + chunk));
                    return {ok: true, b64: btoa(s)};
                } catch (e) { return {ok: false, status: 'error', msg: String(e)}; }
            }
            """,
            pdf_url,
        )
        if result and result.get("ok"):
            return base64.b64decode(result["b64"])
        log.info(f"   [Browser-Official] in-page fetch not ok: {result}")
    except Exception as exc:
        log.info(f"   [Browser-Official] in-page fetch error: {exc}")
    return None


def _wait_for_human(page: Any, manual_wait: int) -> bool:
    """Poll until the page is past any Cloudflare / login challenge."""
    deadline = time.time() + manual_wait
    while time.time() < deadline:
        time.sleep(3)
        try:
            title = page.title() or ""
            body_len = page.evaluate("document.body ? document.body.innerText.length : 0") or 0
        except Exception:
            continue
        if not _looks_like_challenge(title) and body_len > 400:
            log.info(f"   [Browser-Official] page ready: '{title[:50]}'")
            return True
        log.info(f"   [Browser-Official] waiting for manual verify... title='{title[:40]}'")
    return False


def _grab_in_browser(
    page: Any, context: Any, captured: list[tuple[str, bytes]], pdf_url: str,
    output_path: Path, manual_wait: int, doi: str,
) -> bool:
    """Fetch the MAIN-article PDF only — never a Supplementary-Information PDF.

    Strategy, in order of authority:
      1. Same-origin credentialed fetch of the exact main PDF URL. Uses the
         logged-in session, so it succeeds when the user has access and fails
         cleanly when they don't (it can't return an SI or a paywall page).
      2. For cross-origin PDFs (e.g. APS link.aps.org -> journals.aps.org) the
         fetch is CORS-blocked, so we navigate to the PDF URL and accept either
         a captured network response or an inline viewer — but only if its URL
         matches the main article.

    The loop retries, leaving time for the user to clear Cloudflare and/or log in
    to their institution. The user never needs to click the PDF.
    """
    if not is_plausible_pdf_url(pdf_url):
        return False
    captured.clear()

    # Navigate once to the authoritative main PDF (covers inline viewers and
    # lets cross-origin responses stream through the sniffer).
    try:
        page.goto(pdf_url, wait_until="domcontentloaded", timeout=20000)
    except Exception as exc:
        log.info(f"   [Browser-Official] pdf goto ({exc})")

    print("      正在抓取官方正文 PDF…（如需机构登录或人机验证，请在浏览器里完成；脚本只取正文，忽略 SI）")
    deadline = time.time() + manual_wait
    while time.time() < deadline:
        # 1) Authoritative same-origin fetch of the exact main PDF.
        data = _fetch_pdf_in_page(page, pdf_url)
        if data and _save_bytes(data, output_path):
            return True
        # 2) Cross-origin / streamed: only a captured response matching the article.
        if _save_best(captured, output_path, doi, pdf_url):
            return True
        # 3) Inline viewer, but only if the tab URL is the main article PDF.
        for pg in list(context.pages):
            try:
                if _is_inline_pdf_page(pg) and _matches_main(pg.url, doi, pdf_url):
                    pdf_bytes = _extract_inline_pdf(pg)
                    if pdf_bytes and _save_bytes(pdf_bytes, output_path):
                        return True
            except Exception:
                pass
        time.sleep(3)
    return False


def _grab_manual(
    context: Any, captured: list[tuple[str, bytes]], output_path: Path, manual_wait: int,
) -> bool:
    """Manual mode: the user does everything; we just capture the PDF they open.

    Works on any publisher (incl. IEEE/ACM/Elsevier) because the user handles
    verification, login and opening the PDF. We save the latest non-SI PDF that
    streams through any tab, or an inline PDF the user is viewing.
    """
    captured.clear()
    deadline = time.time() + manual_wait
    while time.time() < deadline:
        if captured:
            url, body = captured[-1]
            if _save_bytes(body, output_path):
                log.info(f"   [Browser-Manual] saved captured PDF from {url[:70]}")
                return True
        for pg in list(context.pages):
            try:
                if _is_inline_pdf_page(pg) and not _is_supplementary(pg.url):
                    pdf_bytes = _extract_inline_pdf(pg)
                    if pdf_bytes and _save_bytes(pdf_bytes, output_path):
                        log.info(f"   [Browser-Manual] saved inline PDF from {pg.url[:70]}")
                        return True
            except Exception:
                pass
        time.sleep(2)
    return False


def _download_one(
    page: Any,
    context: Any,
    captured: list[tuple[str, bytes]],
    doi: str,
    output_path: Path,
    manual_wait: int,
    manual: bool = False,
) -> dict[str, Any] | None:
    captured.clear()
    resolved = _resolve_doi_url(doi) or f"https://doi.org/{doi}"
    log.info(f"   [Browser-Official] {doi} -> {resolved}")
    try:
        page.goto(resolved, wait_until="domcontentloaded", timeout=60000)
    except Exception as exc:
        log.info(f"   [Browser-Official] goto warning: {exc}")

    if manual:
        print(f"  >>> 手动模式：{doi}")
        print("      请自行完成：过人机验证 → 机构登录 → 打开正文 PDF。")
        print(f"      脚本检测到界面里出现 PDF 后会自动保存并进入下一篇（最多等 {manual_wait} 秒；SI 会被忽略）。")
        if _grab_manual(context, captured, output_path, manual_wait):
            return success(doi, output_path, "Publisher(Browser-Manual)")
        print("  [跳过] 未检测到 PDF。")
        return None

    print(f"  >>> 请在浏览器里完成人机验证（官网域名）: {resolved}")
    print(f"      验证通过、显示论文页面后会自动继续，最多等待 {manual_wait} 秒。")
    if not _wait_for_human(page, manual_wait):
        print("  [跳过] 等待人机验证超时。")
        return None

    try:
        html = page.content()
    except Exception:
        html = ""
    pdf_url = (
        _construct_publisher_pdf_url(doi, page.url)
        or _find_pdf_link(html, page.url)
        or extract_pdf_url_from_html(html, page.url)
    )
    if not pdf_url:
        print("  [跳过] 页面里没找到官方 PDF 链接（可能是付费墙）。")
        return None

    log.info(f"   [Browser-Official] official pdf_url: {pdf_url[:90]}")
    print(f"      官方正文 PDF: {pdf_url}")
    if _grab_in_browser(page, context, captured, pdf_url, output_path, manual_wait, doi):
        return success(doi, output_path, "Publisher(Browser)")
    print("  [跳过] 未能从官网取到正文 PDF（多半是未登录机构 / 无订阅权限；SI 不会被当作正文保存）。")
    return None


def run_browser_session(
    identifiers: list[str],
    output_dir: str | Path | None,
    config: dict[str, Any],
    *,
    manual_wait: int = 300,
    manual: bool = False,
) -> list[dict[str, Any]]:
    """Download each identifier from the publisher's official site only.

    One visible browser is reused across all identifiers, so the human-check
    cleared for one publisher carries over to its other papers in the batch.
    In ``manual`` mode the user drives the browser (verify, log in, open the PDF)
    and the script only captures whichever PDF appears — works on any publisher.
    """
    try:
        from cloakbrowser import launch
    except ImportError:
        print("  Error: cloakbrowser 未安装，无法使用浏览器模式。")
        return []

    target_dir = Path(output_dir) if output_dir else Path(config.get("output_dir", "."))
    target_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    browser = launch(
        headless=False, humanize=True,
        args=["--disable-features=CrossOriginOpenerPolicy"],
    )
    try:
        context = browser.new_context()
        page = context.new_page()
        captured: list[tuple[str, bytes]] = []
        on_resp = _make_on_response(captured)
        on_dl = _make_on_download(captured)

        def _wire(pg: Any) -> None:
            # Inline PDFs stream through `response`; attachment-style "Download
            # PDF" buttons (Nature/IEEE/ACM) only surface via `download`.
            pg.on("response", on_resp)
            pg.on("download", on_dl)

        _wire(page)
        # Capture PDFs even from tabs opened by clicking a PDF link.
        context.on("page", _wire)

        for raw in identifiers:
            doi = normalize_doi(raw)
            output_path = target_dir / f"{safe_filename(doi)}_Official.pdf"
            print(f"\n=== {doi} ===")
            result = _download_one(page, context, captured, doi, output_path, manual_wait, manual)
            if result and is_pdf_file(Path(result.get("file", output_path))):
                print(f"  OK: {result['file']}")
                print(f"  Source: {result.get('source', 'Publisher(Browser)')}  (官方来源)")
                results.append(result)
            else:
                results.append({"success": False, "identifier": doi, "doi": doi,
                                "error": "official-only download failed"})

        ok = [r for r in results if r.get("success")]
        if ok:
            print(f"\n  ✓ 已保存 {len(ok)} 篇官方 PDF：")
            for r in ok:
                print(f"      {r['file']}")
            print("  浏览器即将关闭...")
    finally:
        try:
            browser.close()
        except Exception:
            pass
    return results
