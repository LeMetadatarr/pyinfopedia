"""Fetch a word and print its readings, senses, etymology, and relations.

    python examples/basic_usage.py casa
    PYINFOPEDIA_FLARESOLVERR=http://host:8191 python examples/basic_usage.py sede
"""
import os
import sys

from pyinfopedia import Transport, get_word


def make_transport():
    url = os.environ.get("PYINFOPEDIA_FLARESOLVERR")
    if url:
        return Transport(mode="flaresolverr", flaresolverr_url=url)
    return Transport(mode="curl_cffi")


def main(word):
    entry = get_word(word, transport=make_transport())
    if entry is None:
        print(f"{word!r} not found")
        return
    print(f"{entry.word}   {entry.pronunciations or [entry.pronunciation]}")
    if entry.etymology:
        print(f"  etym: {entry.etymology}")
    for cat in entry.categories:
        print(f"  [{cat.pronunciation}] {cat.pos}")
        for s in cat.senses:
            print(f"      {s.number}. {s.definition}")
    if entry.relations.get("sinonimos"):
        print("  synonyms:", ", ".join(entry.relations["sinonimos"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "casa")
