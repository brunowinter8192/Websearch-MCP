"""Tests for scrape_logger.write_sidecar's real header content — no prior direct coverage existed
(chromium_scrape.py/camoufox_scrape.py's own tests mock write_sidecar as a no-op). Uses tmp_path
(via WEBSEARCH_SCRAPE_LOG_PATH) so the production log/sidecar dir is never touched.
"""
import src.scraper.scrape_logger as scrape_logger


def test_write_sidecar_header_includes_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBSEARCH_SCRAPE_LOG_PATH", str(tmp_path / "scrape_log.jsonl"))
    rel_path = scrape_logger.write_sidecar(
        "https://example.com/page", "2026-08-25T12:00:00.000Z", "real content", "ok", "filtered", "chromium",
    )
    assert rel_path is not None
    written = (tmp_path / rel_path).read_text(encoding="utf-8")
    assert "<!-- engine: chromium -->" in written
    assert "<!-- url: https://example.com/page -->" in written
    assert "<!-- outcome: ok -->" in written
    assert "<!-- mode: filtered -->" in written
    assert written.endswith("real content")


def test_write_sidecar_header_reflects_camoufox_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBSEARCH_SCRAPE_LOG_PATH", str(tmp_path / "scrape_log.jsonl"))
    rel_path = scrape_logger.write_sidecar(
        "https://example.com/page", "2026-08-25T12:00:00.000Z", "real content", "ok", "markdown", "camoufox",
    )
    written = (tmp_path / rel_path).read_text(encoding="utf-8")
    assert "<!-- engine: camoufox -->" in written


def test_write_sidecar_returns_none_on_empty_content(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBSEARCH_SCRAPE_LOG_PATH", str(tmp_path / "scrape_log.jsonl"))
    assert scrape_logger.write_sidecar("https://x.test", "2026-08-25T12:00:00.000Z", "", "empty", "filtered", "chromium") is None
