"""Run with ``python -m unittest tests.test_stylist`` from ``backend/``."""

import os
import unittest
import uuid
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://invalid:invalid@127.0.0.1/datam_test")

from app.services.stylist.picking import (  # noqa: E402
    Candidate,
    Suggestion,
    assemble,
    known_codes,
    parse_reply,
    parse_wanted,
    proposed_total,
    stem,
)


def candidate(code: str, category: str, price: str) -> Candidate:
    return Candidate(code, uuid.uuid4(), None, category, Decimal(price))


class ParseReply(unittest.TestCase):
    def test_reads_json_reply(self) -> None:
        reply = '{"title": "Вечер", "summary": "Тепло.", "items": [{"id": "P2", "reason": "Тёплый"}, {"id": "p10"}]}'
        suggestion = parse_reply(reply)
        self.assertEqual(suggestion.title, "Вечер")
        self.assertEqual(suggestion.summary, "Тепло.")
        self.assertEqual(suggestion.picks, [("P2", "Тёплый"), ("P10", None)])

    def test_reads_json_wrapped_in_markdown(self) -> None:
        suggestion = parse_reply('```json\n{"items": ["P1", {"id": "P3"}]}\n```')
        self.assertEqual(suggestion.picks, [("P1", None), ("P3", None)])

    def test_falls_back_to_codes_in_plain_text(self) -> None:
        suggestion = parse_reply("Пиджак (P1), брюки (P8) и сумка P9.")
        self.assertIsNone(suggestion.title)
        self.assertEqual([code for code, _ in suggestion.picks], ["P1", "P8", "P9"])

    def test_ignores_garbage(self) -> None:
        self.assertEqual(parse_reply("не знаю").picks, [])
        self.assertEqual(parse_reply('{"items": [{"id": 5}, null]}').picks, [])


class ParseWanted(unittest.TestCase):
    request = "хочу купить пальто и обувь, сумку тоже, остальное всё есть"

    def test_keeps_words_the_shopper_wrote(self) -> None:
        reply = '{"wanted": [{"word": "пальто", "category": "Верхняя одежда"}, {"word": "сумка", "category": "Сумки"}]}'
        wanted = parse_wanted(reply, self.request)
        self.assertEqual([(w.word, w.category) for w in wanted], [("пальто", "Верхняя одежда"), ("сумка", "Сумки")])

    def test_drops_items_the_model_made_up(self) -> None:
        reply = '{"wanted": [{"word": "платье", "category": "Платья"}, {"word": "обувь", "category": "Обувь"}]}'
        self.assertEqual([w.word for w in parse_wanted(reply, self.request)], ["обувь"])

    def test_whole_outfit_and_garbage(self) -> None:
        self.assertEqual(parse_wanted('{"wanted": []}', self.request), [])
        self.assertEqual(parse_wanted("пальто", self.request), [])
        self.assertEqual(parse_wanted('{"wanted": ["пальто", {"word": "пальто"}]}', self.request), [])

    def test_stem_matches_word_forms(self) -> None:
        self.assertIn(stem("Сумка"), "купить сумку")
        self.assertIn(stem("ботинки"), "нужны ботинок")


class Assemble(unittest.TestCase):
    def setUp(self) -> None:
        self.offered = {
            c.code: c
            for c in (
                candidate("P1", "blazers", "89900"),
                candidate("P2", "knitwear", "49900"),
                candidate("P3", "knitwear", "59900"),
                candidate("P4", "sneakers", "69900"),
            )
        }

    def codes(self, picks: list[tuple[str, str | None]], budget: str) -> list[str]:
        chosen = assemble(Suggestion(picks=picks), self.offered, Decimal(budget))
        return [pick.candidate.code for pick in chosen]

    def test_keeps_model_order_and_reasons(self) -> None:
        chosen = assemble(Suggestion(picks=[("P4", "удобно"), ("P1", None)]), self.offered, Decimal("500000"))
        self.assertEqual([(p.candidate.code, p.reason) for p in chosen], [("P4", "удобно"), ("P1", None)])

    def test_drops_unknown_codes_and_repeats(self) -> None:
        self.assertEqual(self.codes([("P9", None), ("P1", None), ("P1", None)], "500000"), ["P1"])

    def test_one_item_per_category(self) -> None:
        self.assertEqual(self.codes([("P2", None), ("P3", None)], "500000"), ["P2"])

    def test_never_exceeds_budget(self) -> None:
        # All three cost 209 700; of the pairs that fit, P1 + P2 uses the most budget.
        self.assertEqual(self.codes([("P1", None), ("P4", None), ("P2", None)], "140000"), ["P1", "P2"])

    def test_prefers_more_pieces_over_the_first_pick(self) -> None:
        # P1 alone fits 120 000, but P4 + P2 makes a fuller outfit for 119 800.
        self.assertEqual(self.codes([("P1", None), ("P2", None), ("P4", None)], "120000"), ["P2", "P4"])

    def test_nothing_fits(self) -> None:
        self.assertEqual(self.codes([("P1", None)], "1000"), [])

    def test_reports_what_the_model_proposed(self) -> None:
        suggestion = Suggestion(picks=[("P1", None), ("P9", None), ("P4", None), ("P1", None)])
        self.assertEqual(known_codes(suggestion, self.offered), ["P1", "P4"])
        self.assertEqual(proposed_total(suggestion, self.offered), Decimal("159800"))


if __name__ == "__main__":
    unittest.main()
