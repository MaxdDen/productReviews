import math
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Header, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from pydantic import BaseModel

from app.templates import templates
from app.database import get_db
from app.models import Product, User, Brand, Category, Promt, ProductImage
from app.api.auth.utils import get_current_user
from app.utils.permissions import check_object_permission
from app.utils.security import ensure_csrf_token, csrf_protect, template_with_csrf
from app.utils.query_params import extract_dashboard_filters
from app.utils.converters import to_int_or_none


router = APIRouter()
 

@router.get("/dashboard", response_class=HTMLResponse, name="dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str = Query('', alias="name"),
    ean: str = Query('', alias="ean"),
    upc: str = Query('', alias="upc"),
    brand: str = Query('', alias="brand"),
    category: str = Query('', alias="category")
):
    filters = extract_dashboard_filters(request)

    query = db.query(Product)
    if not user.is_superuser:
        query = query.filter(Product.user_id == user.id)

    # Получаем справочники для фильтров: 
    brands = db.query(Brand).order_by(Brand.name).all()
    categories = db.query(Category).order_by(Category.name).all()
    
    name = request.query_params.get("name")
    brand_id = request.query_params.get("brand_id")
    category_id = request.query_params.get("category_id")

    # Сборка фильтра SQLAlchemy по полученным параметрам
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if ean:
        query = query.filter(Product.ean.ilike(f"%{ean}%"))
    if upc:
        query = query.filter(Product.upc.ilike(f"%{upc}%"))
    if brand_id:
        if brand_id == "null":
            query = query.filter(Product.brand_id == None)
        elif brand_id:
            query = query.filter(Product.brand_id == int(brand_id))
    if category_id:
        if category_id == "null":
            query = query.filter(Product.category_id == None)
        elif category_id:
            query = query.filter(Product.category_id == int(category_id))

    products = query.all()

    query = query.order_by(Product.id.asc())

    total_products = query.count()

    for product in products:
        main_image = next((img for img in product.images if img.is_main), None)
        product.main_image_filename = main_image.image_path if main_image else None
    
    # Пагинация
    products = query.offset((page - 1) * limit).limit(limit).all()
    total_pages = math.ceil(total_products / limit) if total_products > 0 else 1

    context = {
        "request": request,
        **filters,
        "user": user,
        "products": products,
        "brands": brands,
        "categories": categories,
        "items": [...],
        "total": total_products,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }
    return template_with_csrf(request, templates, "dashboard.html", context)

@router.get("/dashboard/data", response_class=JSONResponse, name="dashboard_data")
async def dashboard_data(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    name: str = Query('', alias="name"),
    ean: str = Query('', alias="ean"),
    upc: str = Query('', alias="upc"),
    brand_id: str = Query(None, alias="brand_id"),
    category_id: str = Query(None, alias="category_id"),
    sort_by: str = Query("id", alias="sort_by"),
    sort_dir: str = Query("asc", alias="sort_dir"),
):
    query = db.query(Product)
    if not user.is_superuser:
        query = query.filter(Product.user_id == user.id)
    
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if ean:
        query = query.filter(Product.ean.ilike(f"%{ean}%"))
    if upc:
        query = query.filter(Product.upc.ilike(f"%{upc}%"))
    if brand_id:
        if brand_id == "null":
            query = query.filter(Product.brand_id == None)
        elif brand_id:
            query = query.filter(Product.brand_id == int(brand_id))
    if category_id:
        if category_id == "null":
            query = query.filter(Product.category_id == None)
        elif category_id:
            query = query.filter(Product.category_id == int(category_id))

    total_products = query.count()
    total_pages = math.ceil(total_products / limit) if total_products > 0 else 1
                      
    sortable_fields = {
        "id": Product.id,
        "name": Product.name,
        "ean": Product.ean,
        "upc": Product.upc,
    }

    if sort_by == "brand":
        query = query.outerjoin(Product.brand)
        sort_field = Brand.name
    elif sort_by == "category":
        query = query.outerjoin(Product.category)
        sort_field = Category.name
    else:
        sort_field = sortable_fields.get(sort_by, Product.id)

    if sort_dir == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Загрузка связанных объектов для сериализации
    query = query.options(joinedload(Product.brand), joinedload(Product.category))

    # Пагинация
    products = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [p.to_dict() for p in products],
        "total": total_products,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }



#  directory
directory_map = {
    "brand": Brand,
    "category": Category,
    "promt": Promt,
}
class DirectoryInput(BaseModel):
    name: str
    description: str = ""


# 1. Список справочника
@router.get("/directory/{directory_name}", response_class=HTMLResponse, name="directory_page")
async def directory_page(
    request: Request,
    directory_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        raise HTTPException(404, "Справочник не найден")
    items_query = db.query(model_class)
    if not user.is_superuser:
        items_query = items_query.filter(model_class.user_id == user.id)
    items = items_query.all()
    context = {
        "request": request,
        "user": user,
        "dict_items": items,
        "dict_type": directory_name,
        "directory_name": directory_name
    }
    return template_with_csrf(request, templates, "directory.html", context)

# 2. Форма создания справочника
@router.get("/directory/{directory_name}/new", response_class=HTMLResponse, name="create_directory_page")
async def create_directory_page(
    request: Request,
    directory_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    context = {
        "request": request,
        "user": user,
        "item": None,
        "directory_name": directory_name
    }
    return template_with_csrf(request, templates, "record.html", context)

# 3. Создать запись
@router.post("/directory/{directory_name}/new")
async def create_directory(
    directory_name: str,
    data: DirectoryInput,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        raise HTTPException(404, f"Справочник '{directory_name}' не найден.")

    directory = model_class(
        name=data.name,
        description=data.description,
        user_id=user.id
    )
    db.add(directory)
    db.commit()
    db.refresh(directory)
    return JSONResponse({"success": True, "url": f"/directory/{directory_name}"})

# 4. Форма редактирования
@router.get("/directory/{directory_name}/update/{item_id}", response_class=HTMLResponse, name="update_directory_item")
async def update_directory_item(
    request: Request,
    directory_name: str,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        raise HTTPException(404, f"Справочник '{directory_name}' не найден.")

    item = db.query(model_class).filter(model_class.id == item_id).first()
    if not item:
        raise HTTPException(404, "Элемент не найден")
    check_object_permission(item, user)
    context = {
        "request": request,
        "user": user,
        "item": item,
        "directory_name": directory_name
    }
    return template_with_csrf(request, templates, "record.html", context)

# 5. Обновить запись
@router.post("/directory/{directory_name}/update/{item_id}")
async def update_directory(
    directory_name: str,
    item_id: int,
    update_data: DirectoryInput,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        return JSONResponse({"success": False, "error": f"Справочник '{directory_name}' не найден."}, status_code=404)

    item = db.query(model_class).filter(model_class.id == item_id).first()
    if not item:
        return JSONResponse({"success": False, "error": "Элемент не найден"}, status_code=404)
    check_object_permission(item, user)

    item.name = update_data.name
    item.description = update_data.description
    db.commit()
    db.refresh(item)
    # В ответе — новое имя и описание для обновления UI, если нужно
    return JSONResponse({"success": True, "url": f"/directory/{directory_name}"})

# 6. Удалить запись 
@router.delete("/directory/{directory_name}/delete/{item_id}", name="delete_directory_item")
async def delete_directory_item(
    directory_name: str,
    item_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    model_class = directory_map.get(directory_name)
    if not model_class:
        return JSONResponse({"success": False, "error": f"Справочник '{directory_name}' не найден."}, status_code=404)

    item = db.query(model_class).filter(model_class.id == item_id).first()
    if not item:
        return JSONResponse({"success": False, "error": "Элемент не найден"}, status_code=404)
    check_object_permission(item, user)
    db.delete(item)
    db.commit()
    return JSONResponse({"success": True, "url": f"/directory/{directory_name}"})
