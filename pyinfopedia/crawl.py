"""Resumable breadth-first crawl of Infopédia.

Infopédia has no public word list, so the crawl bootstraps from a set of seed
words and discovers new ones by following the sidebar related-word links of every
page it parses (synonyms, alphabetical neighbours, look-alikes, related, rhymes,
"people also searched"). It repeats until the frontier is exhausted.

State (the visited set and the pending frontier) is checkpointed to disk, so the
crawl resumes exactly where it stopped after an interruption. Each parsed entry is
appended to a JSONL file as it is discovered.

CLI::

    python -m pyinfopedia.crawl \
        --seeds casa,tempo,agua --out crawl/entries.jsonl --state crawl/state.json \
        --mode flaresolverr --flaresolverr-url http://host:8191 --delay 1.0
"""
from __future__ import annotations

import argparse
import json
import pathlib
import signal
import time
from collections import deque
from typing import Iterable, Optional

from pyinfopedia.client import get_word
from pyinfopedia.ids import id_from_entry
from pyinfopedia.transport import Transport

# Sidebar relations whose entries are Portuguese headwords worth following.
# "traducoes" (translations into other languages) is intentionally excluded.
FOLLOW_RELATIONS = ("sinonimos", "vizinhas", "parecidas", "relacionadas",
                    "rimas", "pesquisa")


def _clean(word: str) -> str:
    return word.strip().strip(".,;:!?").lower()


def _is_followable(word: str) -> bool:
    # single headword only: no spaces, has letters, not absurdly long
    return bool(word) and " " not in word and any(c.isalpha() for c in word) and len(word) <= 40


class CrawlState:
    """Visited set + pending frontier, persisted as JSON."""

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.seen: set = set()
        self.frontier: deque = deque()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.seen = set(data.get("seen", []))
            self.frontier = deque(data.get("frontier", []))

    def seed(self, words: Iterable[str]) -> None:
        if not self.seen and not self.frontier:
            for w in dict.fromkeys(_clean(w) for w in words):
                if _is_followable(w):
                    self.frontier.append(w)

    def save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps({"seen": sorted(self.seen),
                                   "frontier": list(self.frontier)}, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(self.path)        # atomic, so a crash never corrupts the state


def crawl(seeds: Iterable[str], out_path: str, state_path: str, *,
          transport: Optional[Transport] = None, delay: float = 1.0,
          max_pages: Optional[int] = None, checkpoint_every: int = 25) -> int:
    """Crawl from *seeds*, appending entries to *out_path*; returns pages fetched."""
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    state = CrawlState(pathlib.Path(state_path))
    state.seed(seeds)

    stop = {"flag": False}
    def _handler(*_):
        stop["flag"] = True
    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    fetched = 0
    with open(out, "a", encoding="utf-8") as sink:
        while state.frontier and not stop["flag"]:
            if max_pages is not None and fetched >= max_pages:
                break
            word = state.frontier.popleft()
            if word in state.seen:
                continue
            state.seen.add(word)
            try:
                entry = get_word(word, transport=transport)
            except Exception as exc:                       # noqa: BLE001 — keep crawling
                print(f"  ! {word}: {exc}", flush=True)
                entry = None
            fetched += 1
            if entry is not None:
                row = {"id": id_from_entry(entry), **entry.to_dict()}
                sink.write(json.dumps(row, ensure_ascii=False) + "\n")
                sink.flush()
                for key in FOLLOW_RELATIONS:
                    for nxt in entry.relations.get(key, []):
                        nxt = _clean(nxt)
                        if _is_followable(nxt) and nxt not in state.seen:
                            state.frontier.append(nxt)
            if fetched % checkpoint_every == 0:
                state.save()
                print(f"crawled {fetched} | seen {len(state.seen)} | "
                      f"frontier {len(state.frontier)}", flush=True)
            if delay:
                time.sleep(delay)

    state.save()
    print(f"STOP: fetched {fetched}, seen {len(state.seen)}, "
          f"frontier {len(state.frontier)}", flush=True)
    return fetched


def main() -> None:
    ap = argparse.ArgumentParser(description="Resumable BFS crawl of Infopédia.")
    ap.add_argument("--seeds", default="casa", help="comma-separated seed words")
    ap.add_argument("--out", default="crawl/entries.jsonl")
    ap.add_argument("--state", default="crawl/state.json")
    ap.add_argument("--mode", default=None, help="transport mode (curl_cffi/flaresolverr/…)")
    ap.add_argument("--flaresolverr-url", default=None)
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    ap.add_argument("--max-pages", type=int, default=None)
    args = ap.parse_args()

    transport = Transport(mode=args.mode, flaresolverr_url=args.flaresolverr_url) \
        if (args.mode or args.flaresolverr_url) else None
    crawl([s for s in args.seeds.split(",") if s.strip()],
          args.out, args.state, transport=transport,
          delay=args.delay, max_pages=args.max_pages)


if __name__ == "__main__":
    main()
