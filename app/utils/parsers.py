import io
import csv
import json
import openpyxl
from fastapi import UploadFile
from pydantic import ValidationError

from app.schemas.review import preprocess_review_row, ReviewUploadIn

def prettify_pydantic_error(err, raw_row, row_number):
    loc = ".".join([str(x) for x in err.get("loc", [])])
    msg = err.get("msg", "")
    val = err.get("input", None)
    return (f"Строка #{row_number}: поле '{loc}' — {msg}. В файле: «{val}». "
            f"Исходные данные: {raw_row}")

def clean_dict_keys(d):
    return {str(k).strip(): v for k, v in d.items()}

def process_review_row(r: dict, idx: int, errors: list) -> dict|None:
    r = clean_dict_keys(r)
    norm_row = preprocess_review_row(r)
    if all(norm_row[k] is None for k in ["source", "text", "advantages", "disadvantages", "rating", "max_rating", "raw_rating"]):
        errors.append(f"Строка #{idx+1}: не содержит значимых данных, не загружена. Данные: {r}")
        return None
    try:
        review_in = ReviewUploadIn(**norm_row)
        return review_in.model_dump()
    except ValidationError as ve:
        for err in ve.errors():
            errors.append(prettify_pydantic_error(err, r, idx+1))
    except Exception as e:
        errors.append(f"Строка #{idx+1}: Непредвиденная ошибка: {e} — данные: {r}")
    return None

def process_reviews_list(items: list[dict], errors: list) -> list[dict]:
    reviews = []
    for idx, r in enumerate(items):
        row = process_review_row(r, idx, errors)
        if row:
            reviews.append(row)
    return reviews

async def parse_reviews_file_to_list(file: UploadFile):
    ext = file.filename.lower().split(".")[-1]
    content = await file.read()
    errors = []
    total_rows = 0
    empty_rows = 0
    reviews = []
    try:
        if ext == "json":
            try:
                items = json.loads(content.decode())
                total_rows = len(items)
                reviews = process_reviews_list(items, errors)
                empty_rows = sum(1 for e in errors if "пуст" in e or "не содержит" in e)
            except Exception as e:
                errors.append(f"Ошибка парсинга JSON: {e}")
                return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}

        elif ext == "csv":
            try:
                reader = csv.DictReader(io.StringIO(content.decode()))
                items = list(reader)
                total_rows = len(items)
                reviews = process_reviews_list(items, errors)
                empty_rows = sum(1 for e in errors if "пуст" in e or "не содержит" in e)
            except Exception as e:
                errors.append(f"Ошибка парсинга CSV: {e}")
                return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}

        elif ext == "xlsx":
            try:
                wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows or not any(rows[0]):
                    errors.append("В файле не найдено заголовков (первая строка пуста).")
                    return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}
                headers = [str(h or '').strip() for h in rows[0]]
                items = [dict(zip(headers, row)) for row in rows[1:]]
                total_rows = len(items)
                reviews = process_reviews_list(items, errors)
                empty_rows = sum(1 for e in errors if "пуст" in e or "не содержит" in e)
            except Exception as e:
                errors.append(f"Ошибка парсинга XLSX: {e}")
                return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}

        else:
            errors.append("Формат файла должен быть .json, .csv или .xlsx")
            return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}

        return {
            "success_count": len(reviews),
            "total_rows": total_rows,
            "empty_rows": empty_rows,
            "errors": errors,
            "reviews": reviews
        }

    except Exception as e:
        import traceback
        errors.append(f"Ошибка сервера: {e}")
        print(traceback.format_exc())
        return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": errors, "reviews": []}
