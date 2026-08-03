"""Offline parser tests against saved Infopédia HTML fixtures.

The fixtures (``tests/fixtures/*.html``) are trimmed to the ``QuadroDefinicao``
block of a real page, so these run without network. They lock in the two
correctness properties that matter for heterophone work:

* each pronunciation block is parsed separately (a homograph's readings do not
  bleak each other's senses), and
* single-definition entries (no acepção number) are still captured.
"""
import pathlib

import pytest

from pyinfopedia.client import _parse_entry_page

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _entry(word):
    html = (FIXTURES / f"{word}.html").read_text(encoding="utf-8")
    entry = _parse_entry_page(html, word)
    assert entry is not None
    return entry


def _defs(cat):
    return [s.definition for s in cat.senses if s.definition]


def test_sede_readings_are_separated():
    """sede has two readings — seat (ˈsɛd) and thirst (ˈsed) — with disjoint
    senses. Regression: the two used to share one merged definition blob."""
    entry = _entry("sede")
    assert len(entry.pronunciations) == 2
    by_pron = {}
    for cat in entry.categories:
        by_pron.setdefault(cat.pronunciation, []).extend(_defs(cat))
    blobs = [" ".join(v) for v in by_pron.values() if v]
    assert len(blobs) == 2
    seat = next(b for b in blobs if "sentar" in b or "administração" in b)
    thirst = next(b for b in blobs if "beber" in b)
    assert seat != thirst
    assert "beber" not in seat        # thirst sense must not leak into seat
    assert "administração" not in thirst


def test_dobro_single_sense_captured():
    """dobro's entries carry no acepção number; their definitions must still be
    parsed (regression: numberless rows were dropped → empty senses)."""
    entry = _entry("dobro")
    all_defs = [d for cat in entry.categories for d in _defs(cat)]
    assert all_defs, "dobro parsed with zero definitions"


def test_corte_cut_vs_court():
    """corte separates the open-ɔ cut readings from the closed-o court reading."""
    entry = _entry("corte")
    by_pron = {}
    for cat in entry.categories:
        by_pron.setdefault(cat.pronunciation, []).extend(_defs(cat))
    cut = " ".join(d for k, v in by_pron.items() if k and "ɔ" in k for d in v)
    court = " ".join(d for k, v in by_pron.items() if k and "ɔ" not in k for d in v)
    assert "cortar" in cut or "golpe" in cut
    assert "monarca" in court or "rei" in court


def test_every_parsed_sense_has_text():
    for word in ("sede", "dobro", "corte"):
        for cat in _entry(word).categories:
            for s in cat.senses:
                assert s.number >= 1


def test_expressions_have_definitions():
    """casa's set-phrase list (idioms) must carry their gloss.

    Regression: ``_parse_expressions`` looked up the definition table with
    ``find_next_sibling("div.dolTable")``, which bs4 treats as a literal tag
    *name* rather than a CSS selector — it never matched, so every expression
    was recorded with an empty ``definition``."""
    entry = _entry("casa")
    assert len(entry.expressions) > 30
    empty = [e for e in entry.expressions if not e.definition]
    assert not empty, f"{len(empty)} expressions parsed with no definition"
    caramela = next(e for e in entry.expressions if e.expression == "casa caramela")
    assert "edifício" in caramela.definition
    assert caramela.domain == "ARQUITETURA"


def test_casa_relations_and_audio():
    entry = _entry("casa")
    assert "divisão" in entry.relations.get("sinonimos", [])
    assert entry.audio_url and entry.audio_url.startswith("https://")
    assert len(entry.inflected_forms) > 0
