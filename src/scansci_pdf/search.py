"""Paper search via OpenAlex API."""

from __future__ import annotations

from typing import Any

from .config import load_config


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    if not isinstance(inverted_index, dict):
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        if isinstance(positions, list):
            for pos in positions:
                if isinstance(pos, int):
                    word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)[:500]


def search_papers(
    query: str,
    limit: int = 10,
    year_from: int | None = None,
    year_to: int | None = None,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    from .network import _get_session, request_timeout
    config = load_config()
    try:
        session = _get_session(config)
        params: dict[str, Any] = {"search": query, "per_page": limit}

        # Build filter for year range
        filters = []
        if year_from or year_to:
            y_from = year_from or 1900
            y_to = year_to or 2026
            filters.append(f"publication_year:{y_from}-{y_to}")
        if filters:
            params["filter"] = ",".join(filters)

        # Sort: cited_by_count:desc, publication_date:desc, relevance_score:desc
        if sort:
            sort_key = sort if ":" in sort else f"{sort}:desc"
            params["sort"] = sort_key

        resp = session.get(
            "https://api.openalex.org/works",
            params=params,
            timeout=request_timeout(config),
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []
    results = []
    for work in data.get("results", []):
        doi_raw = work.get("doi", "") or ""
        doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])[:5]
        ]
        results.append({
            "title": work.get("title", ""),
            "doi": doi,
            "url": work.get("id", ""),
            "authors": authors,
            "year": work.get("publication_year", ""),
            "cited_by_count": work.get("cited_by_count", 0),
            "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        })
    return results


def search_by_title(title: str, config: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Search OpenAlex by title and return best match with DOI."""
    from difflib import SequenceMatcher
    from .network import _get_session, request_timeout

    if not title or len(title) < 10:
        return None

    if config is None:
        config = load_config()

    try:
        session = _get_session(config)
        resp = session.get(
            "https://api.openalex.org/works",
            params={"search": title, "per_page": 5},
            timeout=request_timeout(config),
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception:
        return None

    title_lower = title.lower().strip()
    best = None
    best_score = 0.0

    for work in data.get("results", []):
        result_title = (work.get("title") or "").lower().strip()
        if not result_title:
            continue
        score = SequenceMatcher(None, title_lower, result_title).ratio()
        if score > best_score:
            best_score = score
            doi_raw = work.get("doi", "") or ""
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in (work.get("authorships") or [])[:5]
            ]
            best = {
                "title": work.get("title", ""),
                "doi": doi,
                "authors": authors,
                "year": work.get("publication_year", ""),
                "score": round(score, 3),
            }

    if best_score >= 0.75 and best and best.get("doi"):
        return best
    return None
