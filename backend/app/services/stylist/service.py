"""AI stylist: picks an outfit from the live catalog with a local model.

A small model handles two simple tasks far better than one complicated one,
so a request goes through these steps:

1. ``catalog``: load every product the store can sell right now;
2. ``understand``: ask the model which kinds of items the shopper wants to buy
   («пальто и обувь, остальное есть»), and note what cannot fit the budget;
3. keep the products of those kinds that fit the budget;
4. ``outfit``: ask the model to choose pieces, checking its answer in ``replies``.

Everything checkable (stock, budget, categories) is checked in code; the model
only reads and chooses.
"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.catalog import ProductRead
from app.schemas.stylist import OutfitItem, OutfitRead, OutfitRequest
from app.services.stylist.catalog import active_categories, sellable
from app.services.stylist.outfit import choose
from app.services.stylist.understand import budget_notes, group_of, understand
from core.config import settings


def empty(title: str, summary: str, budget: Decimal, notes: list[str]) -> OutfitRead:
    return OutfitRead(
        title=title, summary=summary, items=[], total=Decimal(0), budget=budget, notes=notes
    )


async def suggest(db: AsyncSession, payload: OutfitRequest) -> OutfitRead:
    request = payload.prompt.strip()
    offers = await sellable(db, payload.audience)
    categories = await active_categories(db)

    groups = await understand(request, categories, offers)
    notes = budget_notes(groups, offers, payload.budget)

    found = [
        offer
        for offer in offers
        if offer.price <= payload.budget and (not groups or group_of(offer, groups))
    ][: settings.STYLIST_MAX_CANDIDATES]
    if not found:
        if notes:
            return empty("Не нашлось в бюджете", "", payload.budget, notes)
        return empty(
            "Ничего не нашлось",
            "В этом бюджете сейчас нет подходящих вещей в наличии.",
            payload.budget,
            notes,
        )

    outfit = await choose(found, groups, request, payload.budget)
    if not outfit.picks:
        return empty(
            "Не удалось собрать образ",
            "Попробуйте описать повод подробнее или увеличить бюджет.",
            payload.budget,
            notes,
        )

    picks = outfit.picks
    return OutfitRead(
        title=outfit.suggestion.title or "Ваш образ",
        # The summary may describe a piece that was dropped or never fit the budget.
        summary=(outfit.suggestion.summary or "") if outfit.complete and not notes else "",
        items=[
            OutfitItem(
                product=ProductRead.model_validate(outfit.offers[pick.candidate.code].product),
                variant_id=pick.candidate.variant_id,
                price=pick.candidate.price,
                reason=pick.reason,
            )
            for pick in picks
        ],
        total=sum((pick.candidate.price for pick in picks), Decimal(0)),
        budget=payload.budget,
        notes=notes,
    )
