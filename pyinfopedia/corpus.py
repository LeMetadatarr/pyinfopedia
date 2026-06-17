"""BFS-based corpus builder for Infopédia — discovers words iteratively.

Starts from seed words, for each one extracts related word links from the
page, and keeps expanding until *max-words* is reached.  One JSONL row per
sense/meaning.

Usage::

    python -m pyinfopedia.corpus --output corpus.jsonl --max-words 2000
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import time
import urllib.parse
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional, Set
from urllib.parse import unquote

from bs4 import BeautifulSoup

from sitemapper import crawl

from pyinfopedia.client import get_word, _clean_text
from pyinfopedia.models import Entry
from pyinfopedia.transport import default_transport

logger = logging.getLogger("pyinfopedia.corpus")

BASE_URL = "https://www.infopedia.pt"
DICT_PATH = "/dicionarios/lingua-portuguesa"
DELAY = 2.0

SEEDS = [
    "a", "à", "ano", "ao", "aquele", "aquilo", "as", "até", "bem", "bom",
    "cada", "casa", "cão", "como", "com", "coisa", "contra", "comigo",
    "da", "dar", "de", "dela", "dele", "depois", "dia", "dizer", "do", "dos",
    "e", "ela", "ele", "eles", "em", "entre", "essa", "esse", "esta", "está",
    "este", "eu", "fazer", "falar", "fez", "foi", "fora", "fui",
    "gente", "geral", "grande", "há", "haver", "hoje", "homem", "hora",
    "isso", "isto", "ir", "lá", "lhe", "lhes", "livro", "logo",
    "mais", "mal", "mas", "me", "melhor", "menos", "mesmo", "meu", "mim",
    "muito", "mulher", "mundo", "na", "não", "nas", "nem", "ninguém", "no",
    "nome", "nos", "nós", "nova", "novo", "num", "nunca", "o", "obra",
    "olhar", "os", "outro", "para", "parecer", "parte", "pela", "pelo",
    "pessoa", "pode", "poder", "pôr", "por", "porque", "primeiro", "qual",
    "quando", "quanto", "que", "quem", "sabe", "saber", "se", "ser", "seu",
    "si", "sim", "só", "sobre", "sua", "tal", "talvez", "também", "tanto",
    "te", "tem", "ter", "teu", "ti", "tido", "todo", "trabalho", "trás",
    "tu", "um", "uma", "vai", "valor", "vem", "ver", "vez", "vir", "viver",
    "você", "vida", "água", "amor", "cabeça", "caminho", "campo",
    "capaz", "certo", "chegar", "cidade", "contudo", "correr", "costa",
    "criar", "cuja", "cujo", "direito", "durante", "então", "erro",
    "esperar", "estar", "falar", "falso", "fazer", "fim", "frente",
    "guerra", "haver", "história", "idade", "ideia", "igreja", "já",
    "jovem", "julgar", "justo", "lá", "lado", "lei", "ler", "levar",
    "língua", "longe", "lugar", "luz", "mão", "mar", "medida", "melhor",
    "memória", "menino", "menos", "mês", "mesa", "minuto", "modo",
    "moço", "montanha", "morrer", "mostrar", "mãe", "natureza", "necessário",
    "negócio", "nenhum", "noite", "nível", "obra", "obrigado", "ocasião",
    "olho", "ontem", "opinião", "ora", "ordem", "orelha", "órgão", "outono",
    "ouvir", "padre", "palavra", "papel", "par", "passado", "passar",
    "pátria", "paz", "peito", "pena", "pensar", "perder", "pergunta",
    "perigo", "perto", "pé", "pior", "planeta", "plano", "povo", "praia",
    "prazer", "precisar", "prender", "preparar", "presidente", "preto",
    "príncipe", "próprio", "próximo", "público", "pular", "puro", "quadro",
    "qualquer", "quarto", "quase", "querer", "questão", "quieto", "química",
    "raça", "razão", "receber", "recente", "recurso", "redor", "regra",
    "rei", "reino", "relógio", "repetir", "república", "resto", "resultado",
    "reunião", "revista", "rezar", "rico", "rio", "risco", "rocha", "rodar",
    "romance", "roupa", "rua", "ruim", "saber", "sabor", "sair", "sala",
    "salvar", "sangue", "saúde", "secar", "século", "segredo", "seguir",
    "segundo", "segurança", "selva", "semana", "senhor", "sentido", "sentir",
    "separar", "servir", "sé", "sistema", "sítio", "sociedade", "soldado",
    "solução", "sombra", "sonho", "subir", "sucesso", "sul", "superior",
    "surdo", "surpresa", "século", "tarde", "telefone", "telhado", "tema",
    "tempo", "tenda", "tenente", "terreno", "tesoura", "testa", "teste",
    "teto", "tigre", "tinta", "tio", "tipo", "tirar", "título", "tocar",
    "tolo", "tomar", "tonelada", "torre", "tosse", "trabalho", "traduzir",
    "trazer", "tremer", "três", "triângulo", "tribo", "triste", "trocar",
    "trono", "trovão", "tudo", "túnel", "uivar", "ultimar", "último",
    "unha", "unidade", "unir", "universo", "urgente", "usar", "uso",
    "útil", "vaca", "vai", "vale", "valente", "valer", "valor", "vapor",
    "variar", "vasto", "vazio", "velho", "veloz", "vencer", "vender",
    "vento", "verdade", "verde", "vergonha", "vermelho", "verso", "vestir",
    "veterano", "viagem", "vida", "vidro", "vigiar", "vila", "vinho",
    "violino", "virar", "visitar", "vista", "vitória", "viúvo", "viver",
    "vivo", "voz", "voo", "vulgar", "xadrez", "xarope", "zangar", "zarpar",
    "zebra", "zero", "zona", "zumbir",
]


def _extract_word_urls_from_html(html: str) -> Set[str]:
    """Extract all dictionary word URLs from a page's HTML.

    Looks for every ``<a href="/dicionarios/lingua-portuguesa/WORD">`` and
    returns the decoded word paths.
    """
    words: Set[str] = set()
    for m in re.finditer(
        rf'href="{re.escape(DICT_PATH)}/([^"#?]+)',
        html,
    ):
        path = unquote(m.group(1))
        path = path.split("?")[0]
        path = path.strip("/")
        if not path or "/" in path or path.startswith("$"):
            continue
        words.add(path)
    return words


def _extract_words_from_sitemap(word: str, max_pages: int = 15) -> Set[str]:
    """Use sitemapper to crawl a word page and discover more word URLs."""
    words: Set[str] = set()
    url = f"{BASE_URL}{DICT_PATH}/{urllib.parse.quote(word, safe='')}"
    try:
        graph = crawl(url, max_pages=max_pages)
    except Exception:
        return words
    for node_url in graph.nodes:
        if DICT_PATH not in node_url:
            continue
        path = node_url.split(DICT_PATH + "/")[1]
        path = path.split("?")[0]
        path = unquote(path)
        if not path or "/" in path or "#" in path or path.startswith("$"):
            continue
        words.add(path)
    return words


def entry_to_sense_rows(entry: Entry) -> List[Dict]:
    """Split an :class:`Entry` into one dict per sense/meaning."""
    rows: List[Dict] = []

    for cat_idx, cat in enumerate(entry.categories):
        for sense in cat.senses:
            row: Dict[str, object] = {
                "id": f"infopedia_pt:{entry.word}#{sense.number}",
                "word": entry.word,
                "sense_number": sense.number,
                "definition": sense.definition,
                "part_of_speech": cat.pos,
                "category_index": cat_idx,
                "pronunciation": entry.pronunciation or "",
                "syllabification": entry.syllabification or "",
                "synonyms": sense.synonyms,
                "etymology": entry.etymology or "",
            }
            rows.append(row)

    for expr_idx, expr in enumerate(entry.expressions):
        row: Dict[str, object] = {
            "id": f"infopedia_pt:{entry.word}#expr{expr_idx}",
            "word": entry.word,
            "sense_number": -1,
            "definition": expr.definition,
            "part_of_speech": "expressão",
            "category_index": -1,
            "pronunciation": entry.pronunciation or "",
            "syllabification": entry.syllabification or "",
            "synonyms": [],
            "etymology": entry.etymology or "",
            "expression": expr.expression,
            "expression_domain": expr.domain or "",
        }
        rows.append(row)

    for finf_idx, finf in enumerate(entry.inflected_forms):
        if finf.form.lower() == entry.word.lower():
            continue
        row: Dict[str, object] = {
            "id": f"infopedia_pt:{entry.word}#form{finf_idx}",
            "word": entry.word,
            "sense_number": -1,
            "definition": "",
            "part_of_speech": "forma verbal",
            "category_index": -1,
            "pronunciation": entry.pronunciation or "",
            "syllabification": entry.syllabification or "",
            "synonyms": [],
            "etymology": entry.etymology or "",
            "inflected_form": finf.form,
            "inflected_category": finf.grammatical_category or "",
        }
        rows.append(row)

    return rows


def bfs_build_corpus(
    seeds: List[str],
    output: str,
    *,
    max_words: int = 5000,
    resume: bool = True,
    delay: float = DELAY,
    use_crawl: bool = True,
) -> int:
    """BFS: process seeds, extract related words, repeat until *max_words*.

    Returns the number of *new* rows written.
    """
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)

    seen_ids: Set[str] = set()
    if resume and out.exists():
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    seen_ids.add(json.loads(line).get("id", ""))
                except json.JSONDecodeError:
                    continue
        logger.info("Resuming: %d rows already in %s", len(seen_ids), output)

    seen_words: Set[str] = set()
    if resume and out.exists():
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    w = json.loads(line).get("word", "")
                    if w:
                        seen_words.add(w)
                except json.JSONDecodeError:
                    continue
        logger.info("Resuming: %d words already processed", len(seen_words))

    queue: Deque[str] = deque()
    for s in seeds:
        if s not in seen_words:
            queue.append(s)

    # If all seeds were already processed, queue all known words as seeds
    # for further expansion (they'll be skipped but their links will be mined).
    if not queue and seen_words:
        logger.info("All seeds processed — queuing %d known words for expansion", len(seen_words))
        for w in seen_words:
            queue.append(w)
        # Reset seen_words so they get processed again (we only need their links)
        seen_words.clear()

    mode = "a" if resume and out.exists() else "w"
    n_new = 0
    n_errors = 0
    n_words = len(seen_words)
    tport = default_transport()

    with open(out, mode, encoding="utf-8") as fh:
        while queue and n_words < max_words:
            word = queue.popleft()
            if word in seen_words:
                continue
            seen_words.add(word)

            try:
                raw = _fetch_raw(word, tport)
            except Exception as exc:
                logger.warning("Fetch err %s: %s", word, exc)
                time.sleep(delay)
                continue

            found_words = _extract_word_urls_from_html(raw)

            entry = _parse_entry(raw, word)
            if entry is None:
                # no entry for this word, but still add its links to queue
                for fw in found_words:
                    if fw not in seen_words:
                        queue.append(fw)
                time.sleep(delay)
                continue

            # Write sense rows
            rows = entry_to_sense_rows(entry)
            for row in rows:
                rid: str = row["id"]
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_new += 1

            n_words += 1

            # Discover more words via sitemapper crawl (occasional)
            if use_crawl and n_words % 10 == 0:
                crawl_words = _extract_words_from_sitemap(word, max_pages=8)
                found_words.update(crawl_words)

            # Add newly found words to queue
            for fw in found_words:
                if fw not in seen_words and fw not in queue:
                    queue.append(fw)

            if n_words % 50 == 0:
                logger.info(
                    "words=%d/%d queue=%d new_rows=%d errors=%d",
                    n_words, max_words, len(queue), n_new, n_errors,
                )

            time.sleep(delay)

    logger.info(
        "Done: %d words processed, %d new rows (%d errors, %d queued)",
        n_words, n_new, n_errors, len(queue),
    )
    return n_new


def _fetch_raw(word: str, transport) -> str:
    """Fetch the raw HTML for a word entry."""
    url = f"{BASE_URL}{DICT_PATH}/{urllib.parse.quote(word, safe='')}"
    return transport.get_text(url)


def _parse_entry(html: str, word: str) -> Optional[Entry]:
    """Try to parse an Entry from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")
    quadros = soup.select("div.QuadroDefinicao")
    if not quadros:
        return None
    # Use client's internal parser
    from pyinfopedia.client import _parse_entry_page as parse_it
    return parse_it(html, word)


def resume_info(output: str) -> dict:
    """Return stats about an existing corpus."""
    out = Path(output)
    if not out.exists():
        return {"rows": 0, "words": 0}
    words: Set[str] = set()
    rows = 0
    with open(out, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                rows += 1
                w = d.get("word", "")
                if w:
                    words.add(w)
            except json.JSONDecodeError:
                continue
    return {"rows": rows, "words": len(words)}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="BFS Infopédia corpus builder — one row per sense"
    )
    parser.add_argument("--output", default="infopedia_corpus.jsonl")
    parser.add_argument("--max-words", type=int, default=5000)
    parser.add_argument("--delay", type=float, default=DELAY)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--crawl", action="store_true",
                        help="Enable slow sitemapper crawl for extra link discovery")
    args = parser.parse_args()

    if not args.no_resume:
        info = resume_info(args.output)
        if info["rows"]:
            logger.info("Existing corpus: %d rows, %d words", info["rows"], info["words"])

    bfs_build_corpus(
        SEEDS,
        args.output,
        max_words=args.max_words,
        resume=not args.no_resume,
        delay=args.delay,
        use_crawl=args.crawl,
    )


if __name__ == "__main__":
    main()
