# Datasets

`pyinfopedia.dataset` turns a word list into a dataset, in two shapes.

## JSONL — full entries

One typed `Entry` per line (via `Entry.to_dict()`), keyed by a stable id.

```python
from pyinfopedia import Transport
from pyinfopedia.dataset import export_jsonl

export_jsonl(words, "out/infopedia.jsonl", append=False,
             transport=Transport(mode="curl_cffi"))
```

`export_jsonl(words, path, *, append=True, transport=None) -> int` returns the
number of new lines written. With `append=True` it reads existing ids from the
target file and skips words already present, so a run can resume.

## CSV — flat, one row per reading

One row per `(word, ipa, pos)` reading, with definitions joined. Suitable as a
publishable dataset and as an IPA source for downstream packages.

```python
from pyinfopedia.dataset import export_csv

export_csv(words, "out/infopedia.csv", transport=transport)
```

`export_csv(words, path, *, transport=None, dedup=True) -> int`. Columns:
`word, ipa, pos, syllabification, etymology, definition`.

A heterophone yields one row per pronunciation — e.g. `colher` gives `kuˈʎɛɾ`
(noun) and `kuˈʎeɾ` (verb).

## IPA normalisation for downstream matching

Infopédia IPA uses `ʀ` (uvular trill), `ɡ` (script g), `(ə)` for the optional
final schwa, and `r` for the tap. To match these against another IPA source,
normalise allophones and apply Unicode NFC (nasal vowels such as `ẽ` may be
pre-composed or `e` + combining tilde):

```python
import unicodedata
def normalise(ipa):
    s = unicodedata.normalize("NFC", ipa).lower()
    for a, b in {"ˈ":"", "ˌ":"", "ʀ":"ʁ", "ɡ":"g", "ə":"i", "ɨ":"i",
                 "ɐ":"a", "ɫ":"l", "r":"ɾ", "(":"", ")":"", " ":""}.items():
        s = s.replace(a, b)
    return s
```

See `examples/build_dataset.py` for an end-to-end script.

## Attribution

Dictionary content belongs to Porto Editora / Infopédia. A published dataset must
credit the source and respect its terms of use.
