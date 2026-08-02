# pyinfopedia

Typed Python client for **[Infopédia](https://www.infopedia.pt/dicionarios/lingua-portuguesa/)** — the European-Portuguese dictionary by Porto Editora.

Each word page is parsed into a typed `Entry`: headword, **IPA pronunciation(s)**, syllabification, etymology, grammatical categories with numbered senses, set phrases, inflected forms, and the sidebar related-word lists (synonyms, rhymes, neighbours…).

Built for Portuguese NLP/lexicon work — it correctly separates **heterophonic homographs** (same spelling, different pronunciation per reading), which is what makes it useful for grapheme-to-phoneme and disambiguation tasks.

## Install

```bash
pip install pyinfopedia            # or: uv pip install pyinfopedia
pip install pyinfopedia[stealth]   # + curl_cffi for Cloudflare bypass
```

Depends on [`unblock_requests`](https://github.com/LeMetadatarr/unblock_requests) for transport.

## Quick start

```python
import pyinfopedia

entry = pyinfopedia.get_word("casa")
print(entry.pronunciation)              # ˈkazɐ
print(entry.categories[0].pos)          # nome feminino
print(entry.categories[0].senses[0].definition)

for r in pyinfopedia.search("cas"):     # prefix autocomplete
    print(r.word, r.url)
```

## Heterophonic homographs

Infopédia lists one entry block **per pronunciation**; pyinfopedia keeps them
separate, tying each grammatical category (and its senses) to the reading it
belongs to:

```python
entry = pyinfopedia.get_word("sede")
for cat in entry.categories:
    print(cat.pronunciation, cat.pos, "->", cat.senses[0].definition)
# ˈsɛdɨ nome feminino -> lugar onde alguém se pode sentar ou fixar   (seat / HQ)
# ˈsedɨ nome feminino -> sensação causada pela necessidade de beber  (thirst)
```

The two readings carry **disjoint** senses — `corte` (cut ˈkɔɾtɨ / court ˈkoɾtɨ),
`molho` (sauce ˈmoʎu / bundle ˈmɔʎu), `forma` (mould ˈfoɾmɐ / shape ˈfɔɾmɐ) all
behave the same way. See [`examples/heterophones.py`](examples/heterophones.py).

## Transport / Cloudflare

All HTTP goes through `Transport`, a wrapper over `unblock_requests.CloudflareSession`.
Pick a mode when the default is blocked:

```python
from pyinfopedia import Infopedia
client = Infopedia(mode="curl_cffi")                                   # impersonate a browser
client = Infopedia(mode="flaresolverr",
                   flaresolverr_url="http://192.168.1.116:8191")        # FlareSolverr
```

Modes: `requests` · `curl_cffi` · `flaresolverr` · `wayback`.

## Verbs

```python
from pyinfopedia import get_verb
conj = get_verb("jogar")
print(conj.first_person_singular())     # jogo
print(conj.present_indicative())
```

## Datasets

`pyinfopedia.dataset` exports JSONL/CSV for a word list — see
[`examples/build_dataset.py`](examples/build_dataset.py).

## Development

```bash
pytest -m "not live"            # offline parser/model tests (HTML fixtures)
PYINFOPEDIA_FLARESOLVERR=http://host:8191 pytest -m live    # hit the live site
```

Apache-2.0 · `JarbasAi <jarbasai@mailfence.com>`. Data belongs to Porto Editora /
Infopédia; this is an unofficial client — respect their terms and rate limits.

## Related projects

- [`unblock_requests`](https://github.com/LeMetadatarr/unblock_requests) — the Cloudflare-bypass transport this client is built on.
- [`pyportaldalingua`](https://github.com/LeMetadatarr/pyportaldalingua) — client for another Portuguese-language dictionary.
- [`pywiktionary`](https://github.com/LeMetadatarr/pywiktionary) — Wiktionary client.
