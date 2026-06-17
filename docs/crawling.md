# Crawling

Infopédia publishes no word list, so `pyinfopedia.crawl` builds one by traversal:
it starts from seed words and follows the sidebar related-word links of every page
it parses, repeating breadth-first until the frontier is empty.

```bash
python -m pyinfopedia.crawl \
    --seeds casa,tempo,agua --out crawl/entries.jsonl --state crawl/state.json \
    --mode flaresolverr --flaresolverr-url http://host:8191 --delay 1.0
```

## How it discovers words

Each parsed `Entry` carries `relations` — the sidebar lists. The crawl enqueues
the headwords from these (single-word entries only):

- `vizinhas` — alphabetical neighbours (this alone walks the dictionary in order),
- `sinonimos`, `parecidas`, `relacionadas`, `rimas`, `pesquisa`.

`traducoes` (translations into other languages) is **not** followed.

## Resumability

The visited set and the pending frontier are checkpointed to `--state` (atomic
write) every 25 pages and on exit, including on `SIGINT`/`SIGTERM`. Re-running with
the same `--state` and `--out` continues exactly where it stopped — already-seen
words are skipped and entries are appended. The crawl can therefore run
indefinitely, be stopped, and be resumed.

## Output

`--out` is JSONL, one parsed entry per line (`Entry.to_dict()` plus a stable
`id`). It is append-only; deduplicate by `id` if needed.

## Options

| flag | default | meaning |
|---|---|---|
| `--seeds` | `casa` | comma-separated seed words |
| `--out` | `crawl/entries.jsonl` | output JSONL |
| `--state` | `crawl/state.json` | resumable state |
| `--mode` | none | transport mode (see [transport.md](transport.md)) |
| `--flaresolverr-url` | none | FlareSolverr endpoint |
| `--delay` | `1.0` | seconds between requests (be polite) |
| `--max-pages` | none | stop after N pages (omit for a full crawl) |

## Programmatic use

```python
from pyinfopedia import Transport
from pyinfopedia.crawl import crawl

crawl(["casa", "tempo"], "crawl/entries.jsonl", "crawl/state.json",
      transport=Transport(mode="flaresolverr", flaresolverr_url="http://host:8191"),
      delay=1.0)
```
