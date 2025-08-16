from fastapi import Request
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.orm import Query
from sqlalchemy import or_, and_


allowed = {'sort_by', 'sort_dir', 'page', 'brand_id', 'category_id', 'promt_id', 'name', 'ean', 'upc', 'limit', 'highlight_id'}


def extract_dashboard_filters(request: Request):
    params = dict(request.query_params)
    for key in ['brand_id', 'category_id', 'promt_id', 'page', 'limit']:
        if key in params:
            if params[key] == 'null': # Specifically check for 'null' string for ID fields
                params[key] = 'null' # Keep it as string 'null' for backend logic to handle
            elif params[key] in (None, ''):
                params[key] = None
            else:
                try:
                    params[key] = int(params[key])
                except (ValueError, TypeError):
                    params[key] = None 
    return params

def extract_dashboard_return_params111(request: Request):
    """
    Возвращает параметры для возврата на главную с сохранением фильтров/сортировки.
    """
    params = dict(request.query_params)
    # Можно отфильтровать только те параметры, которые тебе нужны
    allowed111 = {'sort_by', 'sort_dir', 'page', 'brand_id', 'category_id', 'name', 'ean', 'upc', 'limit', 'highlight_id'}
    return {k: v for k, v in params.items() if k in allowed111}


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


def filter_non_default_params(params: dict) -> dict:
    """
    Фильтрует параметры, убирая дефолтные значения.
    Аналогично JavaScript функции getNonDefaultFiltersForUrl()
    """
    # Дефолтные значения (аналогично JavaScript)
    defaults = {
        'page': '1',
        'limit': '10',
        'sort_by': 'id',
        'sort_dir': 'asc',
        'name': '',
        'ean': '',
        'upc': '',
        'brand_id': '',
        'category_id': '',
        'promt_id': '',
        'highlight_id': ''
    }
    
    # Фильтруем только не-дефолтные значения
    non_default_params = {}
    for key, value in params.items():
        if key in defaults:
            default_value = defaults[key]
            # Добавляем параметр только если он отличается от дефолтного
            if value is not None and value != '' and str(value) != str(default_value):
                non_default_params[key] = value
        else:
            # Если параметр не в списке дефолтных, добавляем его
            if value is not None and value != '':
                non_default_params[key] = value
    return non_default_params


def extract_dashboard_return_params_sync(request: Request) -> dict:
    """
    Синхронная версия extract_dashboard_return_params
    """
    # Получаем только из query_params
    params = dict(request.query_params)
    result = {k: v for k, v in params.items() if k in allowed}
    return result


async def extract_dashboard_return_params_clean(request: Request) -> dict:
    """
    Возвращает параметры для возврата на главную с сохранением фильтров/сортировки,
    но без дефолтных значений (аналогично JavaScript getNonDefaultFiltersForUrl)
    """
    try:
        # Получаем все параметры (используем синхронную версию)
        all_params = extract_dashboard_return_params_sync(request)
        
        # Фильтруем дефолтные значения
        return filter_non_default_params(all_params)
    except Exception as e:
        print(f"Ошибка в extract_dashboard_return_params_clean: {e}")
        # Возвращаем пустой словарь в случае ошибки
        return {}


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


# Универсальный фильтр для SQLAlchemy

def apply_filters(query, model, filters: dict, allowed_fields: dict):
    """
    query: SQLAlchemy Query
    model: SQLAlchemy модель
    filters: dict с фильтрами (field: value)
    allowed_fields: dict field -> тип (str, int, list, callable)
    """
    for field, value in filters.items():
        if value is None or value == '':
            continue
        if field not in allowed_fields:
            continue
        col = getattr(model, field, None)
        if not col:
            continue
        field_type = allowed_fields[field]
        # Строковые поля — ilike
        if field_type is str:
            query = query.filter(col.ilike(f"%{value}%"))
        # Числовые поля — == или in_
        elif field_type is int:
            if isinstance(value, (list, tuple)):
                query = query.filter(col.in_(value))
            else:
                try:
                    query = query.filter(col == int(value))
                except Exception:
                    continue
        # Списки — in_
        elif field_type is list:
            if isinstance(value, str):
                value = [v.strip() for v in value.split(',') if v.strip()]
            query = query.filter(col.in_(value))
        # Кастомная функция
        elif callable(field_type):
            query = field_type(query, col, value)
    return query

# Универсальная сортировка

def apply_sorting(query, model, sort_by, sort_dir, allowed_fields: dict):
    """
    sort_by: поле или список полей (через запятую)
    sort_dir: asc/desc или список (через запятую)
    allowed_fields: dict field -> тип
    """
    if not sort_by:
        return query
    fields = [f.strip() for f in str(sort_by).split(',') if f.strip()]
    dirs = [d.strip() for d in str(sort_dir).split(',')] if sort_dir else ['asc'] * len(fields)
    for i, field in enumerate(fields):
        if field not in allowed_fields:
            continue
        col = getattr(model, field, None)
        if not col:
            continue
        direction = dirs[i] if i < len(dirs) else dirs[-1]
        if direction == 'desc':
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())
    return query

# Универсальная пагинация

def paginate(query, page: int, limit: int):
    if not page or page < 1:
        page = 1
    if not limit or limit < 1:
        limit = 10
    return query.offset((page - 1) * limit).limit(limit)

