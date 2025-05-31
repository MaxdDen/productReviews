import os
import shutil
import uuid

from fastapi import APIRouter, Request, Form, Depends, HTTPException, File, UploadFile, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone

from app.templates import templates
from app.models import User, Product, Brand, Category, Review, ProductImage
from app.database import get_db
from app.api.auth.utils import get_current_user 
from app.utils.permissions import check_object_permission
from app.utils.converters import to_int_or_none
from app.utils.security import ensure_csrf_token, csrf_protect, template_with_csrf
from app.utils.query_params import extract_dashboard_return_params


router = APIRouter()
UPLOAD_DIR = "app/static/uploads"


@router.get("/product/new/form", response_class=HTMLResponse, name="product_new")
async def product_new(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    brands = db.query(Brand).all()
    categories = db.query(Category).all()
    context = {
        "request": request,
        "product": None,
        "brands": brands,
        "categories": categories,
        "main_image_path": None,
        "return_params": await extract_dashboard_return_params(request),
    }

    return template_with_csrf(request, templates, "product.html", context)

@router.get("/highlight-page")
def get_highlight_page(
    highlight_id: int = Query(...),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    name: str = Query("", alias="name"),
    ean: str = Query("", alias="ean"),
    upc: str = Query("", alias="upc"),
    brand_id: int = Query(None, alias="brand_id"),
    category_id: int = Query(None, alias="category_id"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # 1. Фильтрация
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if ean:
        query = query.filter(Product.ean.ilike(f"%{ean}%"))
    if upc:
        query = query.filter(Product.upc.ilike(f"%{upc}%"))
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # 2. Сортировка
    sort_column = getattr(Product, sort_by, Product.id)
    if sort_dir == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 3. Список id
    product_ids = [row.id for row in query.with_entities(Product.id).all()]
    if highlight_id not in product_ids:
        return {"found": False, "page": None}
    index = product_ids.index(highlight_id)
    page_num = (index // limit) + 1

    return {"found": True, "page": page_num}

@router.get("/product/{product_id}/form", response_class=HTMLResponse, name="product_page")
async def product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Продукт не найден")
    check_object_permission(product, user)

    main_image = db.query(ProductImage).filter(
        ProductImage.product_id == product.id,
        ProductImage.is_main == True
    ).first()
    main_image_path = main_image.image_path if main_image else None
    brands = db.query(Brand).all()
    categories = db.query(Category).all()

    context = {
        "request": request,
        "product": product,
        "brands": brands,
        "categories": categories,
        "main_image_path": main_image_path,
        "return_params": await extract_dashboard_return_params(request),
    }
    return template_with_csrf(request, templates, "product.html", context)


@router.post("/product/save", name="save_product")
async def save_product(
    request: Request,
    product_id: Optional[int] = Form(None),
    name: str = Form(...),
    description: str = Form(""),
    ean: Optional[str] = Form(None),
    upc: Optional[str] = Form(None),
    brand_id: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    main_image: Optional[UploadFile] = File(None),
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(404, "Продукт не найден")
        check_object_permission(product, user)
    else:
        product = Product(user_id=user.id)
        db.add(product)

    product.name = name
    product.description = description if description else ""
    product.ean = ean if ean else ""
    product.upc = upc if upc else ""
    product.brand_id = to_int_or_none(brand_id)
    product.category_id = to_int_or_none(category_id)
    db.commit()
    db.refresh(product)

    # Изображение
    if main_image and main_image.filename:
        db.query(ProductImage).filter(
            ProductImage.product_id == product.id,
            ProductImage.is_main == True
        ).update({"is_main": False})

        file_ext = os.path.splitext(main_image.filename)[1]
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(main_image.file, buffer)

        db.add(ProductImage(
            user_id=product.user_id,
            product_id=product.id,
            image_path=filename,
            is_main=True
        ))

    db.commit()

    # Получить return_params (фильтры/сортировки) из запроса, если они приходят
    return_params = await extract_dashboard_return_params(request)
    params_str = "&".join(f"{k}={v}" for k, v in return_params.items()) if return_params else ""
    print("return_params ", return_params)
    print("params_str ", params_str)
    url = f"/dashboard?highlight_id={product.id}&{params_str}" if params_str else f"/dashboard?highlight_id={product.id}"
    print("url ", url)

    return JSONResponse({"url": url, "product_id": product.id})



@router.delete("/product/{product_id}/delete", name="delete_product")
async def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    # Найди продукт
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Удалить связанное изображение, если есть
    main_image_obj = db.query(ProductImage).filter(
            ProductImage.product_id == product.id,
            ProductImage.is_main == True
        ).first()
    if main_image_obj and main_image_obj.image_path:
        image_path = os.path.join(UPLOAD_DIR, main_image_obj.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
        # Если надо — удаляем запись из базы:
        db.delete(main_image_obj)
        db.commit()

    # Удалить продукт
    db.delete(product)
    db.commit()
    return {"success": True}







@router.post("/upload_gallery_image/{product_id}", name="upload_gallery_image")
async def upload_gallery_image(
    product_id: int,
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    check_object_permission(product, user)

    filename = f"gallery_{uuid.uuid4().hex}_{image.filename}"
    file_path = f"static/uploads/{filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_image = ProductImage(
        product_id=product_id,
        user_id=user.id,
        image_path=filename,
        is_main=False
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {
        "id": new_image.id,
        "path": f"/static/uploads/{new_image.image_path}",
        "is_main": new_image.is_main,
    }


@router.delete("/delete_image/{image_id}", name="delete_image")
async def delete_image(
    image_id: int, 
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    check_object_permission(image, user)

    db.delete(image)
    db.commit()
    return {"status": "ok"}
