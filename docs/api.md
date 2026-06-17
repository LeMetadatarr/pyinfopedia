# API reference

```python
import pyinfopedia
```

All lookup functions accept an optional keyword `transport` (see
[transport.md](transport.md)); when omitted, a default transport is used.

## Functions

### `get_word(word, *, transport=None) -> Entry | None`
Fetch and parse a word page. Returns an [`Entry`](#entry) or `None` if the word
has no dictionary page.

```python
entry = pyinfopedia.get_word("sede")
for cat in entry.categories:
    print(cat.pronunciation, cat.pos, cat.senses[0].definition)
```

### `search(prefix, *, transport=None) -> list[SearchResult]`
Prefix autocomplete. Returns [`SearchResult`](#searchresult) items.

```python
for r in pyinfopedia.search("cas"):
    print(r.word, r.url)
```

### `word_exists(word, *, transport=None) -> bool`
True if the word has a dictionary page.

### `get_verb(verb, *, transport=None) -> Conjugation | None`
Fetch the full conjugation of a verb from the *verbos-portugueses* dictionary.
Returns a [`Conjugation`](#conjugation).

```python
conj = pyinfopedia.get_verb("jogar")
print(conj.first_person_singular())     # jogo
print(conj.present_indicative())         # {"eu": "jogo", "tu": "jogas", ...}
```

### `verb_exists(verb, *, transport=None) -> bool`
True if the verb has a conjugation page.

## `Infopedia` client

A reusable client that holds one transport for many lookups.

```python
from pyinfopedia import Infopedia

client = Infopedia(mode="curl_cffi")          # or mode="flaresolverr", flaresolverr_url=...
entry  = client.get_word("livre")
hits   = client.search("liv")
exists = client.word_exists("livre")
```

`Infopedia(transport=None, *, mode=None, flaresolverr_url=None)` — pass either a
ready `Transport` or the keyword arguments to build one.

## Data models

Every model has a `to_dict()` that returns a JSON-serialisable mapping, omitting
empty fields.

### `Entry`
| field | type | description |
|---|---|---|
| `word` | `str` | headword |
| `pronunciation` | `str \| None` | first reading's IPA |
| `pronunciations` | `list[str]` | all distinct readings on the page |
| `syllabification` | `str \| None` | e.g. `se.de` |
| `etymology` | `str \| None` | origin note |
| `categories` | `list[GrammaticalCategory]` | grammatical classes, one per (reading, POS) |
| `expressions` | `list[Expression]` | set phrases / idioms |
| `inflected_forms` | `list[InflectedForm]` | conjugations / declensions listed on the page |
| `audio_url` | `str \| None` | pronunciation audio |
| `relations` | `dict[str, list[str]]` | sidebar word lists (see below) |

`relations` keys: `sinonimos`, `traducoes`, `rimas`, `vizinhas`, `parecidas`,
`relacionadas`, `pesquisa`.

### `GrammaticalCategory`
| field | type | description |
|---|---|---|
| `pos` | `str` | grammatical class, e.g. `nome feminino`, `verbo transitivo` |
| `pronunciation` | `str \| None` | IPA of the reading this class belongs to |
| `senses` | `list[Sense]` | numbered senses |

### `Sense`
| field | type | description |
|---|---|---|
| `number` | `int` | acepção number (1-based) |
| `definition` | `str` | the gloss; a cross-reference is captured as `"ver <word>"` |
| `synonyms` | `list[str]` | listed synonyms |
| `subsenses` | `list[str]` | nested sub-definitions |

### `Expression`
`expression: str`, `definition: str`, `domain: str | None`.

### `InflectedForm`
`form: str`, `grammatical_category: str | None`.

### `SearchResult`
`word: str`, `url: str`.

### `Conjugation`
| field / method | description |
|---|---|
| `verb: str` | infinitive |
| `moods: dict[str, dict[str, dict[str, str]]]` | mood → tense → {person: form} |
| `form(mood, tense, person) -> str \| None` | single conjugated form |
| `present_indicative() -> dict[str, str]` | {person: form} for the present indicative |
| `first_person_singular() -> str \| None` | 1sg present indicative |

## IDs

`id_from_entry(entry)` / `entry_id(...)` produce a stable identifier for an entry;
`entry_to_extra(entry)` returns auxiliary metadata. Used by the dataset exporters
to deduplicate.
