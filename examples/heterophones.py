"""Show how a heterophonic homograph's readings are kept separate — the core
use case for grapheme-to-phoneme / disambiguation work.

    PYINFOPEDIA_FLARESOLVERR=http://host:8191 python examples/heterophones.py
"""
import os

from pyinfopedia import Transport, get_word

WORDS = ["sede", "corte", "molho", "forma", "jogo"]


def make_transport():
    url = os.environ.get("PYINFOPEDIA_FLARESOLVERR")
    if url:
        return Transport(mode="flaresolverr", flaresolverr_url=url)
    return Transport(mode="curl_cffi")


def main():
    t = make_transport()
    for word in WORDS:
        entry = get_word(word, transport=t)
        if entry is None:
            continue
        print(f"\n{word}")
        by_pron = {}
        for cat in entry.categories:
            by_pron.setdefault(cat.pronunciation, []).extend(
                s.definition for s in cat.senses if s.definition)
        for pron, defs in by_pron.items():
            if defs:
                print(f"  {pron}: {defs[0]}")


if __name__ == "__main__":
    main()
