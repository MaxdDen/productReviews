# app/schemas/review.py

import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

# ======= Функции безопасного преобразования =======

def safe_int(val):
    """
    Преобразует значение к int, если возможно. 
    Если значение пустое или не конвертируется — возвращает None.
    """
    if val in (None, ""):
        return None
    try:
        return int(val)
    except Exception:
        return None

def safe_float(val):
    """
    Преобразует значение к float, если возможно. 
    Если значение пустое или не конвертируется — возвращает None.
    """
    if val in (None, ""):
        return None
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return None

def parse_rating(raw_rating: Optional[str]):
    """
    Парсит строку формата '4.7/5' или '4,7 из 5' или просто '4.5' в числа (rating, max_rating).
    """
    if not raw_rating or not str(raw_rating).strip():
        return None, None
    raw = str(raw_rating).replace(",", ".").strip()
    match = re.match(r"^\s*(\d+(\.\d+)?)\s*(/|из)\s*(\d+(\.\d+)?)(.*)?$", raw, re.I)
    if match:
        return float(match.group(1)), float(match.group(4))
    match = re.match(r"^\s*(\d+(\.\d+)?)(.*)?$", raw)
    if match:
        return float(match.group(1)), None
    return None, None

def preprocess_review_row(row: dict) -> dict:
    """
    Нормализует входной словарь:
    - Приводит типы
    - Парсит raw_rating, если надо
    - Считает normalized_rating
    - Всегда возвращает словарь с полным набором ключей для схемы
    """
    res = {
        "importance": safe_int(row.get("importance")),
        "source": (row.get("source") or None),
        "text": (row.get("text") or None),
        "advantages": (row.get("advantages") or None),
        "disadvantages": (row.get("disadvantages") or None),
        "raw_rating": (row.get("raw_rating") or None),
        "rating": safe_float(row.get("rating")),
        "max_rating": safe_float(row.get("max_rating")),
        "normalized_rating": 0,
    }
    # Парсим raw_rating если rating/max_rating не заданы
    if res["raw_rating"]:
        if (res["rating"] is None and res["max_rating"] is None):
            r, m = parse_rating(res["raw_rating"])
            res["rating"], res["max_rating"] = r, m
    else:
        # Если не заполнен raw_rating, но заполнены rating и/или max_rating
        if res["rating"] or res["max_rating"]:
            res["raw_rating"] = str(res["rating"] if res["rating"] is not None else 0) + "/" + str(res["max_rating"] if res["max_rating"] is not None else 0)

    # Считаем normalized_rating
    if (isinstance(res["rating"], (int, float)) and
        isinstance(res["max_rating"], (int, float)) and res["max_rating"] > 0):
        res["normalized_rating"] = round(res["rating"] / res["max_rating"] * 100)
    else:
        res["normalized_rating"] = 0

    return res

# ======= Pydantic-схема =======

class ReviewUploadIn(BaseModel):
    importance: Optional[int] = Field(default=None, ge=1)
    source: Optional[str] = Field(default=None, max_length=100)
    text: Optional[str] = Field(default=None)
    advantages: Optional[str] = Field(default=None)
    disadvantages: Optional[str] = Field(default=None)
    raw_rating: Optional[str] = Field(default=None)
    rating: Optional[float] = Field(default=None, ge=0)
    max_rating: Optional[float] = Field(default=None, ge=0)
    normalized_rating: Optional[int] = Field(default=None, ge=0, le=100)

    @field_validator("normalized_rating")
    def check_normalized_rating(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("normalized_rating должен быть от 0 до 100")
        return v
