"""Offline tests for search()/word_exists() against saved Infopédia HTML.

``tests/fixtures/casa.html`` is a real entry page (trimmed to QuadroDefinicao);
``tests/fixtures/notfound.html`` is trimmed from a real "no entry" response for
a made-up word, keeping only the dictionary-link anchors that drive the
search() fallback path.
"""
import pathlib

from pyinfopedia.client import search, word_exists

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class _FakeTransport:
    def __init__(self, html: str):
        self.html = html

    def get_text(self, url, **kw):
        return self.html


def test_search_direct_hit_returns_entry_word():
    html = (FIXTURES / "casa.html").read_text(encoding="utf-8")
    results = search("casa", transport=_FakeTransport(html))
    assert len(results) == 1
    assert results[0].word == "casa"


def test_search_fallback_skips_word_of_the_day_widget():
    """Regression: the sidebar "Palavra em destaque" (word-of-the-day) widget
    nests a caption paragraph in front of the headword; ``a.get_text(strip=True)``
    glued them into one string ("Palavra em destaquefleuma") and the widget's
    word leaked into every no-match search as a bogus result."""
    html = (FIXTURES / "notfound.html").read_text(encoding="utf-8")
    results = search("casaxyzabc", transport=_FakeTransport(html))
    assert results == []
    assert all("destaque" not in r.word for r in results)


def test_word_exists_true_for_real_entry():
    html = (FIXTURES / "casa.html").read_text(encoding="utf-8")
    assert word_exists("casa", transport=_FakeTransport(html))


def test_word_exists_false_for_missing_entry():
    html = (FIXTURES / "notfound.html").read_text(encoding="utf-8")
    assert not word_exists("casaxyzabc", transport=_FakeTransport(html))
