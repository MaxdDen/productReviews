from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, Optional

from app.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .product import Product


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    importance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    advantages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disadvantages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_rating: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Assuming Text is appropriate, could be String
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    normalized_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")

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

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, product_id={self.product_id}, user_id={self.user_id})>"