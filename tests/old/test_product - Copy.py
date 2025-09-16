import pytest
from httpx import AsyncClient
from typing import Dict, Any
import io
import os
from sqlalchemy.orm import selectinload

from app.models import Product, User, ProductImage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.product import ProductCreate, ProductUpdate
from app.database.crud import create_directory_item, get_directory_item, update_directory_item, delete_directory_item
import logging
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.anyio

def make_product_payload(name="Test Product", description="desc", ean="1234567890123", upc="123456789012"):
    return {"name": name, "description": description, "ean": ean, "upc": upc}

@pytest.mark.anyio
async def test_create_product_successful111(test_client_without_csrf):
    logger.info("Старт test_create_product_successful")
    username = "user_" + ''.join(os.urandom(4).hex() for _ in range(2))
    password = "StrongPass123"
    logger.info("Регистрируем пользователя %s", username)
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    logger.info("Логинимся")
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    payload = make_product_payload(name="Unique Test Product Alpha")
    logger.info("Отправляем POST /product/save с payload: %s", payload)
    response = await test_client_without_csrf.post("/product/save", data=payload)
    logger.info("Ответ от /product/save: %s", response.text)
    assert response.status_code == 200, f"Product creation failed: {response.text}"
    response_json = response.json()
    logger.info("Ответ JSON: %s", response_json)
    assert "product_id" in response_json
    logger.info("Тест успешно завершён")
    
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

@pytest.mark.anyio
async def test_create_product_missing_name(test_client_without_csrf):
    username = "user_" + ''.join(os.urandom(4).hex() for _ in range(2))
    password = "StrongPass123"
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    payload = make_product_payload()
    del payload["name"]
    response = await test_client_without_csrf.post("/product/save", data=payload)
    assert response.status_code == 422

@pytest.mark.anyio
async def test_create_product_unauthenticated(test_client_without_csrf):
    payload = make_product_payload()
    response = await test_client_without_csrf.post("/product/save", data=payload)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]

@pytest.mark.anyio
async def test_update_product_successful(test_client_without_csrf):
    username = "user_" + ''.join(os.urandom(4).hex() for _ in range(2))
    password = "StrongPass123"
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    # Создаём продукт через API
    payload = make_product_payload(name="ToUpdate")
    response = await test_client_without_csrf.post("/product/save", data=payload)
    assert response.status_code == 200
    product_id = response.json()["product_id"]
    updated_name = f"Updated Product Name {os.urandom(3).hex()}"
    update_payload = {"product_id": product_id, "name": updated_name, "description": "Updated desc.", "ean": payload["ean"], "upc": payload["upc"]}
    response = await test_client_without_csrf.post("/product/save", data=update_payload)
    assert response.status_code == 200, f"Product update failed: {response.text}"
    assert response.json()["product_id"] == product_id

@pytest.mark.anyio
async def test_update_product_by_another_user(test_client_without_csrf, test_db_session):
    username1 = "user1"; password1 = "pass1"
    await test_client_without_csrf.post("/register", json={"username": username1, "password": password1})
    resp1 = await test_client_without_csrf.post("/login", data={"username": username1, "password": password1, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp1.cookies
    db = test_db_session
    user1 = await db.scalar(select(User).where(User.username == username1))
    username2 = "user2"; password2 = "pass2"
    await test_client_without_csrf.post("/register", json={"username": username2, "password": password2})
    user2 = await db.scalar(select(User).where(User.username == username2))
    product_data = ProductCreate(name="OtherUserProduct", description="desc")
    product = await create_directory_item(db, product_data, Product, user=user2)
    await db.refresh(product)
    update_payload = {"product_id": product.id, "name": "Malicious Update"}
    response = await test_client_without_csrf.post("/product/save", data=update_payload)
    assert response.status_code in [403, 404]

@pytest.mark.anyio
async def test_delete_product_successful(test_client_without_csrf, async_test_user, test_db_session):
    username = async_test_user.username
    password = "StrongPass123"
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    db = test_db_session
    product_data = ProductCreate(name="ToDelete", description="desc")
    product = await create_directory_item(db, product_data, Product, user=async_test_user)
    await db.refresh(product)
    delete_url = f"/product/{product.id}/delete"
    response = await test_client_without_csrf.delete(delete_url)
    assert response.status_code == 200, f"Product delete failed: {response.text}"
    assert response.json() == {"success": True}
    deleted_product_db = await db.get(Product, product.id)
    assert deleted_product_db is None

@pytest.mark.anyio
async def test_delete_product_by_another_user(test_client_without_csrf, test_db_session):
    username1 = "user1"; password1 = "pass1"
    await test_client_without_csrf.post("/register", json={"username": username1, "password": password1})
    resp1 = await test_client_without_csrf.post("/login", data={"username": username1, "password": password1, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp1.cookies
    db = test_db_session
    user1 = await db.scalar(select(User).where(User.username == username1))
    username2 = "user2"; password2 = "pass2"
    await test_client_without_csrf.post("/register", json={"username": username2, "password": password2})
    user2 = await db.scalar(select(User).where(User.username == username2))
    product_data = ProductCreate(name="OtherUserProduct", description="desc")
    product = await create_directory_item(db, product_data, Product, user=user2)
    await db.refresh(product)
    delete_url = f"/product/{product.id}/delete"
    response = await test_client_without_csrf.delete(delete_url)
    assert response.status_code == 404
    assert "Товар не найден" in response.json()["detail"]

@pytest.mark.anyio
async def test_create_product_with_image_upload(test_client_without_csrf, async_test_user, test_db_session):
    username = async_test_user.username
    password = "StrongPass123"
    await test_client_without_csrf.post("/register", json={"username": username, "password": password})
    resp = await test_client_without_csrf.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    test_client_without_csrf.cookies = resp.cookies
    payload = make_product_payload(name="Product With Image")
    image_content = b"dummyimagecontent"
    files_payload = {"main_image": ("test_image.png", io.BytesIO(image_content), "image/png")}
    response = await test_client_without_csrf.post("/product/save", data=payload, files=files_payload)
    assert response.status_code == 200, f"Image upload product save response: {response.text}"
    response_json = response.json()
    product_id = response_json["product_id"]
    product_db_stmt = select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
    product_db = (await test_db_session.execute(product_db_stmt)).scalar_one_or_none()
    assert product_db is not None
    assert product_db.name == payload["name"]
    assert len(product_db.images) == 1
    product_image = product_db.images[0]
    assert product_image.is_main is True
    assert product_image.user_id == async_test_user.id
    assert product_image.image_path.endswith(".png")
    assert product_image.product_id == product_id

@pytest.mark.anyio
async def test_async_product_crud(test_db_session):
    db = test_db_session
    user = User(username="testuser_async", hashed_password="hashed", is_superuser=False)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    product_data = ProductCreate(name="Async Product", description="desc")
    product = await create_directory_item(db, product_data, Product, user=user)
    assert product.id is not None
    assert product.name == "Async Product"
    assert product.user_id == user.id
    fetched = await get_directory_item(db, product.id, Product, user=user)
    assert fetched is not None
    assert fetched.id == product.id
    update_data = ProductUpdate(description="updated desc")
    updated = await update_directory_item(db, product.id, update_data, Product, user=user)
    assert updated is not None
    assert updated.description == "updated desc"
    deleted = await delete_directory_item(db, product.id, Product, user=user)
    assert deleted is True
    should_be_none = await get_directory_item(db, product.id, Product, user=user)
    assert should_be_none is None
