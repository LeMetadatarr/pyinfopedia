"""Live tests against infopedia.pt — require network (and usually a Cloudflare
bypass). Skipped by default; run with ``pytest -m live``.

    PYINFOPEDIA_FLARESOLVERR=http://host:8191 pytest -m live
"""
import os

import pytest

pytestmark = pytest.mark.live


@pytest.fixture
def transport():
    from pyinfopedia.transport import Transport
    url = os.environ.get("PYINFOPEDIA_FLARESOLVERR")
    if url:
        return Transport(mode="flaresolverr", flaresolverr_url=url)
    return Transport(mode="curl_cffi")


def test_get_word_sede(transport):
    from pyinfopedia.client import get_word
    entry = get_word("sede", transport=transport)
    assert entry is not None
    assert len(entry.pronunciations) == 2          # seat vs thirst
    defs = " ".join(s.definition for c in entry.categories for s in c.senses)
    assert "beber" in defs                           # thirst sense present


def test_word_exists(transport):
    from pyinfopedia.client import word_exists
    assert word_exists("casa", transport=transport)
