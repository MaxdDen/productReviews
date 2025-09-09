import os

# --- Payload generators ---
def user_payload(username=None, password=None):
    return {
        "username": username or ("user_" + os.urandom(8).hex()),
        "password": password or "StrongPass123"
    }

def product_payload(name="Test Product", description="desc", ean="1234567890123", upc="123456789012"):
    return {"name": name, "description": description, "ean": ean, "upc": upc}

def product_payload_edge_cases():
    return [
        {},  # пустой
        {"name": "", "description": "", "ean": "", "upc": ""},
        {"name": "A"*256, "description": "desc", "ean": "bad_ean", "upc": "bad_upc"},
        {"name": None, "description": None, "ean": None, "upc": None},
        {"name": "Test Product", "description": "desc", "ean": "123", "upc": "456"},
    ]

def brand_payload(name="Test Brand"):
    return {"name": name}

def brand_payload_edge_cases():
    return [
        {},
        {"name": ""},
        {"name": "A"*256},
        {"name": None},
    ]

def category_payload(name="Test Category"):
    return {"name": name}

def category_payload_edge_cases():
    return [
        {},
        {"name": ""},
        {"name": "A"*256},
        {"name": None},
    ]

def promt_payload(text="Test Prompt"):
    return {"text": text}

def promt_payload_edge_cases():
    return [
        {},
        {"text": ""},
        {"text": "A"*1024},
        {"text": None},
    ]

def review_payload(text="Test Review", rating=5):
    return {"text": text, "rating": rating}

def review_payload_edge_cases():
    return [
        {},
        {"text": "", "rating": 0},
        {"text": "A"*1024, "rating": 11},
        {"text": None, "rating": None},
        {"text": "Test Review", "rating": -1},
    ]

# --- DSL actions (как ранее) ---
async def given_registered_user(client, username, password):
    await client.post("/register", json={"username": username, "password": password})
    resp = await client.post("/login", data={"username": username, "password": password, "next_url": "/dashboard"})
    client.cookies = resp.cookies
    return client

async def when_create_product(client, **kwargs):
    return await client.post("/product/save", data=kwargs)

async def when_update_product(client, product_id, **kwargs):
    data = {"product_id": product_id, **kwargs}
    return await client.post("/product/save", data=data)

async def when_delete_product(client, product_id):
    return await client.delete(f"/product/{product_id}/delete")

async def then_product_exists(client, product_id):
    resp = await client.get(f"/product/{product_id}")
    assert resp.status_code == 200
    return resp.json()

async def when_create_brand(client, **kwargs):
    return await client.post("/brand/save", data=kwargs)

async def when_update_brand(client, brand_id, **kwargs):
    data = {"brand_id": brand_id, **kwargs}
    return await client.post("/brand/save", data=data)

async def when_delete_brand(client, brand_id):
    return await client.delete(f"/brand/{brand_id}/delete")

async def then_brand_exists(client, brand_id):
    resp = await client.get(f"/brand/{brand_id}")
    assert resp.status_code == 200
    return resp.json()

async def when_create_category(client, **kwargs):
    return await client.post("/category/save", data=kwargs)

async def when_update_category(client, category_id, **kwargs):
    data = {"category_id": category_id, **kwargs}
    return await client.post("/category/save", data=data)

async def when_delete_category(client, category_id):
    return await client.delete(f"/category/{category_id}/delete")

async def then_category_exists(client, category_id):
    resp = await client.get(f"/category/{category_id}")
    assert resp.status_code == 200
    return resp.json()

async def when_create_prompt(client, **kwargs):
    return await client.post("/promt/save", data=kwargs)

async def when_update_prompt(client, promt_id, **kwargs):
    data = {"promt_id": promt_id, **kwargs}
    return await client.post("/promt/save", data=data)

async def when_delete_prompt(client, promt_id):
    return await client.delete(f"/promt/{promt_id}/delete")

async def then_prompt_exists(client, promt_id):
    resp = await client.get(f"/promt/{promt_id}")
    assert resp.status_code == 200
    return resp.json()

async def when_create_review(client, **kwargs):
    return await client.post("/review/save", data=kwargs)

async def when_update_review(client, review_id, **kwargs):
    data = {"review_id": review_id, **kwargs}
    return await client.post("/review/save", data=data)

async def when_delete_review(client, review_id):
    return await client.delete(f"/review/{review_id}/delete")

async def then_review_exists(client, review_id):
    resp = await client.get(f"/review/{review_id}")
    assert resp.status_code == 200
    return resp.json() 