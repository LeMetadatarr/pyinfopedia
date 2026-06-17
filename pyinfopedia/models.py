from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Sense:
    number: int
    definition: str
    synonyms: List[str] = field(default_factory=list)
    subsenses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"number": self.number, "definition": self.definition}
        if self.synonyms:
            d["synonyms"] = self.synonyms
        if self.subsenses:
            d["subsenses"] = self.subsenses
        return d


@dataclass
class GrammaticalCategory:
    pos: str
    senses: List[Sense] = field(default_factory=list)
    pronunciation: Optional[str] = None  # IPA of the homograph entry this POS belongs to

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"pos": self.pos}
        if self.pronunciation:
            d["pronunciation"] = self.pronunciation
        if self.senses:
            d["senses"] = [s.to_dict() for s in self.senses]
        return d


@dataclass
class Expression:
    expression: str
    definition: str
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"expression": self.expression, "definition": self.definition}
        if self.domain:
            d["domain"] = self.domain
        return d


@dataclass
class InflectedForm:
    form: str
    grammatical_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"form": self.form}
        if self.grammatical_category:
            d["grammatical_category"] = self.grammatical_category
        return d


@dataclass
class Entry:
    word: str
    pronunciation: Optional[str] = None       # first reading (back-compat)
    pronunciations: List[str] = field(default_factory=list)  # all distinct readings on the page
    syllabification: Optional[str] = None
    etymology: Optional[str] = None
    categories: List[GrammaticalCategory] = field(default_factory=list)
    expressions: List[Expression] = field(default_factory=list)
    inflected_forms: List[InflectedForm] = field(default_factory=list)
    audio_url: Optional[str] = None
    # sidebar related-word lists keyed by infopedia resource slug:
    # sinonimos, traducoes, rimas, vizinhas, parecidas, relacionadas, pesquisa
    relations: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"word": self.word}
        if self.pronunciation:
            d["pronunciation"] = self.pronunciation
        if self.pronunciations:
            d["pronunciations"] = self.pronunciations
        if self.syllabification:
            d["syllabification"] = self.syllabification
        if self.etymology:
            d["etymology"] = self.etymology
        if self.categories:
            d["categories"] = [c.to_dict() for c in self.categories]
        if self.expressions:
            d["expressions"] = [e.to_dict() for e in self.expressions]
        if self.inflected_forms:
            d["inflected_forms"] = [f.to_dict() for f in self.inflected_forms]
        if self.audio_url:
            d["audio_url"] = self.audio_url
        if self.relations:
            d["relations"] = self.relations
        return d


@dataclass
class Conjugation:
    """Full conjugation of a verb from the *verbos-portugueses* dictionary.

    ``moods`` maps mood → tense → {person: form}, e.g.
    ``moods["INDICATIVO"]["Presente"]["eu"] == "colmo"``. Infopédia does not give
    per-form IPA, but this confirms the verb exists, its conjugation class, and
    the exact rhizotonic forms (1sg present, etc.).
    """
    verb: str
    moods: Dict[str, Dict[str, Dict[str, str]]] = field(default_factory=dict)
    audio_url: Optional[str] = None

    def form(self, mood: str, tense: str, person: str) -> Optional[str]:
        return self.moods.get(mood, {}).get(tense, {}).get(person)

    def present_indicative(self) -> Dict[str, str]:
        for mood, tenses in self.moods.items():
            if "INDICATIVO" in mood.upper():
                return tenses.get("Presente", {})
        return {}

    def first_person_singular(self) -> Optional[str]:
        """The 1sg present indicative (the rhizotonic form, e.g. ``colmo``)."""
        return self.present_indicative().get("eu")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"verb": self.verb, "moods": self.moods}
        if self.audio_url:
            d["audio_url"] = self.audio_url
        return d


@dataclass
class SearchResult:
    word: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        return {"word": self.word, "url": self.url}
