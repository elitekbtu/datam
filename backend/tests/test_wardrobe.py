"""Run with ``make test``, or point both DATABASE_URL and TEST_DATABASE_URL at a *_test database."""

import os
import tempfile
import unittest
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url

temporary = tempfile.TemporaryDirectory(prefix="datam-wardrobe-test-")
test_database_url = os.environ.get("TEST_DATABASE_URL")
if test_database_url is not None:
    parsed_url = make_url(test_database_url)
    if parsed_url.drivername != "postgresql+asyncpg" or not (parsed_url.database or "").endswith(
        "_test"
    ):
        raise RuntimeError("TEST_DATABASE_URL must point to a PostgreSQL database ending in _test")
os.environ["DATABASE_URL"] = (
    test_database_url or "postgresql+asyncpg://invalid:invalid@127.0.0.1/datam_test"
)
os.environ["MEDIA_ROOT"] = str(Path(temporary.name) / "media")
os.environ["DEBUG"] = "false"
os.environ["COOKIE_SECURE"] = "false"
os.environ["SECRET_KEY"] = "wardrobe-test-secret-at-least-32-chars"

from app import models  # noqa: E402,F401
from app.services.wardrobe.service import is_own_photo  # noqa: E402
from core.config import settings  # noqa: E402
from database.base import Base  # noqa: E402
from database.session import engine  # noqa: E402
from main import app  # noqa: E402
from seed import main as seed_demo  # noqa: E402

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00"
    b"\x00\x00IEND\xaeB`\x82"
)


async def signed_up(client: AsyncClient, name: str) -> dict[str, str]:
    """Register a shopper on ``client`` and return the headers its writes need."""
    token = (await client.get("/api/auth/csrf")).json()["csrf_token"]
    headers = {"X-CSRF-Token": token}
    registered = await client.post(
        "/api/auth/register",
        headers=headers,
        json={"email": f"{name}@example.com", "username": name, "password": "StrongPass123"},
    )
    assert registered.status_code == 201, registered.text
    return headers


def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@unittest.skipUnless(test_database_url, "Set TEST_DATABASE_URL to a disposable PostgreSQL database")
class WardrobeFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # Pooled connections of an earlier test belong to its event loop; drop them unclosed.
        await engine.dispose(close=False)

    async def asyncTearDown(self) -> None:
        await engine.dispose()

    async def test_wardrobe_flow(self) -> None:
        if not (engine.url.database or "").endswith("_test"):
            raise RuntimeError(f"Refusing to reset {engine.url.database!r}: not a *_test database")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        await seed_demo()

        async with client() as owner, client() as stranger:
            self.assertEqual((await owner.get("/api/wardrobe")).status_code, 401)
            headers = await signed_up(owner, "owner")
            stranger_headers = await signed_up(stranger, "stranger")

            categories = (await owner.get("/api/catalog/categories?limit=100")).json()["items"]
            category_id = categories[0]["id"]

            created = await owner.post(
                "/api/wardrobe",
                headers=headers,
                json={
                    "name": "Белая рубашка",
                    "category_id": category_id,
                    "formality": "smart_casual",
                    "color": "white",
                },
            )
            self.assertEqual(created.status_code, 201, created.text)
            shirt = created.json()
            self.assertIsNone(shirt["product_id"])
            self.assertIsNone(shirt["image_url"])

            unknown = await owner.post(
                "/api/wardrobe",
                headers=headers,
                json={"name": "Шарф", "category_id": "00000000-0000-0000-0000-000000000000"},
            )
            self.assertEqual(unknown.status_code, 400)
            extra = await owner.post(
                "/api/wardrobe", headers=headers, json={"name": "Шарф", "image_url": "x"}
            )
            self.assertEqual(extra.status_code, 422)

            product = (await owner.get("/api/catalog/products?limit=1")).json()["items"][0]
            bought = await owner.post(
                "/api/wardrobe/from-product", headers=headers, json={"product_id": product["id"]}
            )
            self.assertEqual(bought.status_code, 201, bought.text)
            self.assertEqual(bought.json()["product_id"], product["id"])
            self.assertEqual(bought.json()["name"], product["name"])
            self.assertEqual(bought.json()["category_id"], product["category"]["id"])
            again = await owner.post(
                "/api/wardrobe/from-product", headers=headers, json={"product_id": product["id"]}
            )
            self.assertEqual(again.json()["id"], bought.json()["id"])

            listing = (await owner.get("/api/wardrobe")).json()
            self.assertEqual(listing["total"], 2)
            for term in ("   ", "%", "_"):
                found = (await owner.get("/api/wardrobe", params={"search": term})).json()
                self.assertEqual(found["total"], 2 if term.isspace() else 0, term)
            filtered = (await owner.get("/api/wardrobe?formality=smart_casual&search=рубаш")).json()
            self.assertEqual([item["id"] for item in filtered["items"]], [shirt["id"]])

            item_url = f"/api/wardrobe/{shirt['id']}"
            self.assertEqual((await stranger.get(item_url)).status_code, 404)
            self.assertEqual(
                (await stranger.delete(item_url, headers=stranger_headers)).status_code, 404
            )
            self.assertEqual((await stranger.get("/api/wardrobe")).json()["total"], 0)

            updated = await owner.patch(
                item_url, headers=headers, json={"color": None, "note": "Под пиджак"}
            )
            self.assertEqual(updated.status_code, 200, updated.text)
            self.assertIsNone(updated.json()["color"])
            self.assertEqual(updated.json()["note"], "Под пиджак")
            self.assertEqual(updated.json()["name"], "Белая рубашка")

            rejected = await owner.put(
                f"{item_url}/photo",
                headers=headers,
                files={"file": ("shirt.txt", b"hello", "text/plain")},
            )
            self.assertEqual(rejected.status_code, 400)
            photo = await owner.put(
                f"{item_url}/photo",
                headers=headers,
                files={"file": ("shirt.png", PNG, "image/png")},
            )
            self.assertEqual(photo.status_code, 200, photo.text)
            photo_url = photo.json()["image_url"]
            self.assertTrue(photo_url.startswith(f"{settings.MEDIA_URL}/wardrobe/"))
            stored = settings.MEDIA_ROOT / photo_url.removeprefix(f"{settings.MEDIA_URL}/")
            self.assertTrue(stored.is_file())

            self.assertEqual((await owner.delete(item_url, headers=headers)).status_code, 204)
            self.assertFalse(stored.exists())
            self.assertEqual((await owner.get(item_url)).status_code, 404)

            self.assertFalse(is_own_photo(f"{settings.MEDIA_URL}/products/1/a.jpg"))
            deleted = await owner.delete(f"/api/wardrobe/{bought.json()['id']}", headers=headers)
            self.assertEqual(deleted.status_code, 204)
            self.assertEqual((await owner.get("/api/wardrobe")).json()["total"], 0)
