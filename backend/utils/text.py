import re
import unicodedata

TRANSLITERATIONS = {
    "а": "a", "ә": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k",
    "қ": "k", "л": "l", "м": "m", "н": "n", "ң": "n", "о": "o", "ө": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ұ": "u", "ү": "u",
    "ф": "f", "х": "h", "һ": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "і": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase, dash separated, ASCII only; empty when nothing survives."""
    spelled = "".join(TRANSLITERATIONS.get(char, char) for char in value.lower())
    ascii_only = (
        unicodedata.normalize("NFKD", spelled).encode("ascii", "ignore").decode()
    )
    return SEPARATORS.sub("-", ascii_only).strip("-")
