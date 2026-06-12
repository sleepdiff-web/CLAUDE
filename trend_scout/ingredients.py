"""Recognise, extract, and normalise ingredient names from free text.

This module solves the messy part of discovery: turning a noisy phrase like
"berberine benefits for weight loss reddit" into the core ingredient
("berberine"), and pulling plausible ingredient candidates out of Reddit post
titles. It leans on a seed lexicon (data/ingredient_lexicon.txt) plus a set of
heuristics so it can also surface NEW terms not yet in the lexicon.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_LEXICON_PATH = Path(__file__).resolve().parent.parent / "data" / "ingredient_lexicon.txt"

# Words that frequently decorate a search query / post title but are not part
# of the ingredient itself. Stripped from the edges of candidate phrases.
_MODIFIERS = {
    "benefits", "benefit", "supplement", "supplements", "dosage", "dose",
    "reddit", "review", "reviews", "results", "result", "side", "effects",
    "effect", "best", "top", "buy", "where", "near", "me", "for", "vs",
    "and", "or", "the", "a", "an", "of", "with", "without", "how", "to",
    "use", "using", "take", "taking", "is", "are", "good", "bad", "does",
    "do", "what", "weight", "loss", "gain", "muscle", "skin", "hair", "sleep",
    "anxiety", "energy", "daily", "powder", "capsules", "capsule", "pills",
    "pill", "extract", "organic", "pure", "natural", "health", "healthy",
    "supplementation", "stack", "guide", "anyone", "tried", "trying", "help",
    "question", "advice", "new", "study", "research", "experience", "my",
    "i", "you", "your", "this", "that", "have", "has", "had", "been", "from",
    "in", "on", "at", "by", "it", "its", "as", "be", "can", "could", "should",
    "would", "any", "more", "most", "much", "really", "just", "about", "vs.",
    "amazon", "brand", "brands", "price", "cheap", "high", "low", "quality",
}

# Generic stopwords that should never appear as a standalone candidate.
_JUNK_TERMS = _MODIFIERS | {
    "supplements", "vitamins", "vitamin", "minerals", "mineral", "pills",
    "powder", "capsule", "herbs", "herb", "tea", "drink", "food", "diet",
}

# Suffixes that strongly suggest a botanical / ingredient even if unknown.
_INGREDIENT_SUFFIXES = (
    "root", "berry", "berries", "seed", "leaf", "bark", "fruit", "grass",
    "mushroom", "oil", "acid", "extract", "powder", "weed", "vine", "flower",
    "tea", "moss", "pollen", "wort", "thistle", "ginseng",
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")


def normalize(text: str) -> str:
    """Lowercase, collapse punctuation/whitespace to single spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@lru_cache(maxsize=1)
def load_lexicon() -> frozenset[str]:
    if not _LEXICON_PATH.exists():
        return frozenset()
    terms = set()
    for line in _LEXICON_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        terms.add(normalize(line))
    return frozenset(terms)


def is_known_ingredient(term: str) -> bool:
    """True if the normalised term (or a token-subset) is in the lexicon."""
    norm = normalize(term)
    if not norm:
        return False
    lex = load_lexicon()
    if norm in lex:
        return True
    # A multiword phrase counts as known if it contains a known ingredient
    # as a contiguous sub-phrase (e.g. "organic ashwagandha root" -> ashwagandha).
    tokens = norm.split()
    for size in range(len(tokens), 0, -1):
        for i in range(len(tokens) - size + 1):
            if " ".join(tokens[i : i + size]) in lex:
                return True
    return False


def _strip_modifiers(tokens: list[str]) -> list[str]:
    """Drop modifier words from the edges, keep the core phrase."""
    start, end = 0, len(tokens)
    while start < end and tokens[start] in _MODIFIERS:
        start += 1
    while end > start and tokens[end - 1] in _MODIFIERS:
        end -= 1
    return tokens[start:end]


def core_ingredient(query: str) -> str | None:
    """Reduce a noisy query/title to its core ingredient phrase.

    Strategy:
      1. If the query contains a known lexicon ingredient, return the longest
         such match (most specific, e.g. "magnesium glycinate" over "magnesium").
      2. Otherwise strip modifier words and, if what remains looks
         ingredient-like (1-3 tokens, has an ingredient suffix or is a single
         uncommon noun), treat it as a NEW candidate.
    Returns None when nothing plausible remains.
    """
    norm = normalize(query)
    if not norm:
        return None
    tokens = norm.split()
    lex = load_lexicon()

    # 1. Longest contiguous lexicon match wins.
    best: str | None = None
    for size in range(min(3, len(tokens)), 0, -1):
        for i in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[i : i + size])
            if phrase in lex:
                if best is None or len(phrase) > len(best):
                    best = phrase
    if best:
        return best

    # 2. Novel candidate: strip decoration, keep a short core.
    core = _strip_modifiers(tokens)
    if not core or len(core) > 3:
        return None
    phrase = " ".join(core)
    if phrase in _JUNK_TERMS:
        return None
    if all(t in _JUNK_TERMS for t in core):
        return None
    if _looks_ingredient_like(core):
        return phrase
    return None


def _looks_ingredient_like(tokens: list[str]) -> bool:
    """Heuristic for an unknown-but-plausible ingredient phrase."""
    if not tokens:
        return False
    last = tokens[-1]
    if any(last.endswith(suf) for suf in _INGREDIENT_SUFFIXES):
        return True
    # A single, reasonably long token that isn't junk: plausible novel name.
    if len(tokens) == 1 and len(tokens[0]) >= 5 and tokens[0] not in _JUNK_TERMS:
        return True
    # Two-token botanical-style name (e.g. "tongkat ali", "bacopa monnieri").
    if len(tokens) == 2 and all(len(t) >= 3 and t not in _JUNK_TERMS for t in tokens):
        return True
    return False


@dataclass(frozen=True)
class Candidate:
    term: str            # normalised core ingredient
    source: str          # "trends" | "reddit"
    known: bool          # already in the lexicon?
    context: str = ""    # the raw phrase it came from


def extract_candidates_from_text(text: str, source: str) -> list[Candidate]:
    """Pull candidate ingredients out of an arbitrary block of text.

    Builds 1-3 grams, keeps those that are known ingredients or look
    ingredient-like. Used for Reddit titles/bodies where the ingredient is
    embedded in a sentence.
    """
    norm = normalize(text)
    if not norm:
        return []
    tokens = norm.split()
    seen: set[str] = set()
    out: list[Candidate] = []
    for size in (1, 2, 3):
        for i in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[i : i + size])
            if phrase in seen:
                continue
            if is_known_ingredient(phrase):
                seen.add(phrase)
                out.append(Candidate(term=phrase, source=source, known=True, context=text[:200]))
    return out


def candidate_from_query(query: str, source: str) -> Candidate | None:
    """Turn a single Trends rising-query string into one candidate."""
    core = core_ingredient(query)
    if not core:
        return None
    return Candidate(
        term=core,
        source=source,
        known=is_known_ingredient(core),
        context=query,
    )
