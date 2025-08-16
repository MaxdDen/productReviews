import os
from typing import List
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.utils.barcode import extract_barcodes
from app.utils.ocr import ocr_image_to_text
#from app.utils.openai_vision import analyze_with_vision
from app.models.product import Product
from app.schemas.product import ProductIdentifyResponse

async def identify_from_images(images: List[UploadFile], db: Session, save_to_product: bool):
    results = {
        "ean": None,
        "upc": None,
        "barcode": None,
        "serial_number": None,
        "name": None,
        "product_link": None,
        "stores": []
    }

    # TODO: сохранить изображения во временную папку
    temp_files = []
    for img in images:
        content = await img.read()
        path = f"/tmp/{img.filename}"
        with open(path, "wb") as f:
            f.write(content)
        temp_files.append(path)

    # 1. Попытка чтения штрихкодов
    for file in temp_files:
        codes = extract_barcodes(file)
        if codes:
            for code in codes:
                if len(code) in [12, 13]:
                    results["ean"] = code
                    results["barcode"] = code
                    break

    # 2. Попытка чтения текста с фото (OCR)
    for file in temp_files:
        text = ocr_image_to_text(file)
        # TODO: извлечение серийного номера, имени, возможно по шаблонам
        if not results["name"]:
            results["name"] = try_extract_name(text)
        if not results["serial_number"]:
            results["serial_number"] = try_extract_serial(text)

    # 3. Поиск товара в базе (упрощённо)
    product = None
    if results["ean"]:
        product = db.query(Product).filter(Product.ean == results["ean"]).first()
    elif results["name"]:
        product = db.query(Product).filter(Product.name.ilike(f"%{results['name']}%")).first()

    if product:
        results["product_link"] = f"/product/{product.id}"
        # можно расширить на поиск производителя, бренда и пр.
    else:
        # 4. OpenAI Vision fallback
        vision_result = analyze_with_vision(temp_files[0])
        results["name"] = results["name"] or vision_result.get("name")
        results["product_link"] = vision_result.get("product_link")

    # 5. Подбор магазинов (будет дополняться позже)
    results["stores"] = get_mock_stores()

    # 6. Очистка временных файлов
    for f in temp_files:
        os.remove(f)

    return results

def try_extract_name(text: str) -> str:
    # Примитивно: первая строка, самая большая по длине
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return max(lines, key=len) if lines else None

def try_extract_serial(text: str) -> str:
    for line in text.split('\n'):
        if "S/N" in line or "Serial" in line:
            return line.split(":")[-1].strip()
    return None

def get_mock_stores():
    return [
        {"name": "Rozetka", "url": "https://rozetka.com.ua"},
        {"name": "Amazon", "url": "https://amazon.com"},
        {"name": "Walmart", "url": "https://walmart.com"},
    ]
