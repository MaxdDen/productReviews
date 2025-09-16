import pytest
from tests.dsl import *

@pytest.mark.anyio
@pytest.mark.parametrize("payload", product_payload_edge_cases())
async def test_create_product_edge_cases(test_client_without_csrf, payload):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    client = await given_registered_user(test_client_without_csrf, username, password)
    resp = await when_create_product(client, **payload)
    # Ожидаем либо 200, либо 4xx в зависимости от валидации
    assert resp.status_code in (200, 400, 422)

@pytest.mark.anyio
@pytest.mark.parametrize("payload", brand_payload_edge_cases())
async def test_create_brand_edge_cases(test_client_without_csrf, payload):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    client = await given_registered_user(test_client_without_csrf, username, password)
    resp = await when_create_brand(client, **payload)
    assert resp.status_code in (200, 400, 422)

@pytest.mark.anyio
@pytest.mark.parametrize("payload", category_payload_edge_cases())
async def test_create_category_edge_cases(test_client_without_csrf, payload):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    client = await given_registered_user(test_client_without_csrf, username, password)
    resp = await when_create_category(client, **payload)
    assert resp.status_code in (200, 400, 422)

@pytest.mark.anyio
@pytest.mark.parametrize("payload", promt_payload_edge_cases())
async def test_create_prompt_edge_cases(test_client_without_csrf, payload):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    client = await given_registered_user(test_client_without_csrf, username, password)
    resp = await when_create_prompt(client, **payload)
    assert resp.status_code in (200, 400, 422)

@pytest.mark.anyio
@pytest.mark.parametrize("payload", review_payload_edge_cases())
async def test_create_review_edge_cases(test_client_without_csrf, payload):
    username = "user_" + os.urandom(8).hex()
    password = "StrongPass123"
    client = await given_registered_user(test_client_without_csrf, username, password)
    resp = await when_create_review(client, **payload)
    assert resp.status_code in (200, 400, 422) 