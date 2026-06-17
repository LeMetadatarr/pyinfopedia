# How parsing works

A word page (`/dicionarios/lingua-portuguesa/<word>`) is parsed by
`client._parse_entry_page(html, word)` into an `Entry`.

## Page structure → model

```
div.QuadroDefinicao                      → Entry
  h1.dolEntrinfoEntrada                  → Entry.word
  div.dolEntradaVverbete   (one per reading / pronunciation)
    span.dolRegfonFonet                  → pronunciation (IPA) for this block
    div.dolDivisaoCatgram                → GrammaticalCategory
      span.dolCatgramTbcat               → pos  ("nome feminino", "verbo", …)
      div.dolCatgramAceps
        div.dolAcepsRow      (one per sense)   → Sense
          div.dolAcepsNum span           → Sense.number
          div.dolAcepsRightCell …Traduz  → Sense.definition (+ synonyms)
  div.dolSilab                           → syllabification
  div.dolVverbeteEtim                    → etymology
  div.dolVverbeteLexeger                 → expressions (set phrases)
  div.QuadroAnamorfs                     → inflected_forms
```

The sidebar related-word lists (synonyms, translations, rhymes, neighbours,
look-alikes, related, "people also searched") are parsed by `_parse_relations`
into `Entry.relations`.

## Heterophones: one block per pronunciation

Infopédia renders a homograph as **multiple `div.dolEntradaVverbete` blocks**,
each with its own `dolRegfonFonet` IPA and its own categories. The parser tags
every `GrammaticalCategory` with `pronunciation = <its block's IPA>`, so a reader
can group senses by reading:

```python
by_pron = {}
for cat in entry.categories:
    by_pron.setdefault(cat.pronunciation, []).append(cat)
```

This is what keeps `sede` (ˈsɛdɨ seat / ˈsedɨ thirst) from merging into one blob.

## Gotchas the parser handles

- **Unnumbered senses.** Single-definition entries omit `dolAcepsNum`. The parser
  falls back to the row ordinal so the definition is still captured (otherwise
  words like `dobro`, `adorno`, `logro` would parse with empty senses).
- **Multiple categories per pronunciation.** A reading can have several
  `dolDivisaoCatgram` (e.g. `corte` ˈkɔɾtɨ has both a masculine "cut" noun and a
  feminine "pen/sty" noun). Group by pronunciation **and aggregate** — do not key
  a dict on pronunciation alone or later categories overwrite earlier ones.

## IPA notation

Infopédia uses `ʀ` (uvular trill), `ɡ` (script g), `(ə)` for the optional final
schwa, and `r` for the tap. Downstream consumers that compare against another
IPA source should normalise allophones (`ʀ→ʁ`, `ɡ→g`, `ə/ɨ→i`, `ɐ→a`, `ɫ→l`,
`r→ɾ`) and apply Unicode NFC (nasal vowels like `ẽ` may be pre-composed or
`e`+combining-tilde). See `examples/build_dataset.py`.
