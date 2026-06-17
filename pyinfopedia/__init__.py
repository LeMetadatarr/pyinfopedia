"""pyinfopedia — typed Python client for Infopédia's Portuguese dictionary.

``pyinfopedia`` fetches and parses entries from
`Infopédia <https://www.infopedia.pt/dicionarios/lingua-portuguesa/>`_, the
Portuguese-language dictionary by Porto Editora. Each word page yields a typed
:class:`Entry` dataclass with the headword, phonetic transcription (IPA),
syllabification, etymology, grammatical categories with numbered senses, set
phrases / expressions, and inflected forms.

Quick start::

    import pyinfopedia

    # Fetch a word
    entry = pyinfopedia.get_word("casa")
    print(entry.word)            # "casa"
    print(entry.pronunciation)   # "ˈkazɐ"
    print(entry.categories[0].pos)       # "nome feminino"
    print(entry.categories[0].senses[0].definition)

    # Search / autocomplete (prefix lookup)
    results = pyinfopedia.search("cas")
    for r in results:
        print(r.word, r.url)

    # Use a configured client
    from pyinfopedia import Infopedia
    client = Infopedia(mode="curl_cffi")
    entry = client.get_word("livre")

All HTTP goes through :class:`pyinfopedia.Transport`, a wrapper over the org
:class:`unblock_requests.CloudflareSession`.
"""

from pyinfopedia.client import Infopedia, get_word, search, word_exists
from pyinfopedia.ids import entry_id, entry_to_extra, id_from_entry
from pyinfopedia.models import (
    Conjugation,
    Entry,
    Expression,
    GrammaticalCategory,
    InflectedForm,
    SearchResult,
    Sense,
)
from pyinfopedia.verbs import get_verb, verb_exists
from pyinfopedia.transport import Transport, default_transport
from pyinfopedia.version import __version__

__all__ = [
    "Entry",
    "Conjugation",
    "get_verb",
    "verb_exists",
    "Sense",
    "GrammaticalCategory",
    "Expression",
    "InflectedForm",
    "SearchResult",
    "Infopedia",
    "Transport",
    "default_transport",
    "get_word",
    "search",
    "word_exists",
    "entry_id",
    "id_from_entry",
    "entry_to_extra",
    "__version__",
]
