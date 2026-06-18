from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup, Tag

from pyinfopedia.models import (
    Entry,
    Expression,
    GrammaticalCategory,
    InflectedForm,
    SearchResult,
    Sense,
)
from pyinfopedia.transport import Transport, default_transport

BASE_URL = "https://www.infopedia.pt"
DICT_PATH = "/dicionarios/lingua-portuguesa"


def _t(transport: Optional[Transport]) -> Transport:
    return transport or default_transport()


def _word_url(word: str) -> str:
    return f"{BASE_URL}{DICT_PATH}/{quote(word, safe='')}"


def _suggest_url(prefix: str) -> str:
    return f"{BASE_URL}{DICT_PATH}/sugestao-pesquisa/{quote(prefix, safe='')}"


def _tag_text(tag: Optional[Tag], strip: bool = True) -> Optional[str]:
    if tag is None:
        return None
    return tag.get_text(strip=strip) or None


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,;.:!?])", r"\1", text)
    return text


def _parse_audio_url(soup: BeautifulSoup) -> Optional[str]:
    word_tts = soup.select_one("audio.audio-player-word-tts")
    if word_tts and word_tts.get("src"):
        src: str = word_tts["src"]
        if src.startswith("/"):
            return f"{BASE_URL}{src}"
        return src
    return None


def _parse_senses(catgram_aceps: Tag) -> List[Sense]:
    senses: List[Sense] = []
    for ridx, row in enumerate(catgram_aceps.select("div.dolAcepsRow")):
        # Single-definition entries (e.g. "dobro" numeral, "adorno") carry no
        # acepção number — fall back to the row's ordinal so the definition is
        # still captured instead of dropped.
        num_el = row.select_one("div.dolAcepsNum span")
        try:
            number = int(num_el.get_text(strip=True).rstrip(".")) if num_el else ridx + 1
        except (ValueError, TypeError):
            number = ridx + 1

        right_cell = row.select_one("div.dolAcepsRightCell")
        if right_cell is None:
            continue

        definitions: List[str] = []
        synonyms: List[str] = []
        for sidx, sub in enumerate(right_cell.select("span.dolAcepsSubacep")):
            texts = []
            for trad in sub.select("span.dolSubacepTraduz span.dolTraduzTrad"):
                text = _clean_text(trad.get_text(separator=" ", strip=True)).strip(",/ ")
                if text:
                    texts.append(text)
            (definitions if sidx == 0 else synonyms).extend(texts)

        # Cross-reference-only senses (e.g. "emperro" → "ver emperramento") carry a
        # remissão link instead of a gloss — capture it so the sense isn't empty.
        if not definitions:
            for rem in right_cell.select("span.dolSubacepLremissoes a"):
                target = _clean_text(rem.get_text(strip=True))
                if target:
                    definitions.append("ver " + target)

        definition = " | ".join(definitions) if definitions else None
        senses.append(Sense(number=number, definition=definition or "", synonyms=synonyms))
    return senses


def _parse_categories(soup: BeautifulSoup) -> List[GrammaticalCategory]:
    categories: List[GrammaticalCategory] = []
    for division in soup.select("div.dolDivisaoCatgram"):
        pos_el = division.select_one("span.dolCatgramTbcat")
        pos = _tag_text(pos_el) or ""

        aceps_el = division.select_one("div.dolCatgramAceps")
        senses: List[Sense] = []
        if aceps_el:
            senses = _parse_senses(aceps_el)

        categories.append(GrammaticalCategory(pos=pos, senses=senses))
    return categories


def _parse_expressions(soup: BeautifulSoup) -> List[Expression]:
    expressions: List[Expression] = []
    lexeger = soup.select_one("div.dolVverbeteLexeger")
    if lexeger is None:
        return expressions

    for exeger in lexeger.select("div.dolLexegerExeger"):
        domain_el = exeger.select_one("span.dolExegerTbdom")
        domain = _clean_text(domain_el.get_text(strip=True)) if domain_el else None

        expr_el = exeger.select_one("span.dolExegerLexpress")
        if expr_el is None:
            continue
        expr_text = _clean_text(expr_el.get_text(strip=True))

        # Find the definition in the following dolTable
        definition = ""
        table = exeger.find_next_sibling("div.dolTable")
        if table:
            def_el = table.select_one(
                "span.dolSubacepTraduz span.dolTraduzTrad"
            ) or table.select_one("span.dolAcepsSubacep span.dolSubacepTraduz")
            if def_el:
                definition = _clean_text(def_el.get_text(strip=True))

        expressions.append(
            Expression(
                expression=expr_text,
                definition=definition,
                domain=domain,
            )
        )
    return expressions


def _parse_inflected_forms(soup: BeautifulSoup) -> List[InflectedForm]:
    forms: List[InflectedForm] = []
    for anamorfs in soup.select("div.QuadroAnamorfs"):
        entry_el = anamorfs.select_one(
            "div.dolAmorfOutros-entrada div.cell-left")
        if entry_el is None:
            continue
        entry_word = _clean_text(entry_el.get_text(separator=" ", strip=True))
        header = entry_word  # e.g. "casar" for conjugations of "casa"

        # Group header: read the tense / category from dolAmorfOutros-group
        group = anamorfs.select_one("div.dolAmorfOutros-group")
        cat: Optional[str] = None
        if group:
            corpo = group.select_one("div.dolAmorfOutros-corpo")
            if corpo:
                cat = _clean_text(corpo.get_text(separator=" ", strip=True))

        # Body rows: pronoun + conjugated form
        body = anamorfs.select_one("div.dolAmorfOutros-body")
        if body:
            for row in body.select("div.col-row"):
                value_el = row.select_one("div.col-value")
                if value_el is None:
                    continue
                form_text = _clean_text(value_el.get_text(separator=" ", strip=True))
                if form_text:
                    forms.append(InflectedForm(
                        form=form_text,
                        grammatical_category=cat or header,
                    ))
    return forms


_REL_TYPES = ("sinonimos", "traducoes", "rimas", "vizinhas",
              "parecidas", "relacionadas", "pesquisa")


def _parse_relations(soup: BeautifulSoup) -> dict:
    """Parse the sidebar related-word lists (synonyms, rhymes, neighbours, …).

    Each ``div.dolRelacoes`` block has a heading link to
    ``/lingua-portuguesa/<type>/<word>`` and a ``div.dolRelacoesAssociacao`` with
    the actual word links (plus a trailing "…" see-more, which is dropped). The
    lists are present on the entry page itself — no need to follow the links.
    """
    out: dict = {}
    for block in soup.select("div.dolRelacoes"):
        head = block.select_one("div.container > a[href]")
        if head is None:
            continue
        m = re.search(r"/lingua-portuguesa/(\w+)/", head.get("href", ""))
        if not m or m.group(1) not in _REL_TYPES:
            continue
        rtype = m.group(1)
        assoc = block.select_one("div.dolRelacoesAssociacao")
        if assoc is None:
            continue
        words: List[str] = []
        for a in assoc.select("a[href]"):
            href = a.get("href", "")
            if f"/{rtype}/" in href:           # the "…" see-more link
                continue
            text = _clean_text(a.get_text(strip=True))
            if text and text != "…" and text not in words:
                words.append(text)
        if words:
            out[rtype] = words
    return out


def word_exists(word: str, *, transport: Optional[Transport] = None) -> bool:
    """Check if *word* has an entry in the dictionary."""
    url = _word_url(word)
    html = _t(transport).get_text(url)
    return ' class="dolEntradaVverbete"' in html or 'class="dolEntradaVverbete"' in html


def _parse_entry_page(html: str, word: str) -> Optional[Entry]:
    soup = BeautifulSoup(html, "html.parser")

    quadros = soup.select("div.QuadroDefinicao")
    if not quadros:
        return None

    quadro = quadros[0]

    # Headword
    entrada_el = quadro.select_one("h1.dolEntrinfoEntrada")
    headword = _tag_text(entrada_el) or word

    # Pronunciations + categories. Infopedia lists one entry block
    # (div.dolEntradaVverbete) per homograph reading, each with its own IPA and
    # its own grammatical categories — e.g. "colher" has kuˈʎɛr (nome) and kuˈʎer
    # (verbo). Collect every distinct reading and tie its IPA to the POS it carries.
    blocks = quadro.select("div.dolEntradaVverbete")
    pronunciations: List[str] = []
    categories: List[GrammaticalCategory] = []
    if blocks:
        for block in blocks:
            block_pron = _tag_text(block.select_one("span.dolRegfonFonet"))
            if block_pron and block_pron not in pronunciations:
                pronunciations.append(block_pron)
            for cat in _parse_categories(block):
                cat.pronunciation = block_pron
                categories.append(cat)
    else:
        categories = _parse_categories(quadro)
    pron_el = quadro.select_one("span.dolRegfonFonet")
    if not pronunciations and pron_el:
        pronunciations = [_tag_text(pron_el)]
    pronunciation = pronunciations[0] if pronunciations else _tag_text(pron_el)

    # Syllabification
    silab_el = quadro.select_one("span.dolSilab")
    syllabification = _tag_text(silab_el)

    # Etymology
    etim_el = quadro.select_one("div.dolVverbeteEtim")
    etymology = None
    if etim_el:
        raw = etim_el.get_text(separator=" ", strip=True)
        raw = raw.removeprefix("Etimologia:")
        etymology = _clean_text(raw) or None

    # Expressions / set phrases
    expressions = _parse_expressions(quadro)

    # Inflected forms
    inflected_forms = _parse_inflected_forms(quadro)

    # Audio URL
    audio_url = _parse_audio_url(soup)

    # Sidebar related-word lists (synonyms, rhymes, neighbours, …)
    relations = _parse_relations(soup)

    return Entry(
        word=headword,
        pronunciation=pronunciation,
        pronunciations=pronunciations,
        relations=relations,
        syllabification=syllabification,
        etymology=etymology,
        categories=categories,
        expressions=expressions,
        inflected_forms=inflected_forms,
        audio_url=audio_url,
    )


def get_word(word: str, *, transport: Optional[Transport] = None) -> Optional[Entry]:
    url = _word_url(word)
    html = _t(transport).get_text(url)
    return _parse_entry_page(html, word)


def search(prefix: str, *, transport: Optional[Transport] = None) -> List[SearchResult]:
    """Search for words matching *prefix*.

    This is a best-effort lookup. The site has no public JSON autocomplete
    endpoint, so the function first tries to find an exact entry match. If
    the entry exists for *prefix*, it is returned as a single result. If no
    entry is found, the related links sidebar is scanned for dictionary word
    links. Results are usually sparse; prefer direct :func:`get_word` lookups.
    """
    url = _word_url(prefix)
    html = _t(transport).get_text(url)
    soup = BeautifulSoup(html, "html.parser")

    # Check if the page contains an entry for the requested word
    quadro = soup.select_one("div.QuadroDefinicao")
    if quadro:
        entrada_el = quadro.select_one("h1.dolEntrinfoEntrada")
        if entrada_el:
            w = _tag_text(entrada_el) or prefix
            return [SearchResult(word=w, url=_word_url(w))]

    # Fallback: scan sidebar for dictionary links
    results: List[SearchResult] = []
    seen: set = set()
    for a in soup.select("a[href^='/dicionarios/lingua-portuguesa/']"):
        href: str = a["href"]
        # Only keep leaf word URLs
        path = href.removeprefix("/dicionarios/lingua-portuguesa/")
        if not path or "/" in path or "#" in path:
            continue
        text = _clean_text(a.get_text(strip=True))
        if text and text not in seen:
            seen.add(text)
            results.append(SearchResult(word=text, url=f"{BASE_URL}{href}"))
    return results


class Infopedia:
    def __init__(self, transport: Optional[Transport] = None, *,
                 mode: Optional[str] = None,
                 flaresolverr_url: Optional[str] = None,
                 flaresolverr_timeout_ms: Optional[int] = None,
                 wayback_fallback: Optional[bool] = None) -> None:
        if isinstance(transport, Transport):
            self.transport = transport
        else:
            self.transport = Transport(
                mode=mode,
                flaresolverr_url=flaresolverr_url,
                flaresolverr_timeout_ms=flaresolverr_timeout_ms,
                wayback_fallback=wayback_fallback,
            )

    def get_word(self, word: str) -> Optional[Entry]:
        return get_word(word, transport=self.transport)

    def search(self, prefix: str) -> List[SearchResult]:
        return search(prefix, transport=self.transport)

    def word_exists(self, word: str) -> bool:
        return word_exists(word, transport=self.transport)
