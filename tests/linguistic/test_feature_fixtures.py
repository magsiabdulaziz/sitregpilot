"""Linguistic fixtures for the feature extractor (spaCy en_core_web_sm 3.8.0, NER disabled).

Each family has positive and negative cases and, where relevant, a documented ambiguity or boundary case.
These bound extraction validity by the fixtures and parser behaviour; they are not a measured accuracy
estimate on CORE (no manual gold annotation exists).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
import spacy
from spacy.language import Language

from core_register.features.extract import count_doc


@pytest.fixture(scope="module")
def counts() -> Callable[[str], dict[str, float]]:
    nlp: Language = spacy.load("en_core_web_sm", disable=["ner"])
    return lambda text: count_doc(nlp(text))


def n(c: dict[str, float], key: str) -> int:
    return int(c.get(key, 0))


def test_pronoun_person(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("I told you that we would help them, and it worked for my friends.")
    persons = ("n_pron_1sg", "n_pron_2", "n_pron_1pl", "n_pron_3", "n_pron_it")
    assert tuple(n(c, k) for k in persons) == (2, 1, 1, 1, 1)
    assert n(counts("The committee approved the budget."), "n_pron_1sg") == 0


def test_demonstrative_pronoun_vs_determiner(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("This is good. That book is mine. Those are new.")
    assert (n(c, "n_dem_pron"), n(c, "n_dem_det")) == (2, 1)
    # boundary: complementiser 'that' is not a demonstrative
    assert n(counts("She said that he left."), "n_dem_pron") + n(counts("She said that he left."), "n_dem_det") == 0


def test_tense_and_perfect(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("She had written two letters. They walked home.")
    assert (n(c, "n_tense_past"), n(c, "n_perfect"), n(c, "n_finite_verbs")) == (2, 1, 2)
    assert n(counts("She writes letters."), "n_tense_past") == 0


def test_progressive_and_passive(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("The house is being painted. He is reading a book. The letter was sent by mail.")
    assert (n(c, "n_passive"), n(c, "n_progressive")) == (2, 1)  # passive progressive counts as passive only
    assert n(counts("He read the letter."), "n_passive") == 0


def test_modal_classes(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("You can go. You must stay. It will rain. They might come. We should leave.")
    assert (n(c, "n_modal_possibility"), n(c, "n_modal_necessity"), n(c, "n_modal_prediction")) == (2, 2, 1)
    assert n(counts("They go home."), "n_modal_possibility") == 0


def test_negation_and_questions(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("Do you like it? I do not know. Why did he leave? She left?")
    assert n(c, "n_neg") == 1
    assert n(c, "n_qmark_sents") == 3
    assert n(c, "n_interrogative_sents") == 2  # declarative question 'She left?' is orthographic only
    assert n(counts("I know it. He left."), "n_qmark_sents") == 0


def test_imperatives(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("Open the door. Then add two cups of flour. He opened the door.")
    assert n(c, "n_imperative_sents") == 2
    assert n(counts("You open the door."), "n_imperative_sents") == 0


def test_nominalisation_and_modification(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("The organization of the government requires careful management and transparency.")
    # organization (-tion), government (-ment), management (-ment); transparency (-ency) is not in the list.
    # 'government' shows that the rule is a string heuristic: it is not a deverbal nominalisation in the strict sense.
    assert n(c, "n_nominalisation") == 3
    assert n(c, "n_amod") >= 1
    # boundary: short words ending in a suffix are not counted (len >= 7)
    assert n(counts("The city is nice."), "n_nominalisation") == 0


def test_clause_proxies(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("The man who called yesterday said that he wanted to come because it was late.")
    assert (n(c, "n_relcl"), n(c, "n_advcl"), n(c, "n_ccomp_xcomp")) == (1, 1, 2)


def test_punctuation_is_not_counted_as_a_word(counts) -> None:  # type: ignore[no-untyped-def]
    c = counts("Hello , world !!! ...")
    assert n(c, "n_tokens_nonpunct") == 2
