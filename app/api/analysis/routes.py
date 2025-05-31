import math
import traceback
import pprint
from fastapi import APIRouter, Request, Depends, HTTPException, Header, UploadFile, File, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.templates import templates
from app.api.auth.utils import get_current_user
from app.database import get_db
from app.models import User, Product, Promt, Review
from app.services.openai_service import analyze_reviews
from app.services.review_service import add_review, update_review, delete_review, delete_all_reviews_for_product
from app.utils.permissions import check_object_permission
from app.utils.security import ensure_csrf_token, csrf_protect, template_with_csrf
from app.utils.query_params import extract_analyze_filters, extract_dashboard_return_params, AnalyzeFilters
from app.utils.parsers import parse_reviews_file_to_list


router = APIRouter()

@router.get("/analyze/{product_id}/form", response_class=HTMLResponse, name="analyze_product_page")
async def analyze_product_page(
    request: Request,
    product_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    importance: int = Query(None, ge=1, le=100),
    source: str = Query('', alias="source"),
    text: str = Query('', alias="text"),
    advantages: str = Query('', alias="advantages"),
    disadvantages: str = Query('', alias="disadvantages"),
    raw_rating: str = Query('', alias="raw_rating"),
    rating: float = Query(None, ge=0.0, le=100.0),
    max_rating: float = Query(None, ge=0.0, le=100.0),
    normalized_rating: Optional[int] = Query(None),
    normalized_rating_min: int = Query(0, ge=0, le=99),
    normalized_rating_max: int = Query(100, ge=1, le=100)
):
    filters = extract_analyze_filters(request)

    product = db.query(Product).options(joinedload(Product.reviews)).filter(Product.id == product_id).first()
    check_object_permission(product, user)

    # Отзывы: если суперюзер — все, иначе только свои
    review_query = db.query(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        review_query = review_query.filter(Review.user_id == user.id)

    # Сборка фильтра SQLAlchemy по полученным параметрам
    if importance:
        review_query = review_query.filter(Review.importance.ilike(f"%{importance}%"))
    if source:
        review_query = review_query.filter(Review.source.ilike(f"%{source}%"))
    if text:
        review_query = review_query.filter(Review.text.ilike(f"%{text}%"))
    if advantages:
        review_query = review_query.filter(Review.advantages.ilike(f"%{advantages}%"))
    if disadvantages:
        review_query = review_query.filter(Review.disadvantages.ilike(f"%{disadvantages}%"))
    if normalized_rating_min:
        review_query = review_query.filter(Review.normalized_rating >= normalized_rating_min)
    if normalized_rating_max:
        review_query = review_query.filter(Review.normalized_rating <= normalized_rating_max)

    review_query = review_query.order_by(Review.id.asc())

    total_reviews = review_query.count()
    total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else 1

    reviews = review_query.offset((page - 1) * limit).limit(limit).all()

    promts = db.query(Promt).all()

    context = {
        "request": request,
        **filters,
        "user": user,
        "product": product,
        "promts": promts,
        "reviews": reviews,
        "items": [...],
        "total": total_reviews,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "return_params": await extract_dashboard_return_params(request),
    }
    return template_with_csrf(request, templates, "analyze_product.html", context)

@router.get("/analyze/data", response_class=JSONResponse, name="analyze_product_data")
async def analyze_product_data(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    product_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    importance: int = Query(None, ge=1, le=100),
    source: str = Query('', alias="source"),
    text: str = Query('', alias="text"),
    advantages: str = Query('', alias="advantages"),
    disadvantages: str = Query('', alias="disadvantages"),
    raw_rating: str = Query('', alias="raw_rating"),
    rating: float = Query(None, alias="rating"),
    max_rating: float = Query(None, alias="max_rating"),
    sort_by: str = Query("id", alias="sort_by"),
    sort_dir: str = Query("asc", alias="sort_dir"),
    normalized_rating_min: int = Query(0, ge=0, le=99),
    normalized_rating_max: int = Query(100, ge=1, le=100)
):

    # Отзывы: если суперюзер — все, иначе только свои
    review_query = db.query(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        review_query = review_query.filter(Review.user_id == user.id)

    # Сборка фильтра SQLAlchemy по полученным параметрам
    if importance:
        review_query = review_query.filter(Review.importance == importance)
    if source:
        review_query = review_query.filter(Review.source.ilike(f"%{source}%"))
    if text:
        review_query = review_query.filter(Review.text.ilike(f"%{text}%"))
    if advantages:
        review_query = review_query.filter(Review.advantages.ilike(f"%{advantages}%"))
    if disadvantages:
        review_query = review_query.filter(Review.disadvantages.ilike(f"%{disadvantages}%"))
    if normalized_rating_min:
        review_query = review_query.filter(Review.normalized_rating >= normalized_rating_min)
    if normalized_rating_max:
        review_query = review_query.filter(Review.normalized_rating <= normalized_rating_max)

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
    if sort_dir == "desc":
        review_query = review_query.order_by(sort_field.desc())
    else:
        review_query = review_query.order_by(sort_field.asc())

    total_reviews = review_query.count()
    total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else 1

    # Пагинация
    reviews = review_query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [p.to_dict() for p in reviews],
        "total": total_reviews,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.post("/analyze/{product_id}")
async def analyze_product(
    product_id: int,
    filters: AnalyzeFilters = Body(...),
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    # Отзывы: если суперюзер — все, иначе только свои
    review_query = db.query(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        review_query = review_query.filter(Review.user_id == user.id)

    promt_id = filters.promt_id

    # Сборка фильтра SQLAlchemy по полученным параметрам
    if filters.importance:
        review_query = review_query.filter(Review.importance == filters.importance)
    if filters.source:
        review_query = review_query.filter(Review.source.ilike(f"%{filters.source}%"))
    if filters.text:
        review_query = review_query.filter(Review.text.ilike(f"%{filters.text}%"))
    if filters.advantages:
        review_query = review_query.filter(Review.advantages.ilike(f"%{filters.advantages}%"))
    if filters.disadvantages:
        review_query = review_query.filter(Review.disadvantages.ilike(f"%{filters.disadvantages}%"))
    if filters.normalized_rating_min:
        review_query = review_query.filter(Review.normalized_rating >= filters.normalized_rating_min)
    if filters.normalized_rating_max:
        review_query = review_query.filter(Review.normalized_rating <= filters.normalized_rating_max)

    reviews = review_query.all()

    product = db.query(Product).filter(Product.id == product_id).first()
    check_object_permission(product, user)

    structured_reviews = [{
        "importance": r.importance or 100,
        "source": r.source or "неизвестно",
        "text": r.text or "",
        "advantages": r.advantages or "",
        "disadvantages": r.disadvantages or "",
        "rating": r.normalized_rating or "нет оценки"
    } for r in reviews]
    print("structured_reviews", structured_reviews)

    result = await analyze_reviews(structured_reviews, promt_id=promt_id, db=db)
    return {"result": result}

@router.post("/parse-reviews-file/{product_id}", name="parse_reviews_file")
async def parse_reviews_file(
    request: Request,
    product_id: int,
    user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    parsed_result = await parse_reviews_file_to_list(file)
    reviews_data = parsed_result["reviews"]
    
    added_reviews = []
    for review_dict in reviews_data:
        review = add_review(db, product_id, user.id, review_dict)
        added_reviews.append(review)
    
    # <--- Добавляем подсчет total отзывов ПОЛЬЗОВАТЕЛЯ (или всех, если суперюзер)
    query = db.query(Review).filter(Review.product_id == product_id)
    if not user.is_superuser:
        query = query.filter(Review.user_id == user.id)
    total_reviews = query.count()
    
    return {
        "status": "ok",
        "items": [r.to_dict() for r in added_reviews],
        "success_count": parsed_result["success_count"],
        "total_rows": parsed_result["total_rows"],
        "empty_rows": parsed_result["empty_rows"],
        "errors": parsed_result["errors"],
        "total": total_reviews
    }

@router.post("/review/{product_id}/add", name="add_review_item")
async def add_review_item(
    product_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    data = await request.json()
    review_dict = {
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
    review = add_review(db, product_id, user.id, review_dict)
    return {"status": "ok", "id": review.id}

@router.put("/review/{reviewId}/update", name="update_review_item")
async def update_review_item(
    reviewId: int,
    request: Request,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    data = await request.json()
    review_dict = {
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
    review = update_review(db, reviewId, user.id, review_dict)
    return {"status": "ok", "id": review.id}

@router.delete("/analyze/{product_id}/reviews/clear", name="analyze_reviews_clear")
async def analyze_reviews_clear(
    product_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    # Для суперюзера — удаляем все, для обычного — только свои
    user_id = None if user.is_superuser else user.id

    deleted_count = delete_all_reviews_for_product(db, product_id, user_id)
    return {
        "status": "ok",
        "deleted": deleted_count
    }

@router.delete("/review/{review_id}/delete", name="delete_review_item")
async def delete_review_item(
    review_id: int,
    user: User = Depends(get_current_user),
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id)
    if not user.is_superuser:
        review = review.filter(Review.user_id == user.id)
    
    review = review.first()
    if not review:
        return {"success": False, "error": "Отзыв не найден"}

    db.delete(review)
    db.commit()
    return {"success": True, "deleted_id": review_id}
