"""Offline tests for pyinfopedia.corpus (no network — transport is monkeypatched)."""
import json

import pyinfopedia.corpus as corpus


class _RaisingTransport:
    def get_text(self, url, **kw):
        raise RuntimeError("boom")


def test_bfs_build_corpus_counts_fetch_errors(tmp_path, monkeypatch, caplog):
    """Regression: n_errors was declared and logged but never incremented on a
    fetch failure, so the summary log always reported 0 errors regardless of
    how many words actually failed to fetch."""
    monkeypatch.setattr(corpus, "default_transport", lambda: _RaisingTransport())
    out = tmp_path / "corpus.jsonl"

    with caplog.at_level("INFO", logger="pyinfopedia.corpus"):
        n_new = corpus.bfs_build_corpus(
            ["naoexistepalavraaleatoria"], str(out),
            max_words=1, resume=False, delay=0, use_crawl=False,
        )

    assert n_new == 0
    assert not out.exists() or out.read_text(encoding="utf-8") == ""
    summary = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("Done:"))
    assert "1 errors" in summary, summary


def test_entry_to_sense_rows_skips_form_matching_headword():
    from pyinfopedia.models import Entry, InflectedForm

    entry = Entry(word="casa", inflected_forms=[
        InflectedForm(form="casa", grammatical_category="presente"),
        InflectedForm(form="casas", grammatical_category="presente"),
    ])
    rows = corpus.entry_to_sense_rows(entry)
    forms = [r["inflected_form"] for r in rows if "inflected_form" in r]
    assert forms == ["casas"]


def test_resume_info_on_missing_file(tmp_path):
    info = corpus.resume_info(str(tmp_path / "does-not-exist.jsonl"))
    assert info == {"rows": 0, "words": 0}


def test_resume_info_counts_rows_and_words(tmp_path):
    out = tmp_path / "corpus.jsonl"
    out.write_text(
        json.dumps({"id": "a#1", "word": "a"}) + "\n"
        + json.dumps({"id": "a#2", "word": "a"}) + "\n"
        + json.dumps({"id": "b#1", "word": "b"}) + "\n",
        encoding="utf-8",
    )
    info = corpus.resume_info(str(out))
    assert info == {"rows": 3, "words": 2}
