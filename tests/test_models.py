"""Model serialization tests (no network)."""
from pyinfopedia.models import Entry, GrammaticalCategory, Sense


def test_entry_to_dict_roundtrip():
    entry = Entry(
        word="sede",
        pronunciation="ˈsɛdɨ",
        pronunciations=["ˈsɛdɨ", "ˈsedɨ"],
        categories=[
            GrammaticalCategory(
                pos="nome feminino",
                pronunciation="ˈsɛdɨ",
                senses=[Sense(number=1, definition="local de uma administração")],
            ),
            GrammaticalCategory(
                pos="nome feminino",
                pronunciation="ˈsedɨ",
                senses=[Sense(number=1, definition="vontade de beber")],
            ),
        ],
    )
    d = entry.to_dict()
    assert d["word"] == "sede"
    assert d["pronunciations"] == ["ˈsɛdɨ", "ˈsedɨ"]
    cats = d["categories"]
    assert len(cats) == 2
    assert cats[0]["pronunciation"] == "ˈsɛdɨ"
    assert cats[0]["senses"][0]["definition"] == "local de uma administração"


def test_grammatical_category_carries_pronunciation():
    cat = GrammaticalCategory(pos="verbo", pronunciation="ˈʒɔɡu",
                              senses=[Sense(number=1, definition="participar num jogo")])
    d = cat.to_dict()
    assert d["pos"] == "verbo"
    assert d["pronunciation"] == "ˈʒɔɡu"
