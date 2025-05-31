from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

from app.database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    importance = Column(Integer, nullable=True)
    source = Column(Text)
    text = Column(Text)
    advantages = Column(Text)
    disadvantages = Column(Text)
    raw_rating = Column(Text)
    rating = Column(Float, nullable=True)
    max_rating = Column(Float, nullable=True)
    normalized_rating = Column(Integer, nullable=True)

    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id")) 

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "importance": self.importance,
            "source": self.source,
            "text": self.text,
            "advantages": self.advantages,
            "disadvantages": self.disadvantages,
            "raw_rating": self.raw_rating,
            "rating": self.rating,
            "max_rating": self.max_rating,
            "normalized_rating": self.normalized_rating,
        }