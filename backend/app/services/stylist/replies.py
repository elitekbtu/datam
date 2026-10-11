"""Reading the model's replies and holding them to what the store can sell.

A small local model is good at matching clothes to an occasion but not at
arithmetic or following rules, so everything checkable is checked here.
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from itertools import combinations

CODE = re.compile(r"\bP(\d+)\b")
#: Caps the subset search; an outfit never needs more pieces than this.
MAX_PICKS = 6


@dataclass(frozen=True)
class Candidate:
    """A product offered to the model under a short code like ``P3``."""

    code: str
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    category: str
    price: Decimal


@dataclass(frozen=True)
class Suggestion:
    title: str | None = None
    summary: str | None = None
    picks: list[tuple[str, str | None]] = field(default_factory=list)


@dataclass(frozen=True)
class Pick:
    candidate: Candidate
    reason: str | None


def _text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _code(value: object) -> str | None:
    match = CODE.search(value.upper()) if isinstance(value, str) else None
    return f"P{int(match.group(1))}" if match else None


def _json_object(reply: str) -> object:
    """The JSON object in the reply, even when wrapped in markdown or prose."""
    start, end = reply.find("{"), reply.rfind("}")
    try:
        return json.loads(reply[start : end + 1]) if start != -1 else None
    except json.JSONDecodeError:
        return None


def stem(word: str) -> str:
    """A crude Russian stem: enough to match «сумку» against «сумка»."""
    word = word.strip().casefold()
    return word[: max(4, len(word) - 2)]


@dataclass(frozen=True)
class Wanted:
    """A kind of item the shopper asked to buy, quoted from their request."""

    word: str
    category: str


def parse_wanted(reply: str, request: str) -> list[Wanted]:
    """Read which items the shopper wants, keeping only ones they really wrote.

    The model must quote the shopper's own word for each item; a word missing
    from the request means the model made the item up.
    """
    data = _json_object(reply)
    items = data.get("wanted") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    text = request.casefold()
    wanted = []
    for item in items:
        if not isinstance(item, dict):
            continue
        word, category = _text(item.get("word")), _text(item.get("category"))
        if word and category and len(word) >= 3 and stem(word) in text:
            wanted.append(Wanted(word, category))
    return wanted


def parse_reply(reply: str) -> Suggestion:
    """Read the model's JSON, falling back to any product codes in the text."""
    data = _json_object(reply)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        picks = []
        for item in data["items"]:
            if isinstance(item, dict):
                code, reason = _code(item.get("id")), _text(item.get("reason"))
            else:
                code, reason = _code(item), None
            if code:
                picks.append((code, reason))
        return Suggestion(_text(data.get("title")), _text(data.get("summary")), picks)

    return Suggestion(picks=[(f"P{int(n)}", None) for n in CODE.findall(reply)])


def known_codes(suggestion: Suggestion, candidates: dict[str, Candidate]) -> list[str]:
    """The model's picks that exist in the catalog, without repeats."""
    return list(dict.fromkeys(c for c, _ in suggestion.picks if c in candidates))


def proposed_total(
    suggestion: Suggestion, candidates: dict[str, Candidate]
) -> Decimal:
    """What the model's own picks add up to, before any are dropped."""
    codes = known_codes(suggestion, candidates)
    return sum((candidates[code].price for code in codes), Decimal(0))


def assemble(
    suggestion: Suggestion, candidates: dict[str, Candidate], budget: Decimal
) -> list[Pick]:
    """The most pieces from the model's picks that fit the budget together.

    Only known codes count, one per category. Among equally large sets the one
    that uses more of the budget wins; picks keep the model's order.
    """
    reasons: dict[str, str | None] = {}
    categories: set[str] = set()
    for code, reason in suggestion.picks:
        candidate = candidates.get(code)
        if candidate is None or code in reasons or candidate.category in categories:
            continue
        reasons[code] = reason
        categories.add(candidate.category)
        if len(reasons) == MAX_PICKS:
            break

    codes = list(reasons)
    for size in range(len(codes), 0, -1):
        fitting = [
            combo
            for combo in combinations(codes, size)
            if sum(candidates[code].price for code in combo) <= budget
        ]
        if fitting:
            best = max(fitting, key=lambda combo: sum(candidates[c].price for c in combo))
            return [Pick(candidates[code], reasons[code]) for code in best]
    return []
