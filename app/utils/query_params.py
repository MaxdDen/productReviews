from fastapi import Request
from pydantic import BaseModel
from typing import Optional


allowed = {'sort_by', 'sort_dir', 'page', 'brand_id', 'category_id', 'name', 'ean', 'upc', 'limit', 'highlight_id'}


def extract_dashboard_filters(request: Request):
    params = dict(request.query_params)
    for key in ['brand_id', 'category_id', 'page', 'limit']:
        if key in params:
            if params[key] in (None, '', 'null'):
                params[key] = None
            else:
                try:
                    params[key] = int(params[key])
                except (ValueError, TypeError):
                    params[key] = None 
    return params

async def extract_dashboard_return_params(request: Request) -> dict:
    # 1. Сначала пробуем забрать из query_params
    params = dict(request.query_params)
    result = {k: v for k, v in params.items() if k in allowed}

    # 2. Пробуем дополнить из form, если это POST/PUT с формой
    # (если используется FormData, например, через JS/fetch)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            form_data = await request.form()
            # Фильтруем только те поля, которые нужны (либо те, что начинаются с return_param_)
            for k in allowed:
                key = f"return_param_{k}"
                if key in form_data:
                    result[k] = form_data[key]
        except Exception:
            pass

    return result


def extract_analyze_filters(request: Request):
    params = dict(request.query_params)
    for key in ['page', 'limit']:
        if key in params:
            if params[key] in (None, '', 'null'):
                params[key] = None
            else:
                try:
                    params[key] = int(params[key])
                except (ValueError, TypeError):
                    params[key] = None
    return params

class AnalyzeFilters(BaseModel):
    promt_id: Optional[int] = 0
    importance: Optional[int] = 0
    source: Optional[str] = ""
    text: Optional[str] = ""
    advantages: Optional[str] = ""
    disadvantages: Optional[str] = ""
    normalized_rating_min: Optional[int] = 0
    normalized_rating_max: Optional[int] = 0

