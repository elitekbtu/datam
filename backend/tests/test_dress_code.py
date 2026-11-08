"""Run with ``python -m unittest tests.test_dress_code`` from ``backend/``."""

import os
import unittest
import uuid
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://invalid:invalid@127.0.0.1/datam_test")
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-0123456789abcdef")

from app.services.stylist.catalog import Offer
from app.services.stylist.dress_code import allowed, is_formal, ruled_out
from app.services.stylist.understand import Group
from utils.enums import Formality


def product(formality: Formality | None, category_id: uuid.UUID | None = None) -> SimpleNamespace:
    return SimpleNamespace(formality=formality, category_id=category_id or uuid.uuid4())


class IsFormal(unittest.TestCase):
    def test_formal_occasions(self) -> None:
        for request in (
            "Собеседование в офисе, нужен строгий образ",
            "Свадьба друга в субботу",
            "Деловая встреча с партнёрами",
            "Официальный ужин",
            "Formal dinner at a hotel",
        ):
            with self.subTest(request=request):
                self.assertTrue(is_formal(request))

    def test_relaxed_codes_are_not_formal(self) -> None:
        for request in (
            "Свидание вечером, дресс-код smart casual",
            "Деловой кэжуал на работу",
            "Business casual в офис",
            "Прогулка в парке",
        ):
            with self.subTest(request=request):
                self.assertFalse(is_formal(request))


class Allowed(unittest.TestCase):
    def test_formal_occasion_rejects_only_casual_items(self) -> None:
        self.assertFalse(allowed(product(Formality.CASUAL), formal=True))
        self.assertTrue(allowed(product(Formality.SMART_CASUAL), formal=True))
        self.assertTrue(allowed(product(Formality.FORMAL), formal=True))

    def test_untagged_items_are_not_judged(self) -> None:
        self.assertTrue(allowed(product(None), formal=True))

    def test_relaxed_occasion_keeps_everything(self) -> None:
        self.assertTrue(allowed(product(Formality.CASUAL), formal=False))


class RuledOut(unittest.TestCase):
    def test_names_a_requested_kind_that_is_only_casual(self) -> None:
        shoes = uuid.uuid4()
        offers = [Offer(product(Formality.CASUAL, shoes), None, Decimal("69900"))]
        notes = ruled_out([Group("обувь", shoes, frozenset({shoes}))], offers)
        self.assertEqual(len(notes), 1)
        self.assertTrue(notes[0].startswith("Обувь:"))

    def test_silent_when_a_suitable_option_exists(self) -> None:
        shoes = uuid.uuid4()
        offers = [
            Offer(product(Formality.CASUAL, shoes), None, Decimal("69900")),
            Offer(product(Formality.SMART_CASUAL, shoes), None, Decimal("78900")),
        ]
        self.assertEqual(ruled_out([Group("обувь", shoes, frozenset({shoes}))], offers), [])


if __name__ == "__main__":
    unittest.main()
