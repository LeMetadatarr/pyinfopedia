from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from pyinfopedia.client import get_word
from pyinfopedia.ids import id_from_entry
from pyinfopedia.models import Entry
from pyinfopedia.transport import Transport


def to_row(entry: Entry) -> dict:
    row = {"id": id_from_entry(entry)}
    d = entry.to_dict()
    d.pop("audio_url", None)
    row.update(d)
    return row


def _read_ids(path: Path) -> set:
    ids: set = set()
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(json.loads(line).get("id"))
                except json.JSONDecodeError:
                    continue
    return ids


def export_jsonl(words: Iterable[str], path: str, *,
                 append: bool = True,
                 transport: Optional[Transport] = None) -> int:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = _read_ids(out) if append else set()
    mode = "a" if append and out.exists() else "w"
    n = 0
    with open(out, mode, encoding="utf-8") as fh:
        for word in words:
            entry = get_word(word, transport=transport)
            if entry is None:
                continue
            row = to_row(entry)
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def build_corpus(words: Iterable[str], path: str, *,
                 transport: Optional[Transport] = None) -> Dict[str, int]:
    written = export_jsonl(words, path, append=True, transport=transport)
    return {"written": written}


# ── flat CSV export (one row per pronunciation/POS reading) ───────────────────
CSV_FIELDS = ["word", "ipa", "pos", "syllabification", "etymology",
              "definition", "audio_url"]


def to_csv_rows(entry: Entry) -> List[dict]:
    """Flatten an Entry to one row per grammatical category (= per reading).

    Each row carries the IPA of the homograph entry that POS belongs to, so a
    heterophone like ``colher`` yields both ``kuˈʎɛr`` (nome) and ``kuˈʎer``
    (verbo). Words with a single reading yield one row per POS.
    """
    base = {"word": entry.word,
            "syllabification": entry.syllabification or "",
            "etymology": entry.etymology or "",
            "audio_url": entry.audio_url or ""}
    rows: List[dict] = []
    if entry.categories:
        for cat in entry.categories:
            defs = "; ".join(s.definition for s in cat.senses if s.definition)
            rows.append({**base, "pos": cat.pos,
                         "ipa": cat.pronunciation or entry.pronunciation or "",
                         "definition": defs})
    else:
        rows.append({**base, "pos": "", "ipa": entry.pronunciation or "",
                     "definition": ""})
    return rows


def export_csv(words: Iterable[str], path: str, *,
               transport: Optional[Transport] = None, dedup: bool = True) -> int:
    """Write a flat CSV with full dictionary data, one row per (word, ipa, pos).

    Suitable as a publishable dataset and as an IPA source for downstream
    packages (e.g. bifonia).
    """
    import csv as _csv
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen: set = set()
    n = 0
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = _csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for word in words:
            entry = get_word(word, transport=transport)
            if entry is None:
                continue
            for row in to_csv_rows(entry):
                key = (row["word"], row["ipa"], row["pos"])
                if dedup and key in seen:
                    continue
                seen.add(key)
                writer.writerow(row)
                n += 1
    return n
