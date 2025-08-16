from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING

from app.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .product import Product


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    image_path: Mapped[str] = mapped_column(String, nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped["Product"] = relationship("Product", back_populates="images")
    user: Mapped["User"] = relationship("User", back_populates="images")

    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, path='{self.image_path}')>"
