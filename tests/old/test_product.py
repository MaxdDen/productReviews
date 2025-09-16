import pytest
import os
import sys


@pytest.mark.anyio
async def test_create_product_successful(test_client_without_csrf):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    payload = {"name": "Test Product", "description": "desc", "ean": "1234567890123", "upc": "123456789012"}
    response = await test_client_without_csrf.post("/product/save", data=payload)
    assert response.status_code == 200

def teardown_module(module):
    sys.exit(0)