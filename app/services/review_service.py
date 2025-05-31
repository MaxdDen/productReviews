from sqlalchemy.orm import Session

from app.utils.converters import parse_int, parse_str, parse_float
from app.models import Review



def add_review(db: Session, product_id: int, user_id: int | None, review_data: dict):
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
    db.commit()
    db.refresh(review) 
    return review

def update_review(db: Session, review_id: int, user_id: int | None, review_data: dict):
    review = db.query(Review).filter(Review.id == review_id)
    if user_id is not None:
        review = review.filter(Review.user_id == user_id)
    review = review.first()
    if not review:
        raise Exception("Review not found")
    # Обновляем только те поля, которые пришли:
    review.importance = parse_int(review_data.get('importance'))
    review.source = parse_str(review_data.get('source'))
    review.text = parse_str(review_data.get('text'))
    review.advantages = parse_str(review_data.get('advantages'))
    review.disadvantages = parse_str(review_data.get('disadvantages'))
    review.raw_rating = parse_str(review_data.get('raw_rating'))
    review.rating = parse_float(review_data.get('rating'))
    review.max_rating = parse_float(review_data.get('max_rating'))
    review.normalized_rating = parse_int(review_data.get('normalized_rating'))
    db.commit()
    db.refresh(review)
    return review

def delete_review(db: Session, review_id: int, user_id: int | None):
    query = db.query(Review).filter(Review.id == review_id)
    if user_id is not None:
        query = query.filter(Review.user_id == user_id)
    query.delete()
    db.commit()

def delete_all_reviews_for_product(db: Session, product_id: int, user_id: int | None):
    query = db.query(Review).filter(Review.product_id == product_id)
    if user_id is not None:
        query = query.filter(Review.user_id == user_id)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return deleted_count


