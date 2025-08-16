import math
from fastapi import APIRouter, Request, Depends, HTTPException, Query # Removed Form, Header
from fastapi.responses import HTMLResponse, JSONResponse # Removed RedirectResponse
# from fastapi.templating import Jinja2Templates # templates object used directly
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, or_
from typing import Optional, Type, Any
from pydantic import BaseModel

from app.templates import templates
from app.database.session import get_db # Provides AsyncSession
from app.models import Product, User, Brand, Category, Promt # ProductImage not used here
from app.api.auth.dependencies import get_current_user # Assumed async compatible
from app.utils.permissions import check_object_permission # Assumed sync, CPU-bound
from app.utils.security import csrf_protect, template_with_csrf # ensure_csrf_token not used
from app.utils.query_params import extract_dashboard_filters, extract_dashboard_return_params_clean, apply_filters, apply_sorting, paginate # Assumed sync, CPU-bound
# from app.utils.converters import to_int_or_none # Not directly used, standard int conversion


router = APIRouter()
 

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    # These query params are extracted by extract_dashboard_filters or directly from request.query_params
    # name: str = Query('', alias="name"),
    # ean: str = Query('', alias="ean"),
    # upc: str = Query('', alias="upc"),
    # brand: str = Query('', alias="brand"), # This was likely meant to be brand_id
    # category: str = Query('', alias="category") # This was likely meant to be category_id
    # promt: str = Query('', alias="promt") # This was likely meant to be promt_id
):
    filters = extract_dashboard_filters(request) # Contains name, ean, upc, brand_id, category_id, promt_id

    # Base query for products
    product_stmt = select(Product).options(
        selectinload(Product.images), # Eager load images to find main_image efficiently
        selectinload(Product.brand),   # Eager load brand
        selectinload(Product.category), # Eager load category
        selectinload(Product.promt) # Eager load promt
    )
    if not user.is_superuser:
        product_stmt = product_stmt.filter(Product.user_id == user.id)

    # Apply filters from query_params (filters object from extract_dashboard_filters)
    if filters.get("name"):
        product_stmt = product_stmt.filter(Product.name.ilike(f"%{filters['name']}%"))
    if filters.get("ean"):
        product_stmt = product_stmt.filter(Product.ean.ilike(f"%{filters['ean']}%"))
    if filters.get("upc"):
        product_stmt = product_stmt.filter(Product.upc.ilike(f"%{filters['upc']}%"))
    
    brand_id_str = filters.get("brand_id")
    if brand_id_str:
        if brand_id_str == "null":
            product_stmt = product_stmt.filter(Product.brand_id == None)
        else:
            try:
                product_stmt = product_stmt.filter(Product.brand_id == int(brand_id_str))
            except ValueError:
                pass # Or raise HTTPException for invalid brand_id format

    category_id_str = filters.get("category_id")
    if category_id_str:
        if category_id_str == "null":
            product_stmt = product_stmt.filter(Product.category_id == None)
        else:
            try:
                product_stmt = product_stmt.filter(Product.category_id == int(category_id_str))
            except ValueError:
                pass # Or raise HTTPException for invalid category_id format

    promt_id_str = filters.get("promt_id")
    if promt_id_str:
        if promt_id_str == "null":
            product_stmt = product_stmt.filter(Product.promt_id == None)
        else:
            try:
                product_stmt = product_stmt.filter(Product.promt_id == int(promt_id_str))
            except ValueError:
                pass # Or raise HTTPException for invalid promt_id format

    # Count total products with filters
    count_stmt = select(func.count()).select_from(product_stmt.subquery())
    total_products_result = await db.execute(count_stmt)
    total_products = total_products_result.scalar_one()

    # Get paginated products
    paginated_stmt = product_stmt.order_by(Product.id.asc()).offset((page - 1) * limit).limit(limit)
    products_result = await db.execute(paginated_stmt)
    products_list = products_result.scalars().all()

    # Set main_image_filename (can be done in Pydantic model or template too)
    for p in products_list:
        main_image = next((img for img in p.images if img.is_main), None)
        p.main_image_filename = main_image.image_path if main_image else None
    
    total_pages = math.ceil(total_products / limit) if total_products > 0 else 1

    # Fetch brands and categories for filters (independent of product query)
    brands_result = await db.execute(select(Brand).order_by(Brand.name))
    brands_list = brands_result.scalars().all()
    categories_result = await db.execute(select(Category).order_by(Category.name))
    categories_list = categories_result.scalars().all()
    promts_result = await db.execute(select(Promt).order_by(Promt.name))
    promts_list = promts_result.scalars().all()

    # Получаем параметры для возврата без дефолтных значений
    return_params = await extract_dashboard_return_params_clean(request)

    # Формируем строку параметров для ссылки
    return_params_str = ""
    if return_params:
        param_pairs = [f"{k}={v}" for k, v in return_params.items()]
        return_params_str = "?" + "&".join(param_pairs)

    context = {
        "request": request,
        **filters, # Spread the filters dictionary into the context
        "user": user,
        "products": products_list,
        "brands": brands_list,
        "categories": categories_list,
        "promts": promts_list,
        "items": products_list, # Исправлено: передаем products_list вместо литерала
        "total": total_products,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "active_menu": 'dashboard',
        "return_params": return_params,
        "return_params_str": return_params_str
    }
    return template_with_csrf(request, templates, "dashboard.html", context)


@router.get("/dashboard/data", response_class=JSONResponse, name="dashboard_data")
async def dashboard_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, alias="name"),
    ean: Optional[str] = Query(None, alias="ean"),
    upc: Optional[str] = Query(None, alias="upc"),
    brand_id: Optional[str] = Query(None, alias="brand_id"),
    category_id: Optional[str] = Query(None, alias="category_id"),
    promt_id: Optional[str] = Query(None, alias="promt_id"),
    sort_by: str = Query("id", alias="sort_by"),
    sort_dir: str = Query("asc", alias="sort_dir"),
):
    allowed_fields = {
        "id": int,
        "name": str,
        "ean": str,
        "upc": str,
        "brand_id": int,
        "category_id": int,
        "promt_id": int,
    }
    filters = {
        "name": name,
        "ean": ean,
        "upc": upc,
    }
    # Обработка фильтрации по null для brand/category/promt
    if brand_id is not None:
        if brand_id == "null":
            filters["brand_id"] = None
        else:
            filters["brand_id"] = brand_id
    if category_id is not None:
        if category_id == "null":
            filters["category_id"] = None
        else:
            filters["category_id"] = category_id
    if promt_id is not None:
        if promt_id == "null":
            filters["promt_id"] = None
        else:
            filters["promt_id"] = promt_id

    query = select(Product)
    if not user.is_superuser:
        query = query.filter(Product.user_id == user.id)
    query = apply_filters(query, Product, filters, allowed_fields)

    # Сортировка по связанным моделям (brand/category)
    join_map = {"brand": Brand, "category": Category}
    if sort_by in join_map:
        query = query.outerjoin(getattr(Product, sort_by))
        allowed_fields[sort_by] = str
        # Для сортировки по имени бренда/категории
        def brand_sort(q, col, val):
            return q.order_by(getattr(join_map[sort_by], "name").desc() if sort_dir == "desc" else getattr(join_map[sort_by], "name").asc())
        query = brand_sort(query, None, None)
    else:
        query = apply_sorting(query, Product, sort_by, sort_dir, allowed_fields)

    # Eager load relationships needed for to_dict()
    query = query.options(
        selectinload(Product.brand),
        selectinload(Product.category),
        selectinload(Product.promt),
        selectinload(Product.images)
    )

    # Подсчет total до пагинации
    count_stmt = select(func.count()).select_from(query.subquery())
    total_products_result = await db.execute(count_stmt)
    total_products = total_products_result.scalar_one()
    total_pages = math.ceil(total_products / limit) if total_products > 0 else 1

    # Пагинация
    query = paginate(query, page, limit)
    products_result = await db.execute(query)
    products_list = products_result.scalars().all()

    return {
        "items": [p.to_dict() for p in products_list],
        "total": total_products,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "sort_dir": sort_dir
    }


#  directory
directory_map: dict[str, Type[Brand | Category | Promt]] = { # Type hint for clarity
    "brand": Brand,
    "category": Category,
    "promt": Promt,
}

# DirectoryInput and related routes (new, update, delete for /directory/*) are now obsolete
# as directory.js calls /api/v1/* endpoints.
# The GET route for /directory/{directory_name} (directory_page) is kept as it serves the main HTML page.

@router.get("/directory/{directory_name}", response_class=HTMLResponse, name="directory_page")
async def directory_page(
    request: Request,
    directory_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        raise HTTPException(status_code=404, detail="Справочник не найден")

    stmt = select(model_class)

    # Eager load user relationship if model_class has 'user' attribute
    # All Brand, Category, Promt models have a 'user' relationship.
    stmt = stmt.options(selectinload(model_class.user))

    # Filter by user_id if applicable (all these models have user_id)
    if not user.is_superuser: # Superuser sees all
        stmt = stmt.filter(model_class.user_id == user.id)

    # Determine order_by attribute (all these models have name)
    order_by_attr = model_class.name
    stmt = stmt.order_by(order_by_attr)

    result = await db.execute(stmt)
    items = result.scalars().all()

    context = {
        "request": request,
        "user": user, # user is already passed to Depends, available in template context
        "dict_items": items,
        "dict_type": directory_name, # This is same as directory_name, maybe redundant
        "directory_name": directory_name,
        "active_menu": directory_name
    }
    return template_with_csrf(request, templates, "directory.html", context)

# The following routes are now obsolete as directory.js has been updated to use
# the /api/v1/* endpoints for CRUD operations on directory items.
# - GET /directory/{directory_name}/new (create_directory_page)
# - POST /directory/{directory_name}/new (create_directory)
# - GET /directory/{directory_name}/update/{item_id} (update_directory_item_form)
# - POST /directory/{directory_name}/update/{item_id} (update_directory_item_action)
# - DELETE /directory/{directory_name}/delete/{item_id} (delete_directory_item_action)
# The associated Pydantic model `DirectoryInput` is also no longer needed here.
@router.get("/directory/{directory_name}/data", response_class=JSONResponse, name="directory_data")
async def directory_data(
    request: Request,
    directory_name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("id", alias="sort_by"),
    sort_dir: str = Query("asc", alias="sort_dir"),
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        raise HTTPException(status_code=404, detail="Справочник не найден")

    # Define allowed fields for filtering and sorting for this model
    allowed_fields = {
        "id": int,
        "name": str,
        "description": str,
        # Add other common fields if necessary
    }

    # Extract filters from request
    # This is a simplified example; you might need a more robust way to get filters
    filters = {}
    query_params = request.query_params
    for field in allowed_fields.keys():
        if field in query_params:
            filters[field] = query_params[field]

    # Base query
    query = select(model_class)
    if not user.is_superuser:
        query = query.filter(model_class.user_id == user.id)

    # Apply filters
    query = apply_filters(query, model_class, filters, allowed_fields)

    # Apply sorting
    query = apply_sorting(query, model_class, sort_by, sort_dir, allowed_fields)

    # Count total items
    count_stmt = select(func.count()).select_from(query.subquery())
    total_items_result = await db.execute(count_stmt)
    total_items = total_items_result.scalar_one()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1

    # Apply pagination
    query = paginate(query, page, limit)

    # Eager load user if the model has a 'user' relationship
    if hasattr(model_class, 'user'):
        query = query.options(selectinload(model_class.user))

    items_result = await db.execute(query)
    items_list = items_result.scalars().all()

    # Convert to a list of dicts. Make sure your models have a to_dict() method.
    items_as_dicts = [item.to_dict(include_user=True) for item in items_list]

    return {
        "items": items_as_dicts,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }
