import io
import csv
import json
import openpyxl
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool # Import run_in_threadpool
from pydantic import ValidationError
from typing import Dict, List, Any, Optional # Added for type hints

from app.schemas.review import preprocess_review_row, ReviewUploadIn

def prettify_pydantic_error(err: Dict[str, Any], raw_row: Dict[str, Any], row_number: int) -> str:
    loc = ".".join([str(x) for x in err.get("loc", [])])
    msg = err.get("msg", "")
    val_input = err.get("input", None) # Changed 'val' to 'val_input' to avoid conflict
    return (f"Строка #{row_number}: поле '{loc}' — {msg}. В файле: «{val_input}». "
            f"Исходные данные: {raw_row}")

def clean_dict_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k).strip(): v for k, v in d.items()}

def process_review_row(r: Dict[str, Any], idx: int, errors: List[str]) -> Optional[Dict[str, Any]]:
    r = clean_dict_keys(r)
    norm_row = preprocess_review_row(r) # Assuming this returns a dict
    # Check if all relevant values are None
    if all(norm_row.get(k) is None for k in ["source", "text", "advantages", "disadvantages", "rating", "max_rating", "raw_rating"]):
        errors.append(f"Строка #{idx+1}: не содержит значимых данных, не загружена. Данные: {r}")
        return None
    try:
        review_in = ReviewUploadIn(**norm_row)
        return review_in.model_dump()
    except ValidationError as ve:
        for err_detail in ve.errors(): # Renamed 'err' to 'err_detail'
            errors.append(prettify_pydantic_error(err_detail, r, idx+1))
    except Exception as e:
        errors.append(f"Строка #{idx+1}: Непредвиденная ошибка: {e} — данные: {r}")
    return None

def process_reviews_list(items: List[Dict[str, Any]], errors: List[str]) -> List[Dict[str, Any]]:
    reviews = []
    for idx, r_item in enumerate(items): # Renamed 'r' to 'r_item'
        row = process_review_row(r_item, idx, errors)
        if row:
            reviews.append(row)
    return reviews

def _parse_and_process_content_sync(content_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Synchronous helper to handle parsing and processing."""
    ext = filename.lower().split(".")[-1]
    errors: List[str] = []
    total_rows = 0
    empty_rows = 0
    reviews: List[Dict[str, Any]] = []

    try:
        if ext == "json":
            items = json.loads(content_bytes.decode())
            total_rows = len(items)
            reviews = process_reviews_list(items, errors)
        elif ext == "csv":
            reader = csv.DictReader(io.StringIO(content_bytes.decode()))
            items = list(reader)
            total_rows = len(items)
            reviews = process_reviews_list(items, errors)
        elif ext == "xlsx":
            wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
            ws = wb.active
            if not ws: # Check if worksheet exists
                 errors.append("В файле XLSX не найден активный лист.")
                 raise ValueError("Активный лист не найден в XLSX")

            rows_iter = ws.iter_rows(values_only=True)
            try:
                first_row = next(rows_iter) # Get header row
            except StopIteration:
                first_row = None

            if not first_row or not any(first_row):
                errors.append("В файле не найдено заголовков (первая строка пуста).")
                raise ValueError("Заголовки не найдены")

            headers = [str(h or '').strip() for h in first_row]
            items = [dict(zip(headers, row_data)) for row_data in rows_iter] # Renamed 'row' to 'row_data'
            total_rows = len(items)
            reviews = process_reviews_list(items, errors)
        else:
            errors.append("Формат файла должен быть .json, .csv или .xlsx")
            # No need to return here, let it fall through to the main return

    except Exception as e: # Catch parsing specific errors
        errors.append(f"Ошибка парсинга {ext.upper()}: {e}")
        # For parsing errors, we might want to return immediately or let the outer try-except handle it.
        # For now, let it return with empty reviews and the error.
        # The caller function will then format the final error response.

    empty_rows = sum(1 for e_msg in errors if "пуст" in e_msg or "не содержит" in e_msg) # Renamed 'e' to 'e_msg'
    return {
        "success_count": len(reviews),
        "total_rows": total_rows,
        "empty_rows": empty_rows,
        "errors": errors,
        "reviews": reviews
    }

async def parse_reviews_file_to_list(file: UploadFile) -> Dict[str, Any]:
    content_bytes = await file.read() # Read file async
    filename = file.filename if file.filename else ""

    try:
        # Run the synchronous parsing logic in a thread pool
        result = await run_in_threadpool(_parse_and_process_content_sync, content_bytes, filename)

        # Check if parsing itself failed critically within the sync function
        if not result.get("reviews") and result.get("errors") and "Формат файла должен быть" in result["errors"][0]:
             return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": result["errors"], "reviews": []}
        if not result.get("reviews") and result.get("errors") and any("Ошибка парсинга" in e for e in result["errors"]):
            return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": result["errors"], "reviews": []}


        return result

    except Exception as e:
        # This catches errors from run_in_threadpool or other unexpected errors
        import traceback
        error_message = f"Ошибка сервера при обработке файла: {e}"
        print(traceback.format_exc())
        return {"success_count": 0, "total_rows": 0, "empty_rows": 0, "errors": [error_message], "reviews": []}
