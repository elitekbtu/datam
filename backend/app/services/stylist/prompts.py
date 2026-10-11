"""Everything the stylist says to the model, kept in one place to tune."""

from decimal import Decimal
from typing import Final

from app.services.stylist.catalog import Offer
from app.services.stylist.replies import (
    Candidate,
    Suggestion,
    known_codes,
    proposed_total,
)
from utils.enums import Audience

AUDIENCE_LABELS: Final = {
    Audience.WOMEN: "женское",
    Audience.MEN: "мужское",
    Audience.UNISEX: "унисекс",
}

#: Step 1: which kinds of items the shopper asked to buy.
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

#: Step 2: choose pieces from the offered catalog.
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


def tenge(amount: Decimal) -> str:
    return f"{amount:,.0f} ₸".replace(",", " ")


def understand_request(category_names: list[str], request: str) -> str:
    return f"Категории: {', '.join(category_names)}\nЗапрос клиента: {request}"


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


def outfit_request(
    lines: list[str], wanted_words: list[str], budget: Decimal, request: str
) -> str:
    task = (
        f"Клиенту нужны только: {', '.join(wanted_words)}. "
        "Возьми по одной вещи каждого вида и ничего больше."
        if wanted_words
        else "Собери полный образ из 2–5 вещей."
    )
    return (
        "Каталог (код | название | категория | для кого | цена | описание):\n"
        + "\n".join(lines)
        + f"\n\nБюджет: {budget:.0f} ₸\n{task}\nЗапрос клиента: {request}"
    )


def correction(
    suggestion: Suggestion, offered: dict[str, Candidate], budget: Decimal
) -> str:
    """Tell the model what was wrong with its outfit so it can try again."""
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
