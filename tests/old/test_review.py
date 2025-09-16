import pytest
from httpx import AsyncClient
from typing import Dict, Any

from app.models import Review, Product, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

pytestmark = pytest.mark.asyncio

async def test_add_review_successful(user_1_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client: AsyncClient = user_1_auth_details["client"]
    db_session: AsyncSession = user_1_auth_details["db_session"]
    user: User = user_1_auth_details["user"]
    product_id = product_by_user_1.id
    review_data = review_payload_factory(text="A fantastic product, highly recommend!")

    dash_response = await client.get("/dashboard") # Get CSRF from a logged-in page
    csrf_token = dash_response.cookies.get("csrf_token")
    assert csrf_token

    # /review/{product_id}/add expects JSON payload and X-CSRFToken header
    response = await client.post(
        f"/review/{product_id}/add",
        json=review_data,
        headers={"X-CSRFToken": csrf_token}
    )
    assert response.status_code == 200, f"Add review failed: {response.text}"
    response_json = response.json()
    assert response_json["status"] == "ok"
    review_id = response_json["id"]

    review_db = await db_session.get(Review, review_id)
    assert review_db is not None
    assert review_db.text == review_data["text"]
    assert review_db.product_id == product_id
    assert review_db.user_id == user.id

async def test_add_review_to_non_existent_product(user_1_auth_details: Dict[str, Any], review_payload_factory):
    client: AsyncClient = user_1_auth_details["client"]
    review_data = review_payload_factory()
    non_existent_product_id = 999999

    dash_response = await client.get("/dashboard")
    csrf_token = dash_response.cookies.get("csrf_token")
    assert csrf_token

    response = await client.post(
        f"/review/{non_existent_product_id}/add",
        json=review_data,
        headers={"X-CSRFToken": csrf_token}
    )
    assert response.status_code == 404 # Product not found check in the route
    assert f"Product with id {non_existent_product_id} not found" in response.json()["detail"]

async def test_add_review_unauthenticated(test_client: AsyncClient, product_by_user_1: Product, review_payload_factory):
    review_data = review_payload_factory()
    response = await test_client.post(f"/review/{product_by_user_1.id}/add", json=review_data) # No auth, no CSRF
    assert response.status_code == 302 # AuthMiddleware redirects
    assert "/login" in response.headers["location"]

async def test_update_review_successful(user_1_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client: AsyncClient = user_1_auth_details["client"]
    db_session: AsyncSession = user_1_auth_details["db_session"]

    # Create a review first
    dash_response_add = await client.get("/dashboard")
    csrf_add = dash_response_add.cookies.get("csrf_token")
    assert csrf_add
    initial_review_data = review_payload_factory(text="Initial review.")
    add_response = await client.post(
        f"/review/{product_by_user_1.id}/add", json=initial_review_data, headers={"X-CSRFToken": csrf_add}
    )
    assert add_response.status_code == 200
    review_id = add_response.json()["id"]

    # Update the review
    updated_text = "This review has been updated."
    update_payload = {"text": updated_text, "rating": 4.0}
    dash_response_update = await client.get("/dashboard") # Fresh CSRF
    csrf_update = dash_response_update.cookies.get("csrf_token")
    assert csrf_update
    update_response = await client.put(
        f"/review/{review_id}/update", json=update_payload, headers={"X-CSRFToken": csrf_update}
    )
    assert update_response.status_code == 200, f"Update review failed: {update_response.text}"
    assert update_response.json()["id"] == review_id

    updated_review_db = await db_session.get(Review, review_id)
    assert updated_review_db is not None
    assert updated_review_db.text == updated_text
    assert updated_review_db.rating == 4.0

async def test_update_review_by_another_user(user_1_auth_details: Dict[str, Any], user_2_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client_user_1: AsyncClient = user_1_auth_details["client"]
    client_user_2: AsyncClient = user_2_auth_details["client"]

    # User 1 creates a review
    dash_csrf_u1 = (await client_user_1.get("/dashboard")).cookies.get("csrf_token")
    review_data_u1 = review_payload_factory(text="User 1's review")
    add_resp_u1 = await client_user_1.post(
        f"/review/{product_by_user_1.id}/add", json=review_data_u1, headers={"X-CSRFToken": dash_csrf_u1}
    )
    assert add_resp_u1.status_code == 200
    review_id_u1 = add_resp_u1.json()["id"]

    # User 2 attempts to update User 1's review
    dash_csrf_u2 = (await client_user_2.get("/dashboard")).cookies.get("csrf_token")
    update_payload_malicious = {"text": "Malicious update by User 2"}
    update_response_u2 = await client_user_2.put(
        f"/review/{review_id_u1}/update", json=update_payload_malicious, headers={"X-CSRFToken": dash_csrf_u2}
    )
    # update_review service raises generic Exception for perm issues, leading to 500
    assert update_response_u2.status_code == 500

async def test_delete_review_successful(user_1_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client: AsyncClient = user_1_auth_details["client"]
    db_session: AsyncSession = user_1_auth_details["db_session"]

    dash_csrf_add = (await client.get("/dashboard")).cookies.get("csrf_token")
    add_response = await client.post(
        f"/review/{product_by_user_1.id}/add", json=review_payload_factory(), headers={"X-CSRFToken": dash_csrf_add}
    )
    assert add_response.status_code == 200
    review_id = add_response.json()["id"]

    dash_csrf_del = (await client.get("/dashboard")).cookies.get("csrf_token")
    delete_response = await client.delete(f"/review/{review_id}/delete", headers={"X-CSRFToken": dash_csrf_del})
    assert delete_response.status_code == 200, f"Delete review failed: {delete_response.text}"
    assert delete_response.json()["deleted_id"] == review_id

    assert await db_session.get(Review, review_id) is None

async def test_delete_review_by_another_user(user_1_auth_details: Dict[str, Any], user_2_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client_user_1: AsyncClient = user_1_auth_details["client"]
    client_user_2: AsyncClient = user_2_auth_details["client"]

    dash_csrf_u1 = (await client_user_1.get("/dashboard")).cookies.get("csrf_token")
    add_resp_u1 = await client_user_1.post(
        f"/review/{product_by_user_1.id}/add", json=review_payload_factory(), headers={"X-CSRFToken": dash_csrf_u1}
    )
    assert add_resp_u1.status_code == 200
    review_id_u1 = add_resp_u1.json()["id"]

    dash_csrf_u2 = (await client_user_2.get("/dashboard")).cookies.get("csrf_token")
    delete_response_u2 = await client_user_2.delete(
        f"/review/{review_id_u1}/delete", headers={"X-CSRFToken": dash_csrf_u2}
    )
    assert delete_response_u2.status_code == 404 # Service returns False, route raises 404
    assert "Отзыв не найден или нет прав на удаление" in delete_response_u2.json()["detail"]

async def test_add_review_empty_text_allowed(user_1_auth_details: Dict[str, Any], product_by_user_1: Product, review_payload_factory):
    client: AsyncClient = user_1_auth_details["client"]
    db_session: AsyncSession = user_1_auth_details["db_session"]
    review_data = review_payload_factory(text=None, source="Review with no text")

    dash_csrf = (await client.get("/dashboard")).cookies.get("csrf_token")
    response = await client.post(
        f"/review/{product_by_user_1.id}/add", json=review_data, headers={"X-CSRFToken": dash_csrf}
    )
    assert response.status_code == 200
    review_id = response.json()["id"]
    review_db = await db_session.get(Review, review_id)
    assert review_db is not None
    assert review_db.text is None
    assert review_db.source == "Review with no text"
