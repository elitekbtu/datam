"""Step 2: let the model choose pieces, then hold its choice to the rules."""

from decimal import Decimal
from typing import NamedTuple

from app.services.stylist import ollama
from app.services.stylist.catalog import Offer
from app.services.stylist.prompts import (
    PICK_PROMPT,
    catalog_line,
    correction,
    outfit_request,
)
from app.services.stylist.replies import (
    Candidate,
    Pick,
    Suggestion,
    assemble,
    known_codes,
    parse_reply,
)
from app.services.stylist.understand import Group, group_of


class Outfit(NamedTuple):
    suggestion: Suggestion
    picks: list[Pick]
    offers: dict[str, Offer]
    #: Every piece the model chose made it in, so its summary still holds.
    complete: bool


def offer_codes(
    found: list[Offer], groups: list[Group]
) -> tuple[dict[str, Candidate], dict[str, Offer]]:
    """Number the products ``P1``, ``P2``… so the model can name them reliably."""
    offered: dict[str, Candidate] = {}
    by_code: dict[str, Offer] = {}
    for number, offer in enumerate(found, start=1):
        code = f"P{number}"
        group = group_of(offer, groups)
        offered[code] = Candidate(
            code=code,
            product_id=offer.product.id,
            variant_id=offer.variant.id if offer.variant else None,
            # Asked-for kinds count as one slot: one pair of shoes, not two.
            category=str(group.root if group else offer.product.category_id),
            price=offer.price,
        )
        by_code[code] = offer
    return offered, by_code


async def choose(
    found: list[Offer], groups: list[Group], request: str, budget: Decimal
) -> Outfit:
    offered, by_code = offer_codes(found, groups)
    words = list(dict.fromkeys(g.word for o in found if (g := group_of(o, groups))))
    lines = [catalog_line(code, by_code[code]) for code in offered]
    messages = [{"role": "user", "content": outfit_request(lines, words, budget, request)}]

    reply = await ollama.chat_json(PICK_PROMPT, messages)
    suggestion = parse_reply(reply)
    picks = assemble(suggestion, offered, budget)
    complete = len(picks) == len(known_codes(suggestion, offered))

    if not picks or not complete:
        # Small models add prices badly; one round of feedback usually fixes it.
        messages += [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": correction(suggestion, offered, budget)},
        ]
        retry = parse_reply(await ollama.chat_json(PICK_PROMPT, messages))
        retry_picks = assemble(retry, offered, budget)
        if retry_picks and len(retry_picks) >= len(picks):
            suggestion, picks = retry, retry_picks
            complete = len(picks) == len(known_codes(retry, offered))

    return Outfit(suggestion, picks, by_code, complete)
