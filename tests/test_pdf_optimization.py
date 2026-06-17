from __future__ import annotations

import sys
from pathlib import Path

_PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT / "src"))


def test_polite_delay_is_disabled_unless_fixed_delay_is_enabled(monkeypatch):
    from scansci_pdf import network

    sleeps: list[float] = []
    monkeypatch.setattr(network.time, "sleep", sleeps.append)
    monkeypatch.setattr(network.random, "uniform", lambda lo, hi: hi)

    network.polite_delay({"request_delay_min": 2.0, "request_delay_max": 5.0})
    assert sleeps == []

    network.polite_delay(
        {
            "fixed_request_delay_enabled": True,
            "request_delay_min": 2.0,
            "request_delay_max": 5.0,
        }
    )
    assert sleeps == [5.0]


def test_fetch_json_reuses_in_memory_probe_cache(monkeypatch):
    from scansci_pdf import network

    network._json_cache.clear()
    network._json_cache_expires.clear()
    calls = {"count": 0}

    class FakeResponse:
        status_code = 200

        def json(self):
            calls["count"] += 1
            return {"count": calls["count"]}

    monkeypatch.setattr(network, "fetch", lambda *args, **kwargs: FakeResponse())

    config = {"json_probe_cache_seconds": 60}
    first = network.fetch_json("https://example.test/metadata", config)
    second = network.fetch_json("https://example.test/metadata", config)

    assert first == {"count": 1}
    assert second == {"count": 1}
    assert calls["count"] == 1
