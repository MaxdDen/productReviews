import math
import traceback # Keep for potential debugging, though not actively used in async changes
import pprint # Keep for potential debugging
from fastapi import APIRouter, Request, Depends, HTTPException, Header, UploadFile, File, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.templating import Jinja2Templates # Not used directly, templates object is used
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload # For eager loading with async
from sqlalchemy import func # For count
from typing import List, Optional, Any # Added Any

from app.templates import templates
from app.api.auth.dependencies import get_current_user
from app.database.session import get_db # This now provides AsyncSession
from app.models import User, Product, Promt, Review
from app.services.openai_service import analyze_reviews
from app.services.review_service import add_review, add_review_to_session, update_review, delete_review, delete_all_reviews_for_product # These are now async
from app.utils.permissions import check_object_permission
from app.utils.security import ensure_csrf_token, csrf_protect, template_with_csrf
from app.utils.query_params import extract_analyze_filters, extract_dashboard_return_params_clean, AnalyzeFilters
from app.utils.parsers import parse_reviews_file_to_list # Assuming this is potentially async or I/O bound


router = APIRouter()

@router.get("/analyze/{product_id}/form", response_class=HTMLResponse, name="analyze_product_page")
async def analyze_product_page(
    request: Request,
    product_id: int, # Required parameter from path
    user: User = Depends(get_current_user), # Assuming get_current_user is async or compatible
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    importance: Optional[int] = Query(None, ge=1, le=100), # Made Optional
    source: str = Query('', alias="source"),
    text: str = Query('', alias="text"),
    advantages: str = Query('', alias="advantages"),
    disadvantages: str = Query('', alias="disadvantages"),
    raw_rating: str = Query('', alias="raw_rating"),
    rating: Optional[float] = Query(None, ge=0.0, le=100.0), # Made Optional
    max_rating: Optional[float] = Query(None, ge=0.0, le=100.0), # Made Optional
    normalized_rating: Optional[int] = Query(None),
    normalized_rating_min: int = Query(0, ge=0, le=99),
    normalized_rating_max: int = Query(100, ge=1, le=100)
):
    filters = extract_analyze_filters(request) # Assuming this is synchronous and CPU bound

    # Fetch product with reviews
    # Note: joinedload with async needs careful handling if relationships are also to be async.
    # For now, assuming Product.reviews is a standard relationship.
    product_stmt = select(Product).options(joinedload(Product.reviews)).filter(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    # Use .unique() to handle potential duplicate rows from joinedload of a collection
    product = product_result.unique().scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    check_object_permission(product, user) # Assuming this is synchronous

    # Base query for reviews
    review_stmt = select(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        review_stmt = review_stmt.filter(Review.user_id == user.id)

    # Apply filters
    if importance is not None: # Check for None explicitly
        review_stmt = review_stmt.filter(Review.importance == importance) # Exact match for int
    if source:
        review_stmt = review_stmt.filter(Review.source.ilike(f"%{source}%"))
    if text:
        review_stmt = review_stmt.filter(Review.text.ilike(f"%{text}%"))
    if advantages:
        review_stmt = review_stmt.filter(Review.advantages.ilike(f"%{advantages}%"))
    if disadvantages:
        review_stmt = review_stmt.filter(Review.disadvantages.ilike(f"%{disadvantages}%"))
    if normalized_rating_min is not None: # Check for explicit None or 0 if that's the intent
        review_stmt = review_stmt.filter(Review.normalized_rating >= normalized_rating_min)
    if normalized_rating_max is not None:
        review_stmt = review_stmt.filter(Review.normalized_rating <= normalized_rating_max)

    # Count total reviews with filters
    count_stmt = select(func.count()).select_from(review_stmt.subquery()) # Use subquery for count with filters
    total_reviews_result = await db.execute(count_stmt)
    total_reviews = total_reviews_result.scalar_one()

    total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else 1

    # Get paginated reviews
    review_stmt = review_stmt.order_by(Review.id.asc()).offset((page - 1) * limit).limit(limit)
    reviews_result = await db.execute(review_stmt)
    reviews = reviews_result.scalars().all()

    # Get all promts
    promts_stmt = select(Promt)
    promts_result = await db.execute(promts_stmt)
    promts = promts_result.scalars().all()

    # Extract dashboard return parameters
    dashboard_return_params = await extract_dashboard_return_params_clean(request)
    
    # Формируем строку параметров для ссылки
    return_params_str = ""
    if dashboard_return_params:
        param_pairs = [f"{k}={v}" for k, v in dashboard_return_params.items()]
        return_params_str = "&".join(param_pairs)

    context = {
        "request": request,
        **filters, # This is fine
        "user": user, # User object from get_current_user
        "product": product, # Product object
        "promts": promts, # List of Promt objects
        "reviews": reviews, # List of Review objects
        "items": reviews, # Use actual reviews list
        "total": total_reviews,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "return_params": dashboard_return_params,
        "return_params_str": return_params_str,
    }
    return template_with_csrf(request, templates, "analyze_product.html", context)


@router.get("/analyze/data", response_class=JSONResponse, name="analyze_product_data")
async def analyze_product_data(
    request: Request,  # Добавляем request для отладки
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user) # Assuming get_current_user is fine
):
    # Получаем параметры из query string
    query_params = request.query_params
    product_id = query_params.get("product_id")
    page = int(query_params.get("page", 1))
    limit = int(query_params.get("limit", 10))
    importance = query_params.get("importance")
    source = query_params.get("source", "")
    text = query_params.get("text", "")
    advantages = query_params.get("advantages", "")
    disadvantages = query_params.get("disadvantages", "")
    sort_by = query_params.get("sort_by", "id")
    sort_dir = query_params.get("sort_dir", "asc")
    
    try:
        # Убедимся, что product_id - это int
        product_id = int(product_id) if product_id else None
        if not product_id:
            raise HTTPException(status_code=422, detail="product_id is required")
        
        review_stmt = select(Review).filter(Review.product_id == product_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid product_id: {product_id}")
    if not user.is_superuser:
        review_stmt = review_stmt.filter(Review.user_id == user.id)

    if importance and importance != "":
        try:
            importance_int = int(importance)
            review_stmt = review_stmt.filter(Review.importance == importance_int)
        except ValueError:
            pass  # Игнорируем невалидные значения
    if source and source != "":
        review_stmt = review_stmt.filter(Review.source.ilike(f"%{source}%"))
    if text and text != "":
        review_stmt = review_stmt.filter(Review.text.ilike(f"%{text}%"))
    if advantages and advantages != "":
        review_stmt = review_stmt.filter(Review.advantages.ilike(f"%{advantages}%"))
    if disadvantages and disadvantages != "":
        review_stmt = review_stmt.filter(Review.disadvantages.ilike(f"%{disadvantages}%"))

    sortable_fields = {
        "id": Review.id,
        "importance": Review.importance,
        "source": Review.source,
        "text": Review.text,
        "advantages": Review.advantages,
        "disadvantages": Review.disadvantages,
        "normalized_rating": Review.normalized_rating
    }

    sort_field = sortable_fields.get(sort_by, Review.id)
    review_stmt = review_stmt.order_by(sort_field.desc() if sort_dir == "desc" else sort_field.asc())

    # Count total reviews with filters
    count_stmt = select(func.count()).select_from(review_stmt.subquery())
    total_reviews_result = await db.execute(count_stmt)
    total_reviews = total_reviews_result.scalar_one()

    total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else 1

    # Paginate
    paginated_stmt = review_stmt.offset((page - 1) * limit).limit(limit)
    reviews_result = await db.execute(paginated_stmt)
    reviews = reviews_result.scalars().all()

    return {
        "items": [p.to_dict() for p in reviews], # to_dict() methods on models are synchronous
        "total": total_reviews,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.post("/analyze/{product_id}")
async def analyze_product(
    product_id: int,
    filters: AnalyzeFilters = Body(...), # Assuming AnalyzeFilters is a Pydantic model
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect), # Assuming csrf_protect is async or compatible
    db: AsyncSession = Depends(get_db)
):
    review_stmt = select(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        review_stmt = review_stmt.filter(Review.user_id == user.id)

    promt_id = filters.promt_id

    if filters.importance is not None:
        review_stmt = review_stmt.filter(Review.importance == filters.importance)
    if filters.source:
        review_stmt = review_stmt.filter(Review.source.ilike(f"%{filters.source}%"))
    if filters.text:
        review_stmt = review_stmt.filter(Review.text.ilike(f"%{filters.text}%"))
    if filters.advantages:
        review_stmt = review_stmt.filter(Review.advantages.ilike(f"%{filters.advantages}%"))
    if filters.disadvantages:
        review_stmt = review_stmt.filter(Review.disadvantages.ilike(f"%{filters.disadvantages}%"))
    if filters.normalized_rating_min is not None:
        review_stmt = review_stmt.filter(Review.normalized_rating >= filters.normalized_rating_min)
    if filters.normalized_rating_max is not None:
        review_stmt = review_stmt.filter(Review.normalized_rating <= filters.normalized_rating_max)

    reviews_result = await db.execute(review_stmt)
    reviews = reviews_result.scalars().all()

    product_stmt = select(Product).filter(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found for analysis")
    check_object_permission(product, user) # Sync call

    structured_reviews = [{
        "importance": r.importance or 100, # Defaulting if None
        "source": r.source or "неизвестно",
        "text": r.text or "",
        "advantages": r.advantages or "",
        "disadvantages": r.disadvantages or "",
        "rating": r.normalized_rating if r.normalized_rating is not None else "нет оценки"
    } for r in reviews]

    # analyze_reviews service is already async and takes db session
    analysis_result_str = await analyze_reviews(structured_reviews, promt_id=promt_id, db=db)
    return {"result": analysis_result_str}


@router.post("/parse-reviews-file/{product_id}", name="parse_reviews_file")
async def parse_reviews_file(
    request: Request, # Not used directly, but often kept for context or future use
    product_id: int,
    user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    # parse_reviews_file_to_list might do I/O (reading file). If it's purely CPU-bound, it's fine.
    # If it reads the file in a blocking way, it should be made async or run in threadpool.
    # For now, assuming it's okay or that UploadFile content is already in memory.
    # The function parse_reviews_file_to_list is async and expects an UploadFile object.
    parsed_result = await parse_reviews_file_to_list(file)

    reviews_data = parsed_result["reviews"]
    
    added_reviews_objects = []
    try:
        for review_dict in reviews_data:
            # add_review service is now async
            #review = await add_review(db, product_id, user.id, review_dict)
            review = await add_review_to_session(db, product_id, user.id, review_dict)

            added_reviews_objects.append(review)
            
    except Exception as e:
        await db.rollback()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Ошибка при добавлении: {str(e)}"}
        )

    # Если нужно вернуть dict-представление:
    result_items = [r.to_dict() for r in added_reviews_objects if hasattr(r, "to_dict")]
    
    # Count total reviews for the user/product
    count_stmt = select(func.count(Review.id)).filter(Review.product_id == product_id)
    if not user.is_superuser:
        count_stmt = count_stmt.filter(Review.user_id == user.id)
    total_reviews_result = await db.execute(count_stmt)
    total_reviews = total_reviews_result.scalar_one()
    
    return {
        "status": "ok",
        "items": result_items, # to_dict() is sync
        "success_count": parsed_result["success_count"],
        "total_rows": parsed_result["total_rows"],
        "empty_rows": parsed_result["empty_rows"],
        "errors": parsed_result["errors"],
        "total": total_reviews
    }


@router.post("/api/review/{product_id}/add", name="add_review_item")
async def add_review_item(
    product_id: int,
    request: Request, # Used for request.json()
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()

    # Verify product exists
    product_stmt = select(Product).filter(Product.id == product_id)
    product_result = await db.execute(product_stmt)
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found.")

    # Ensure the user has permission to add reviews to this product if necessary
    # For now, assuming any authenticated user can add a review to any existing product
    # check_object_permission(product, user) # Uncomment and adapt if product ownership/access rules apply

    # review_dict can be constructed directly
    # add_review service is now async
    review = await add_review(db, product_id, user.id, data) # Pass data directly if add_review expects dict
    return {"status": "ok", "id": review.id}


@router.put("/api/review/{reviewId}/update", name="update_review_item")
async def update_review_item(
    reviewId: int,
    request: Request, # Used for request.json()
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await request.json()
        # update_review service is now async
        review = await update_review(db, reviewId, user.id, data) # Pass data directly
        await db.commit()  # Коммитим транзакцию для сохранения изменений
        await db.refresh(review)  # Обновляем объект
        return {"status": "ok", "id": review.id}
    except Exception as e:
        await db.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/review/clear/{product_id}", name="analyze_reviews_clear")
async def analyze_reviews_clear(
    product_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    try:
        effective_user_id = None if user.is_superuser else user.id
        # delete_all_reviews_for_product service is now async
        deleted_count = await delete_all_reviews_for_product(db, product_id, effective_user_id)
        
        await db.commit()  # Коммитим транзакцию для сохранения удаления
        
        return {
            "status": "ok",
            "deleted": deleted_count
        }
    except Exception as e:
        await db.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/review/{review_id}/delete", name="delete_review_item")
async def delete_review_item(
    review_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # delete_review service is now async and handles the logic of finding and deleting
        deleted = await delete_review(db, review_id, user_id=None if user.is_superuser else user.id)
        
        if not deleted:
            # The service function now returns False if review not found / not permitted
            raise HTTPException(status_code=404, detail="Отзыв не найден или нет прав на удаление")

        await db.commit()  # Коммитим транзакцию для сохранения удаления
        return {"success": True, "deleted_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()  # Откатываем транзакцию в случае ошибки
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/review/{review_id}", name="get_review_item")
async def get_review_item(
    review_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    review_stmt = select(Review).filter(Review.id == review_id)
    if not user.is_superuser:
        review_stmt = review_stmt.filter(Review.user_id == user.id)
    
    review_result = await db.execute(review_stmt)
    review = review_result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return review.to_dict()


@router.post("/api/review", name="create_review_item")
async def create_review_item(
    request: Request,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await request.json()
        
        # Проверяем, есть ли review_id для определения операции UPDATE/CREATE
        review_id = data.get("review_id")
        
        if review_id:
            # ОПЕРАЦИЯ UPDATE - обновляем существующий отзыв
            print(f"UPDATE operation for review_id: {review_id}")
            review_data = {
                "importance": data.get("importance"),
                "source": data.get("source"),
                "text": data.get("text"),
                "advantages": data.get("advantages"),
                "disadvantages": data.get("disadvantages"),
                "raw_rating": data.get("raw_rating"),
                "rating": data.get("rating"),
                "max_rating": data.get("max_rating"),
                "normalized_rating": data.get("normalized_rating")
            }
            
            review = await update_review(db, review_id, user.id, review_data)
            await db.commit()
            await db.refresh(review)
            return review.to_dict()
        else:
            # ОПЕРАЦИЯ CREATE - создаем новый отзыв
            print(f"CREATE operation for product_id: {data.get('product_id')}")
            review_data = {
                "product_id": data.get("product_id"),
                "importance": data.get("importance"),
                "source": data.get("source"),
                "text": data.get("text"),
                "advantages": data.get("advantages"),
                "disadvantages": data.get("disadvantages"),
                "raw_rating": data.get("raw_rating"),
                "rating": data.get("rating"),
                "max_rating": data.get("max_rating"),
                "normalized_rating": data.get("normalized_rating")
            }
            
            review = await add_review(db, review_data["product_id"], user.id, review_data)
            await db.commit()
            await db.refresh(review)
            return review.to_dict()
            
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
