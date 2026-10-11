"""Step 1: which kinds of items the shopper asked to buy, if they named any."""

import uuid
from decimal import Decimal
from typing import NamedTuple

from app.models.catalog import Category
from app.services.stylist import ollama
from app.services.stylist.catalog import Offer, descendants
from app.services.stylist.prompts import UNDERSTAND_PROMPT, tenge, understand_request
from app.services.stylist.replies import Wanted, parse_wanted, stem


class Group(NamedTuple):
    """The products one word of the request covers, e.g. «обувь» → all shoes."""

    word: str
    root: uuid.UUID
    category_ids: frozenset[uuid.UUID]


def group_of(offer: Offer, groups: list[Group]) -> Group | None:
    return next((g for g in groups if offer.product.category_id in g.category_ids), None)


def resolve(
    want: Wanted, categories: list[Category], offers: list[Offer]
) -> Category | None:
    """The category the model named, or failing that, one the word points to."""
    by_name = {category.name.casefold(): category for category in categories}
    if found := by_name.get(want.category.casefold()):
        return found
    for term in (want.category, want.word):
        needle = stem(term)
        if found := next((c for c in categories if needle in c.name.casefold()), None):
            return found
    needle = stem(want.word)
    return next(
        (offer.product.category for offer in offers if needle in offer.product.name.casefold()),
        None,
    )


async def understand(
    request: str, categories: list[Category], offers: list[Offer]
) -> list[Group]:
    """Which kinds of items the shopper asked for; empty for a whole outfit."""
    reply = await ollama.chat_json(
        UNDERSTAND_PROMPT,
        [{"role": "user", "content": understand_request([c.name for c in categories], request)}],
    )
    groups: list[Group] = []
    for want in parse_wanted(reply, request):
        category = resolve(want, categories, offers)
        if category is not None and all(g.root != category.id for g in groups):
            groups.append(Group(want.word, category.id, descendants(category.id, categories)))
    return groups


def budget_notes(groups: list[Group], offers: list[Offer], budget: Decimal) -> list[str]:
    """Explain plainly when something the shopper asked for cannot fit."""
    notes = []
    cheapest_total = Decimal(0)
    all_fit = True
    for group in groups:
        label = group.word.capitalize()
        options = [o for o in offers if o.product.category_id in group.category_ids]
        if not options:
            notes.append(f"{label}: сейчас нет в наличии.")
            all_fit = False
            continue
        cheapest = min(options, key=lambda offer: offer.price)
        cheapest_total += cheapest.price
        if cheapest.price > budget:
            notes.append(
                f"{label}: самый доступный вариант «{cheapest.product.name}» стоит "
                f"{tenge(cheapest.price)}, это больше бюджета {tenge(budget)}."
            )
            all_fit = False
    if all_fit and len(groups) > 1 and cheapest_total > budget:
        notes.append(
            f"Всё вместе стоит минимум {tenge(cheapest_total)}, поэтому целиком "
            f"в бюджет {tenge(budget)} не помещается."
        )
    return notes
