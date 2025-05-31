from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
    from app.models.user import User
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, user_id: int):
    from app.models.user import User
    return db.query(User).filter(User.id == user_id).first()

