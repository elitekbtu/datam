"""Run with ``backend/.venv/bin/python -m unittest discover -s tests``."""

import os
import tempfile
import unittest
import uuid
from pathlib import Path

from httpx import ASGITransport, AsyncClient

temporary = tempfile.TemporaryDirectory(prefix="datam-test-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{Path(temporary.name) / 'store.db'}"
os.environ["MEDIA_ROOT"] = str(Path(temporary.name) / "media")
os.environ["DEBUG"] = "false"
os.environ["COOKIE_SECURE"] = "false"
os.environ["SECRET_KEY"] = "storefront-test-secret-at-least-32-chars"

from app import models  # noqa: E402,F401
from database.base import Base  # noqa: E402
from database.session import engine  # noqa: E402
from main import app  # noqa: E402
from seed import main as seed_demo  # noqa: E402


class StorefrontFlow(unittest.IsolatedAsyncioTestCase):
    async def test_customer_flow(self) -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        await seed_demo()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = (await client.get("/api/auth/csrf")).json()["csrf_token"]
            headers = {"X-CSRF-Token": token}
            self.assertIsNone(
                (await client.post("/api/auth/session", headers=headers)).json()
            )
            categories = (await client.get("/api/catalog/categories?limit=100")).json()[
                "items"
            ]
            self.assertGreaterEqual(len(categories), 8)
            products = (
                await client.get(
                    "/api/catalog/products?audience=women&category=clothing"
                )
            ).json()["items"]
            self.assertTrue(products)
            self.assertTrue(
                all(product["audience"] in ("women", "unisex") for product in products)
            )
            affordable = (
                await client.get(
                    "/api/catalog/products?audience=women&max_price=50000&sort=price"
                )
            ).json()["items"]
            self.assertTrue(affordable)
            self.assertTrue(
                all(float(product["price"]) <= 50000 for product in affordable)
            )
            blazer = next(
                product
                for product in products
                if product["slug"] == "black-wool-blazer"
            )
            variant = blazer["variants"][0]
            item = {
                "product_id": blazer["id"],
                "variant_id": variant["id"],
                "quantity": 1,
            }
            self.assertEqual(
                (await client.post("/api/cart/items", json=item)).status_code, 403
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/cart/items",
                        json=item,
                        headers={**headers, "Origin": "https://untrusted.example"},
                    )
                ).status_code,
                403,
            )
            self.assertGreaterEqual(
                (
                    await client.post(
                        "/api/cart/items",
                        json={**item, "variant_id": str(uuid.uuid4())},
                        headers=headers,
                    )
                ).status_code,
                400,
            )
            added = await client.post("/api/cart/items", json=item, headers=headers)
            self.assertEqual(added.status_code, 201, added.text)
            self.assertEqual(added.json()["count"], 1)
            self.assertEqual(
                (
                    await client.post(
                        "/api/cart/items",
                        json={**item, "quantity": 99},
                        headers=headers,
                    )
                ).status_code,
                409,
            )
            self.assertEqual(
                (
                    await client.put(f"/api/favorites/{blazer['id']}", headers=headers)
                ).status_code,
                200,
            )

            registered = await client.post(
                "/api/auth/register",
                headers=headers,
                json={
                    "email": "shopper@example.com",
                    "username": "shopper",
                    "full_name": "Айдана",
                    "password": "StrongPass123",
                },
            )
            self.assertEqual(registered.status_code, 201, registered.text)
            self.assertNotIn("access_token", registered.json())
            self.assertIn("datam_access", client.cookies)
            self.assertEqual(
                (await client.post("/api/auth/session", headers=headers)).json()[
                    "username"
                ],
                "shopper",
            )
            self.assertEqual((await client.get("/api/cart")).json()["count"], 1)
            self.assertEqual(
                len((await client.get("/api/favorites")).json()["items"]), 1
            )
            self.assertEqual(
                (await client.post("/api/auth/refresh", headers=headers)).status_code,
                200,
            )
            updated = await client.patch(
                "/api/account",
                headers=headers,
                json={
                    "full_name": "Айдана С.",
                    "username": "shopper",
                    "email": "shopper@example.com",
                },
            )
            self.assertEqual(updated.status_code, 200, updated.text)
            self.assertEqual(updated.json()["full_name"], "Айдана С.")

            payload = {
                "full_name": "Айдана С.",
                "phone": "+77001234567",
                "city": "Алматы",
                "address": "Абая 10, 5",
                "postal_code": "050000",
                "note": None,
            }
            order_headers = {**headers, "Idempotency-Key": "checkout-test-001"}
            order = await client.post(
                "/api/orders", headers=order_headers, json=payload
            )
            self.assertEqual(order.status_code, 201, order.text)
            order_id = order.json()["id"]
            self.assertEqual(order.json()["total"], blazer["price"])
            self.assertEqual(
                (
                    await client.post(
                        "/api/orders", headers=order_headers, json=payload
                    )
                ).json()["id"],
                order_id,
            )
            self.assertEqual((await client.get("/api/cart")).json()["count"], 0)
            self.assertEqual((await client.get("/api/orders")).json()["total"], 1)
            self.assertEqual(
                (await client.get(f"/api/orders/{order_id}")).json()["items"][0][
                    "name"
                ],
                blazer["name"],
            )
            current = (
                await client.get(f"/api/catalog/products/{blazer['slug']}")
            ).json()
            self.assertEqual(current["variants"][0]["stock"], variant["stock"] - 1)

            changed = await client.put(
                "/api/account/password",
                headers=headers,
                json={
                    "current_password": "StrongPass123",
                    "new_password": "NewStrongPass123",
                },
            )
            self.assertEqual(changed.status_code, 204, changed.text)
            self.assertEqual((await client.get("/api/account")).status_code, 401)
            self.assertEqual(
                (
                    await client.post(
                        "/api/auth/login",
                        headers=headers,
                        json={
                            "email": "shopper@example.com",
                            "password": "NewStrongPass123",
                        },
                    )
                ).status_code,
                200,
            )
            self.assertEqual(
                (await client.post("/api/auth/logout", headers=headers)).status_code,
                204,
            )
            self.assertEqual((await client.get("/api/account")).status_code, 401)
            self.assertIsNone(
                (await client.post("/api/auth/session", headers=headers)).json()
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/auth/login",
                        headers=headers,
                        json={
                            "email": "shopper@example.com",
                            "password": "NewStrongPass123",
                        },
                    )
                ).status_code,
                200,
            )
            self.assertEqual(
                (await client.delete("/api/account", headers=headers)).status_code, 204
            )
            self.assertEqual(
                (
                    await client.post(
                        "/api/auth/login",
                        headers=headers,
                        json={
                            "email": "shopper@example.com",
                            "password": "NewStrongPass123",
                        },
                    )
                ).status_code,
                403,
            )


if __name__ == "__main__":
    unittest.main()
