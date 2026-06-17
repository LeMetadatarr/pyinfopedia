# pyinfopedia documentation

Typed Python client for [Infopédia](https://www.infopedia.pt/dicionarios/lingua-portuguesa/),
the European-Portuguese dictionary by Porto Editora.

- [API reference](api.md) — functions, the `Infopedia` client, and the data models.
- [Transport](transport.md) — HTTP and Cloudflare-bypass modes.
- [Parsing](parsing.md) — how a word page maps to the `Entry` model.
- [Datasets](datasets.md) — exporting word lists to JSONL and CSV.
- [Crawling](crawling.md) — resumable breadth-first crawl of the whole dictionary.

## Concepts

A word page resolves to an `Entry`: headword, one or more IPA pronunciations,
syllabification, etymology, grammatical categories (each with numbered senses),
set phrases, inflected forms, and the sidebar related-word lists.

Infopédia renders a heterophonic homograph as one block per pronunciation, so a
word with two readings (e.g. `sede` ˈsɛdɨ "seat" / ˈsedɨ "thirst") yields two
groups of categories, each tagged with its own IPA. This separation is the basis
for grapheme-to-phoneme and disambiguation use.

All network access goes through a [`Transport`](transport.md), a wrapper over
`unblock_requests.CloudflareSession`.
