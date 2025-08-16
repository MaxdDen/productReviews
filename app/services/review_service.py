from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.utils.converters import parse_int, parse_str, parse_float
from app.models import Review
from typing import Optional, Dict, Any


async def add_review(db: AsyncSession, product_id: int, user_id: Optional[int], review_data: Dict[str, Any]) -> Review:
    review = Review(
        product_id=product_id,
        user_id=user_id,
        importance=parse_int(review_data.get('importance')),
        source=parse_str(review_data.get('source')),
        text=parse_str(review_data.get('text')),
        advantages=parse_str(review_data.get('advantages')),
        disadvantages=parse_str(review_data.get('disadvantages')),
        raw_rating=parse_str(review_data.get('raw_rating')),
        rating=parse_float(review_data.get('rating')), 
        max_rating=parse_float(review_data.get('max_rating')),
        normalized_rating=parse_int(review_data.get('normalized_rating')),
    )
    db.add(review)
    return review

async def add_review_to_session(
    db: AsyncSession,
    product_id: int,
    user_id: Optional[int],
    review_data: Dict[str, Any]
) -> Review:
    review = Review(
        product_id=product_id,
        user_id=user_id,
        importance=parse_int(review_data.get('importance')),
        source=parse_str(review_data.get('source')),
        text=parse_str(review_data.get('text')),
        advantages=parse_str(review_data.get('advantages')),
        disadvantages=parse_str(review_data.get('disadvantages')),
        raw_rating=parse_str(review_data.get('raw_rating')),
        rating=parse_float(review_data.get('rating')),
        max_rating=parse_float(review_data.get('max_rating')),
        normalized_rating=parse_int(review_data.get('normalized_rating')),
    )
    db.add(review)
    return review

async def update_review(db: AsyncSession, review_id: int, user_id: Optional[int], review_data: Dict[str, Any]) -> Review:
    stmt = select(Review).filter(Review.id == review_id)
    if user_id is not None:
        stmt = stmt.filter(Review.user_id == user_id)

    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        # TODO: Consider a more specific exception type
        raise Exception("Review not found or permission denied")

    # Обновляем только те поля, которые пришли:
    review.importance = parse_int(review_data.get('importance', review.importance))
    review.source = parse_str(review_data.get('source', review.source))
    review.text = parse_str(review_data.get('text', review.text))
    review.advantages = parse_str(review_data.get('advantages', review.advantages))
    review.disadvantages = parse_str(review_data.get('disadvantages', review.disadvantages))
    review.raw_rating = parse_str(review_data.get('raw_rating', review.raw_rating))
    review.rating = parse_float(review_data.get('rating', review.rating))
    review.max_rating = parse_float(review_data.get('max_rating', review.max_rating))
    review.normalized_rating = parse_int(review_data.get('normalized_rating', review.normalized_rating))

    return review

async def delete_review(db: AsyncSession, review_id: int, user_id: Optional[int]) -> bool:
    stmt = select(Review).filter(Review.id == review_id)
    if user_id is not None:
        stmt = stmt.filter(Review.user_id == user_id)

    result = await db.execute(stmt)
    review_to_delete = result.scalar_one_or_none()

    if review_to_delete:
        await db.delete(review_to_delete)
        return True
    return False

async def delete_all_reviews_for_product(db: AsyncSession, product_id: int, user_id: Optional[int]) -> int:
    stmt = delete(Review).filter(Review.product_id == product_id)
    if user_id is not None:
        stmt = stmt.filter(Review.user_id == user_id)

    result = await db.execute(stmt)
    return result.rowcount
