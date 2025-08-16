import os
import aiofiles # For async file operations if uncommented
import uuid

from fastapi import APIRouter, Request, Form, Depends, HTTPException, File, UploadFile, Query
from fastapi.responses import HTMLResponse, JSONResponse # RedirectResponse not used
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # For eager loading
from sqlalchemy import update, delete, func # For update and delete statements, func for count
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
from typing import List, Optional # List not used directly here
# from fastapi.templating import Jinja2Templates # templates object used directly
# from datetime import datetime, timedelta, timezone # Not used

from pydantic import ValidationError

from app.templates import templates
from app.models import User, Product, Brand, Category, Promt, ProductImage
from app.schemas import ProductCreate, ProductUpdate
from app.database.session import get_db
from app.database import crud
from app.api.auth.dependencies import get_current_user
from app.utils.permissions import check_object_permission
from app.utils.converters import to_int_or_none
from app.utils.security import csrf_protect, template_with_csrf
from app.utils.query_params import extract_dashboard_return_params_clean


router = APIRouter()
UPLOAD_DIR = "app/static/uploads" # Ensure this directory exists


@router.get("/product/new/form", response_class=HTMLResponse, name="product_new")
async def product_new_form( # Renamed for clarity
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user) # For context, not strictly DB related here
):
    # Fetch brands, categories, and promts applying user-based filtering
    # Using a large limit to effectively get all items for dropdowns
    # crud.get_directory_items sorts by name by default if 'name' attribute exists.
    brands = await crud.get_directory_items(db=db, model_class=Brand, user=user, limit=10000)
    categories = await crud.get_directory_items(db=db, model_class=Category, user=user, limit=10000)
    promts = await crud.get_directory_items(db=db, model_class=Promt, user=user, limit=10000)

    dashboard_params = await extract_dashboard_return_params_clean(request)
    
    # Формируем строку параметров для ссылки
    return_params_str = ""
    if dashboard_params:
        param_pairs = [f"{k}={v}" for k, v in dashboard_params.items()]
        return_params_str = "&".join(param_pairs)

    context = {
        "request": request,
        "product": None, # For new product form
        "brands": brands,
        "categories": categories,
        "promts": promts,
        "main_image_path": None,
        "return_params": dashboard_params,
        "return_params_str": return_params_str,
    }
    return template_with_csrf(request, templates, "product.html", context)


@router.get("/highlight-page")
async def get_highlight_page( # Changed to async def
    highlight_id: int = Query(...),
    page: int = Query(1, ge=1), # Not used in this logic directly, but part of original signature
    limit: int = Query(10, ge=1),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    name: Optional[str] = Query(None, alias="name"), # Made Optional
    ean: Optional[str] = Query(None, alias="ean"),
    upc: Optional[str] = Query(None, alias="upc"),
    brand_id: Optional[int] = Query(None, alias="brand_id"), # Made Optional
    category_id: Optional[int] = Query(None, alias="category_id"), # Made Optional
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user), # For potential user-specific filtering
):
    product_stmt = select(Product.id) # Select only IDs initially
    if not user.is_superuser: # Apply user filter if not superuser
        product_stmt = product_stmt.filter(Product.user_id == user.id)

    if name:
        product_stmt = product_stmt.filter(Product.name.ilike(f"%{name}%"))
    if ean:
        product_stmt = product_stmt.filter(Product.ean.ilike(f"%{ean}%"))
    if upc:
        product_stmt = product_stmt.filter(Product.upc.ilike(f"%{upc}%"))
    if brand_id is not None:
        product_stmt = product_stmt.filter(Product.brand_id == brand_id)
    if category_id is not None:
        product_stmt = product_stmt.filter(Product.category_id == category_id)

    sort_column = getattr(Product, sort_by, Product.id)
    product_stmt = product_stmt.order_by(sort_column.desc() if sort_dir == 'desc' else sort_column.asc())

    product_ids_result = await db.execute(product_stmt)
    product_ids = product_ids_result.scalars().all()

    if highlight_id not in product_ids:
        return {"found": False, "page": None}

    try:
        index = product_ids.index(highlight_id)
        page_num = (index // limit) + 1
        return {"found": True, "page": page_num}
    except ValueError: # Should not happen if highlight_id in product_ids
        return {"found": False, "page": None}


@router.get("/product/{product_id}/form", response_class=HTMLResponse, name="product_page")
async def product_page_form( # Renamed for clarity
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Eager load brand, category and promt along with product
    product_stmt = select(Product).options(
        selectinload(Product.brand),
        selectinload(Product.category),
        selectinload(Product.promt)
    ).filter(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    check_object_permission(product, user) # Sync call

    main_image_stmt = select(ProductImage).filter(
        ProductImage.product_id == product.id,
        ProductImage.is_main == True
    )
    main_image_result = await db.execute(main_image_stmt)
    main_image = main_image_result.scalar_one_or_none()
    main_image_path = main_image.image_path if main_image else None

    # Fetch brands, categories, and promts applying user-based filtering
    # Using a large limit to effectively get all items for dropdowns
    # crud.get_directory_items sorts by name by default if 'name' attribute exists.
    brands = await crud.get_directory_items(db=db, model_class=Brand, user=user, limit=10000)
    categories = await crud.get_directory_items(db=db, model_class=Category, user=user, limit=10000)
    promts = await crud.get_directory_items(db=db, model_class=Promt, user=user, limit=10000)

    dashboard_params = await extract_dashboard_return_params_clean(request)
    
    # Формируем строку параметров для ссылки
    return_params_str = ""
    if dashboard_params:
        param_pairs = [f"{k}={v}" for k, v in dashboard_params.items()]
        return_params_str = "&".join(param_pairs)

    context = {
        "request": request,
        "product": product,
        "brands": brands,
        "categories": categories,
        "promts": promts,
        "main_image_path": main_image_path,
        "return_params": dashboard_params,
        "return_params_str": return_params_str,
    }
    return template_with_csrf(request, templates, "product.html", context)


# --- Универсальная функция вычисления страницы для highlight_id ---
async def find_highlight_page(db, user, highlight_id, page, limit, sort_by, sort_dir, name, ean, upc, brand_id, category_id):
    from app.models import Product
    from sqlalchemy.future import select
    product_stmt = select(Product.id)
    if not user.is_superuser:
        product_stmt = product_stmt.filter(Product.user_id == user.id)
    if name:
        product_stmt = product_stmt.filter(Product.name.ilike(f"%{name}%"))
    if ean:
        product_stmt = product_stmt.filter(Product.ean.ilike(f"%{ean}%"))
    if upc:
        product_stmt = product_stmt.filter(Product.upc.ilike(f"%{upc}%"))
    if brand_id is not None:
        try:
            brand_id_int = int(brand_id)
            product_stmt = product_stmt.filter(Product.brand_id == brand_id_int)
        except Exception:
            pass
    if category_id is not None:
        try:
            category_id_int = int(category_id)
            product_stmt = product_stmt.filter(Product.category_id == category_id_int)
        except Exception:
            pass
    sort_column = getattr(Product, sort_by, Product.id)
    product_stmt = product_stmt.order_by(sort_column.desc() if sort_dir == 'desc' else sort_column.asc())
    product_ids_result = await db.execute(product_stmt)
    product_ids = product_ids_result.scalars().all()
    if highlight_id not in product_ids:
        return None
    index = product_ids.index(highlight_id)
    page_num = (index // limit) + 1
    return page_num


@router.post("/product/save", name="save_product")
async def save_product(
    request: Request, # For dashboard params
    product_id: Optional[int] = Form(None),
    name: str = Form(...),
    description: Optional[str] = Form(""), # Made Optional
    ean: Optional[str] = Form(None),
    upc: Optional[str] = Form(None),
    brand_id: Optional[str] = Form(None), # Kept as str for to_int_or_none
    category_id: Optional[str] = Form(None), # Kept as str
    promt_id: Optional[str] = Form(None), # Kept as str for to_int_or_none
    main_image: Optional[UploadFile] = File(None),
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    form_data = {
        "name": name,
        "description": description,
        "ean": ean,
        "upc": upc,
        "brand_id": to_int_or_none(brand_id),
        "category_id": to_int_or_none(category_id),
        "promt_id": to_int_or_none(promt_id),
    }

    try:
        if product_id:
            product_data = ProductUpdate(**form_data)
            product_stmt = select(Product).filter(Product.id == product_id)
            product_result = await db.execute(product_stmt)
            product = product_result.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail="Продукт не найден")
            check_object_permission(product, user)
        else:
            product_data = ProductCreate(**form_data) # name is mandatory here
            product = Product(user_id=user.id)
            db.add(product)
            # For a new product, we might need to flush to get product.id for image handling
            # await db.flush([product]) # Flushes product to DB to get ID

    except ValidationError as e:
        # Handle Pydantic validation errors, e.g., return a 422 response
        # This is a basic handler; you might want more sophisticated error reporting
        raise HTTPException(status_code=422, detail=e.errors())

    # Apply validated data to the product model
    for field, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    # Ensure description, ean, upc are set to empty strings if None (as per original logic)
    # Pydantic models might treat None differently from an empty string if not handled in schema defaults
    product.description = product.description or ""
    product.ean = product.ean or ""
    product.upc = product.upc or ""

    try:
        # Handle image upload if provided
        if main_image and main_image.filename:
            # Ensure product has an ID (especially for new products)
            if not product.id: # This implies it's a new product, product was added to session earlier
                await db.flush([product]) # Ensure product.id is available by flushing the session

            # Set existing main images to False
            update_stmt = update(ProductImage).where(
                ProductImage.product_id == product.id,
                ProductImage.is_main == True
            ).values(is_main=False)
            await db.execute(update_stmt)

            file_ext = os.path.splitext(main_image.filename)[1]
            filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            # Actual file save commented out in original, keep it that way
            async with aiofiles.open(file_path, "wb") as buffer:
                content = await main_image.read()
                await buffer.write(content)

            new_img_obj = ProductImage(
                user_id=user.id, # Assign current user as owner of the image
                product_id=product.id,
                image_path=filename,
                is_main=True
            )
            db.add(new_img_obj)

        # Ensure the product instance is in the session if it was not already flushed
        # (e.g. new product and no image uploaded)
        if product not in db and not db.is_modified(product) and product.id is None:
             # If it's a truly new, unflushed product, ensure it's added.
             # However, earlier logic `db.add(product)` for new products should cover this.
             # This specific check `product not in db` might be tricky with async sessions.
             # A simpler approach is to ensure flush/commit handles persistence.
             pass # Re-evaluating the necessity of this specific `if product not in db` block

        # For new products not yet flushed (e.g., no image upload triggered a flush),
        # or for existing products to ensure they are loaded before refresh.
        if not product.id: # If still no ID, means it's new and wasn't flushed
            await db.flush([product]) # Ensure new product has ID before potential refresh needs it (though refresh is now after commit)

        # For existing products, changes are in the session. For new products, they are added.
        # Commit first to save changes to the DB.
        await db.commit() # Persist all changes

        # Refresh after commit if you need to get DB-generated values (e.g., timestamps, trigger effects)
        # or ensure the Python object state is identical to DB state.
        if product: # Check if product object exists
             await db.refresh(product)


    except SQLAlchemyError as e:
        # await db.rollback() # Handled by get_db dependency's exception handling
        # Log the error e for debugging if logging is set up
        # print(f"Database error: {e}")
        original_error = getattr(e, 'orig', None)
        error_detail = f"Database error: {str(e)}"
        if original_error:
            error_detail = f"Database error: {str(original_error)}"

        # Check for common IntegrityError details (example for unique constraint)
        # This is a basic check and might need to be more robust depending on DB and specific constraints
        if "UNIQUE constraint failed" in str(original_error).lower():
             raise HTTPException(status_code=409, detail=f"Conflict: {error_detail}")

        raise HTTPException(status_code=500, detail=error_detail)
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e: # Catch any other unexpected errors
        # await db.rollback() # Handled by get_db
        # print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    return_params = await extract_dashboard_return_params_clean(request)
    params_str = "&".join(f"{k}={v}" for k, v in return_params.items() if v is not None) if return_params else ""
    try:
        highlight_id = product.id
        page = int(return_params.get('page', 1))
        limit = int(return_params.get('limit', 10))
        sort_by = return_params.get('sort_by', 'id')
        sort_dir = return_params.get('sort_dir', 'asc')
        name = return_params.get('name')
        ean = return_params.get('ean')
        upc = return_params.get('upc')
        brand_id_val = return_params.get('brand_id')
        category_id_val = return_params.get('category_id')
        # --- Вычисление страницы ---
        page_num = await find_highlight_page(
            db=db,
            user=user,
            highlight_id=highlight_id,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
            name=name,
            ean=ean,
            upc=upc,
            brand_id=brand_id_val,
            category_id=category_id_val
        )
        url = f"/dashboard?highlight_id={product.id}&new_created=1"
        if page_num:
            url += f"&page={page_num}"
        if params_str:
            url += f"&{params_str}"
        return JSONResponse({"url": url, "product_id": product.id})
    except Exception as e:
        import traceback
        print('ERROR in save_product:', traceback.format_exc())
        return JSONResponse({"error": "Internal server error", "details": str(e)}, status_code=500)


@router.delete("/product/{product_id}/delete", name="delete_product")
async def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    print('DELETE')
    product_stmt = select(Product).filter(Product.id == product_id)
    # Apply user ownership check only if not superuser
    if not user.is_superuser:
        product_stmt = product_stmt.filter(Product.user_id == user.id)
    
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден или нет прав доступа")

    # Find and delete associated images (files are not deleted as per original commented code)
    # This will also be handled by cascade delete if set up on Product.images relationship
    # However, explicit deletion of ProductImage records might be desired if files were managed
    images_to_delete_stmt = select(ProductImage).filter(ProductImage.product_id == product.id)
    images_result = await db.execute(images_to_delete_stmt)
    images = images_result.scalars().all()
    for img in images:
        # image_path = os.path.join(UPLOAD_DIR, img.image_path)
        # if os.path.exists(image_path):
        #     os.remove(image_path) # This would be sync, use aiofiles.os.remove for async
        await db.delete(img) # Delete DB record

    await db.delete(product)
    await db.commit() # Must be called to persist changes
    return JSONResponse({"success": True}) # Return JSONResponse for consistency


@router.post("/upload_gallery_image/{product_id}", name="upload_gallery_image")
async def upload_gallery_image(
    product_id: int,
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    product_stmt = select(Product).filter(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден для загрузки изображения")
    check_object_permission(product, user)

    file_ext = os.path.splitext(image.filename)[1] if image.filename else ".png" # Default ext
    filename = f"gallery_{uuid.uuid4().hex}_{image.filename if image.filename else ''}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await image.read()
        await buffer.write(content)

    new_image_obj = ProductImage(
        product_id=product.id, # Use product.id
        user_id=user.id, # Assuming uploader is current user
        image_path=filename,
        is_main=False
    )
    db.add(new_image_obj)
    # await db.commit() # Handled by get_db
    await db.refresh(new_image_obj) # To get ID and path for response

    return JSONResponse({ # Return JSONResponse
        "id": new_image_obj.id,
        "path": f"/{UPLOAD_DIR}/{new_image_obj.image_path}".replace("app/", ""), # Construct relative path
        "is_main": new_image_obj.is_main,
    })


@router.delete("/delete_image/{image_id}", name="delete_image")
async def delete_image(
    image_id: int, 
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    image_stmt = select(ProductImage).options(selectinload(ProductImage.product)).filter(ProductImage.id == image_id) # Load product for permission check
    image_result = await db.execute(image_stmt)
    image = image_result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")

    # Check permission based on the product the image belongs to, or image's own user_id if applicable
    if image.product:
         check_object_permission(image.product, user) # Check against product owner
    elif hasattr(image, 'user_id'): # Fallback if image has user_id directly and no product link (though unlikely for ProductImage)
         check_object_permission(image,user)
    else: # Should not happen for ProductImage tied to a Product
        raise HTTPException(status_code=403, detail="Невозможно определить права доступа к изображению")

    # Actual file deletion is commented out
    # image_file_path = os.path.join(UPLOAD_DIR, image.image_path)
    # if os.path.exists(image_file_path):
    #     os.remove(image_file_path)

    await db.delete(image)
    # await db.commit() # Handled by get_db
    return JSONResponse({"status": "ok"}) # Return JSONResponse
