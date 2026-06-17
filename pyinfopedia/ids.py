from __future__ import annotations

from typing import Optional

from pyinfopedia.models import Entry


def entry_id(word: str) -> str:
    return f"infopedia_pt:{word}"


def id_from_entry(entry: Entry) -> str:
    return entry_id(entry.word)


def entry_to_extra(entry: Entry) -> dict:
    extra = {
        "infopedia_id": id_from_entry(entry),
        "infopedia_word": entry.word,
    }
    if entry.pronunciation:
        extra["infopedia_pronunciation"] = entry.pronunciation
    if entry.syllabification:
        extra["infopedia_syllabification"] = entry.syllabification
    if entry.etymology:
        extra["infopedia_etymology"] = entry.etymology
    if entry.categories:
        pos_list = [c.pos for c in entry.categories if c.pos]
        if pos_list:
            extra["infopedia_pos"] = "|".join(pos_list)
        n_senses = sum(len(c.senses) for c in entry.categories)
        if n_senses:
            extra["infopedia_n_senses"] = str(n_senses)

    return extra
