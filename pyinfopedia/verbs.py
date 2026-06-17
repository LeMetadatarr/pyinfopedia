"""Verb-conjugation dictionary support (infopedia *verbos-portugueses*).

Parses ``https://www.infopedia.pt/dicionarios/verbos-portugueses/<verb>`` into a
:class:`~pyinfopedia.models.Conjugation` (mood → tense → {person: form}).

    from pyinfopedia import get_verb
    conj = get_verb("colmar")
    conj.first_person_singular()      # "colmo"
    conj.present_indicative()         # {"eu": "colmo", "tu": "colmas", ...}

Infopédia exposes the conjugated forms but no per-form IPA; the page does carry
one TTS audio URL for the infinitive (``audio_url``).
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from pyinfopedia.client import BASE_URL, _clean_text, _tag_text
from pyinfopedia.models import Conjugation
from pyinfopedia.transport import Transport, default_transport

VERBS_PATH = "/dicionarios/verbos-portugueses"


def _verb_url(verb: str) -> str:
    return f"{BASE_URL}{VERBS_PATH}/{quote(verb, safe='')}"


def _parse_conjugation(html: str, verb: str) -> Optional[Conjugation]:
    soup = BeautifulSoup(html, "html.parser")
    if not soup.select_one("table.dolVerbosTempoContainer"):
        return None  # not a verb / no conjugation on page

    h1 = soup.select_one("h1")
    headword = _tag_text(h1) or verb

    audio = None
    audio_el = soup.select_one("audio[src], audio source[src]")
    if audio_el and audio_el.get("src"):
        src = audio_el["src"]
        audio = f"{BASE_URL}{src}" if src.startswith("/") else src

    moods: dict = {}
    for block in soup.select("div.dolVerbosModoBlock"):
        modo_el = block.select_one("div.dolVerbosHeaderModo")
        mood = _tag_text(modo_el) or ""
        if not mood:
            continue
        tenses: dict = {}
        for tempo in block.select("div.dolVerbosTempo"):
            title_el = tempo.select_one("div.dolVerbosTempoHeaderTitle")
            tense = _tag_text(title_el) or ""
            forms: dict = {}
            for tr in tempo.select("table.dolVerbosTempoContainer tr"):
                person_el = tr.select_one("td.dolVerbosPessoa")
                form_el = tr.select_one("td.dolVerbosFormaVerbal")
                if person_el is None or form_el is None:
                    continue
                person = _clean_text(person_el.get_text(" ", strip=True))
                form = _clean_text(form_el.get_text(" ", strip=True))
                if person and form:
                    forms[person] = form
            if tense and forms:
                tenses[tense] = forms
        if tenses:
            moods.setdefault(mood, {}).update(tenses)
    return Conjugation(verb=headword, moods=moods, audio_url=audio)


def get_verb(verb: str, *, transport: Optional[Transport] = None) -> Optional[Conjugation]:
    """Fetch and parse the conjugation of *verb*; None if it has no verb entry."""
    html = (transport or default_transport()).get_text(_verb_url(verb))
    return _parse_conjugation(html, verb)


def verb_exists(verb: str, *, transport: Optional[Transport] = None) -> bool:
    """True if *verb* has a conjugation entry (a real Portuguese verb)."""
    return get_verb(verb, transport=transport) is not None
