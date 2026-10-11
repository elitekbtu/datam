"""AI stylist: picks an outfit from the live catalog with a local model.

A small model handles two simple tasks far better than one complicated one,
so a request takes two short calls:

1. understand: which kinds of items the shopper asked to buy, if they named any
   («пальто и обувь, остальное есть»);
2. pick: choose pieces from the matching in-stock products within budget.

Everything checkable (stock, budget, categories) is checked in code.
"""

import uuid
from decimal import Decimal
from typing import Final, NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Product, ProductVariant
from app.schemas.catalog import ProductRead
from app.schemas.stylist import OutfitItem, OutfitRead, OutfitRequest
from app.services.commerce.common import price_for
from app.services.stylist import ollama
from app.services.stylist.picking import (
    Candidate,
    Suggestion,
    Wanted,
    assemble,
    known_codes,
    parse_reply,
    parse_wanted,
    proposed_total,
    stem,
)
from core.config import settings
from utils.enums import Audience, Currency

AUDIENCE_LABELS: Final = {
    Audience.WOMEN: "женское",
    Audience.MEN: "мужское",
    Audience.UNISEX: "унисекс",
}

UNDERSTAND_PROMPT: Final = (
    "Ты помощник магазина одежды. Найди в запросе клиента вещи, которые он прямо "
    "просит КУПИТЬ, и сопоставь каждую с категорией из списка. Не включай вещи, "
    "которые у клиента уже есть. Если клиент не назвал конкретные вещи, а просит "
    "подобрать образ, верни пустой список. Для каждой вещи укажи слово ровно так, "
    "как оно написано у клиента. Примеры: «нужно пальто и обувь, остальное есть» "
    '-> {"wanted": [{"word": "пальто", "category": "Верхняя одежда"}, '
    '{"word": "обувь", "category": "Обувь"}]}; «собери образ на свидание» -> '
    '{"wanted": []}. Верни ТОЛЬКО JSON.'
)

PICK_PROMPT: Final = (
    "Ты стилист интернет-магазина одежды DATAM. Подбери вещи ТОЛЬКО из товаров "
    "каталога, который даст пользователь. Учитывай повод, погоду, дресс-код и "
    "пожелания клиента. Бери не больше одной вещи из каждой категории и не больше "
    "5 вещей всего. Сумма цен не должна превышать бюджет. Отвечай на русском, "
    "коротко. Верни ТОЛЬКО JSON без markdown: "
    '{"title": "название образа", "summary": "1-2 предложения о настроении и '
    'стиле образа, без перечисления вещей", "items": [{"id": "P1", "reason": '
    '"зачем эта вещь"}]}'
)


class Offer(NamedTuple):
    """A product the store can sell right now, in its suggested size."""

    product: Product
    variant: ProductVariant | None
    price: Decimal


class Group(NamedTuple):
    """The products one word of the request covers, e.g. «обувь» → all shoes."""

    word: str
    root: uuid.UUID
    category_ids: frozenset[uuid.UUID]


def tenge(amount: Decimal) -> str:
    return f"{amount:,.0f} ₸".replace(",", " ")


def suggested_variant(product: Product) -> ProductVariant | None:
    """The first in-stock size, or ``None`` for a product sold without sizes."""
    return next(
        (v for v in product.variants if v.is_active and v.stock > 0), None
    )


async def sellable(db: AsyncSession, audience: Audience | None) -> list[Offer]:
    """Every product a shopper could order right now, newest first."""
    query = (
        select(Product)
        .join(Category, Product.category_id == Category.id)
        .where(
            Product.is_active.is_(True),
            Category.is_active.is_(True),
            Product.currency == Currency.KZT,
        )
        .order_by(Product.created_at.desc(), Product.id)
    )
    if audience is not None:
        query = query.where(Product.audience.in_([audience, Audience.UNISEX]))

    offers = []
    for product in (await db.scalars(query)).unique():
        if product.in_stock:
            variant = suggested_variant(product)
            offers.append(Offer(product, variant, price_for(product, variant)))
    return offers


def descendants(root: uuid.UUID, categories: list[Category]) -> frozenset[uuid.UUID]:
    found, frontier = {root}, [root]
    while frontier:
        parent = frontier.pop()
        for category in categories:
            if category.parent_id == parent and category.id not in found:
                found.add(category.id)
                frontier.append(category.id)
    return frozenset(found)


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
    names = ", ".join(category.name for category in categories)
    reply = await ollama.chat_json(
        UNDERSTAND_PROMPT,
        [{"role": "user", "content": f"Категории: {names}\nЗапрос клиента: {request}"}],
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


def catalog_line(code: str, offer: Offer) -> str:
    product = offer.product
    description = " ".join((product.description or "").split())[:140]
    return " | ".join(
        (
            code,
            product.name,
            product.category.name,
            AUDIENCE_LABELS[product.audience],
            tenge(offer.price),
            description,
        )
    )


def correction(
    suggestion: Suggestion, offered: dict[str, Candidate], budget: Decimal
) -> str:
    total = proposed_total(suggestion, offered)
    if not known_codes(suggestion, offered):
        problem = "Используй только коды товаров из каталога, например P1."
    elif total > budget:
        problem = (
            f"Вещи стоят {total:.0f} ₸, а бюджет {budget:.0f} ₸. "
            "Замени дорогие вещи более дешёвыми или убери лишние."
        )
    else:
        problem = "Нельзя брать две вещи из одной категории."
    return f"Этот образ не подходит. {problem} Верни исправленный JSON."


def empty(title: str, summary: str, budget: Decimal, notes: list[str]) -> OutfitRead:
    return OutfitRead(
        title=title, summary=summary, items=[], total=Decimal(0), budget=budget, notes=notes
    )


async def suggest(db: AsyncSession, payload: OutfitRequest) -> OutfitRead:
    request = payload.prompt.strip()
    offers = await sellable(db, payload.audience)
    categories = list(
        await db.scalars(select(Category).where(Category.is_active.is_(True)))
    )

    groups = await understand(request, categories, offers)
    notes = budget_notes(groups, offers, payload.budget)

    def group_of(offer: Offer) -> Group | None:
        return next((g for g in groups if offer.product.category_id in g.category_ids), None)

    found = [
        offer
        for offer in offers
        if offer.price <= payload.budget and (not groups or group_of(offer))
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

    offered: dict[str, Candidate] = {}
    by_code: dict[str, Offer] = {}
    for number, offer in enumerate(found, start=1):
        code = f"P{number}"
        group = group_of(offer)
        offered[code] = Candidate(
            code=code,
            product_id=offer.product.id,
            variant_id=offer.variant.id if offer.variant else None,
            # Asked-for kinds count as one slot: one pair of shoes, not two.
            category=str(group.root if group else offer.product.category_id),
            price=offer.price,
        )
        by_code[code] = offer

    if groups:
        words = list(dict.fromkeys(g.word for o in found if (g := group_of(o))))
        task = (
            f"Клиенту нужны только: {', '.join(words)}. "
            "Возьми по одной вещи каждого вида и ничего больше."
        )
    else:
        task = "Собери полный образ из 2–5 вещей."
    prompt = (
        "Каталог (код | название | категория | для кого | цена | описание):\n"
        + "\n".join(catalog_line(code, by_code[code]) for code in offered)
        + f"\n\nБюджет: {payload.budget:.0f} ₸\n{task}\nЗапрос клиента: {request}"
    )
    messages = [{"role": "user", "content": prompt}]
    reply = await ollama.chat_json(PICK_PROMPT, messages)
    suggestion = parse_reply(reply)
    picks = assemble(suggestion, offered, payload.budget)

    complete = len(picks) == len(known_codes(suggestion, offered))
    if not picks or not complete:
        # Small models add prices badly; one round of feedback usually fixes it.
        messages += [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": correction(suggestion, offered, payload.budget)},
        ]
        retry = parse_reply(await ollama.chat_json(PICK_PROMPT, messages))
        retry_picks = assemble(retry, offered, payload.budget)
        if retry_picks and len(retry_picks) >= len(picks):
            suggestion, picks = retry, retry_picks
            complete = len(picks) == len(known_codes(retry, offered))

    if not picks:
        return empty(
            "Не удалось собрать образ",
            "Попробуйте описать повод подробнее или увеличить бюджет.",
            payload.budget,
            notes,
        )
    return OutfitRead(
        title=suggestion.title or "Ваш образ",
        # The summary may describe a piece that was dropped or never fit the budget.
        summary=(suggestion.summary or "") if complete and not notes else "",
        items=[
            OutfitItem(
                product=ProductRead.model_validate(by_code[pick.candidate.code].product),
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
