"""Dress-code rule checked in code, so a formal request never gets a casual item."""

from app.models.catalog import Product
from app.services.stylist.catalog import Offer
from app.services.stylist.understand import Group
from utils.enums import Formality

# Relaxed codes win: «деловой кэжуал» or «business casual» is not a formal event.
RELAXED = ("casual", "кэжуал", "кежуал", "повседнев")
FORMAL = (
    "строг",
    "собеседован",
    "официальн",
    "делов",
    "свадьб",
    "торжеств",
    "formal",
    "business",
    "black tie",
)


def is_formal(request: str) -> bool:
    text = request.casefold()
    if any(word in text for word in RELAXED):
        return False
    return any(word in text for word in FORMAL)


def allowed(product: Product, formal: bool) -> bool:
    # Untagged items pass, so an untagged catalog still produces outfits.
    return not formal or product.formality is not Formality.CASUAL


def ruled_out(groups: list[Group], offers: list[Offer]) -> list[str]:
    """Notes for requested kinds of items that exist only in casual styles."""
    notes = []
    for group in groups:
        options = [o for o in offers if o.product.category_id in group.category_ids]
        if options and not any(allowed(o.product, formal=True) for o in options):
            notes.append(
                f"{group.word.capitalize()}: в наличии только повседневные модели, "
                "к строгому дресс-коду они не подходят."
            )
    return notes
