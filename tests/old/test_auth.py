import pytest

@pytest.mark.anyio
async def test_register_success(client_without_csrf):
    payload = {"username": "user3", "password": "StrongPass123"}
    response = await client_without_csrf.post("/register", json=payload)
    assert response.status_code in (200, 201)
    assert response.json()["next"] == "/login"

@pytest.mark.anyio
async def test_register_duplicate_username(client_without_csrf):
    payload = {"username": "user4", "password": "StrongPass123"}
    await client_without_csrf.post("/register", json=payload)
    response = await client_without_csrf.post("/register", json=payload)
    assert response.status_code == 400
    assert "уже существует" in response.text.lower()

@pytest.mark.anyio
@pytest.mark.parametrize("payload,expected_status", [
    ({"username": "", "password": "123"}, 400),
    ({"username": "user5", "password": ""}, 400),
    ({}, 422),
])
async def test_register_invalid_data(client_without_csrf, payload, expected_status):
    response = await client_without_csrf.post("/register", json=payload)
    assert response.status_code == expected_status

@pytest.mark.anyio
async def test_login_success(client_without_csrf):
    username = "user6"
    password = "StrongPass123"
    await client_without_csrf.post("/register", json={"username": username, "password": password})
    data = {"username": username, "password": password, "next_url": "/dashboard"}
    response = await client_without_csrf.post("/login", data=data)
    assert response.status_code == 200
    assert response.json()["next"] == "/dashboard"
    # Проверяем, что установлена кука access_token
    assert "access_token" in response.cookies

@pytest.mark.anyio
async def test_login_wrong_password(client_without_csrf):
    username = "user7"
    password = "StrongPass123"
    await client_without_csrf.post("/register", json={"username": username, "password": password})
    data = {"username": username, "password": "WrongPass", "next_url": "/dashboard"}
    response = await client_without_csrf.post("/login", data=data)
    assert response.status_code == 401
    assert "неверные данные" in response.text.lower()

@pytest.mark.anyio
async def test_login_nonexistent_user(client_without_csrf):
    data = {"username": "nouser", "password": "any", "next_url": "/dashboard"}
    response = await client_without_csrf.post("/login", data=data)
    assert response.status_code == 401
    assert "неверные данные" in response.text.lower()

@pytest.mark.anyio
async def test_login_missing_fields(client_without_csrf):
    data = {"username": "", "password": ""}
    response = await client_without_csrf.post("/login", data=data)
    assert response.status_code == 400
    assert "обязательны" in response.text.lower()

@pytest.mark.anyio
async def test_logout(client_without_csrf):
    # Просто проверяем, что редирект и кука удаляется
    response = await client_without_csrf.get("/logout", follow_redirects=False)
    assert response.status_code in (302, 307)
    # Проверяем, что access_token удалён (Set-Cookie с Max-Age=0 или отсутствует)
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token" in set_cookie and ("max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower())
