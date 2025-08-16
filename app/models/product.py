from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List, Optional

from app.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .brand import Brand
    from .category import Category
    from .promt import Promt
    from .review import Review
    from .image import ProductImage


# Продукты
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True) # Assuming name can be nullable based on original
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Assuming description can be nullable
    ean: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    upc: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    brand_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("brands.id"), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    promt_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("promts.id"), nullable=True)

    analysis_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="products")
    brand: Mapped[Optional["Brand"]] = relationship("Brand", back_populates="products")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    promt: Mapped[Optional["Promt"]] = relationship("Promt", back_populates="products")

    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete")

    def to_dict(self):
        main_image = next((img for img in self.images if img.is_main), None)
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ean": self.ean,
            "upc": self.upc,
            "user_id": self.user_id,
            "brand_id": self.brand_id,
            "category_id": self.category_id,
            "promt_id": self.promt_id,
            "brand": {"id": self.brand.id, "name": self.brand.name} if self.brand else None,
            "category": {"id": self.category.id, "name": self.category.name} if self.category else None,
            "promt": {"id": self.promt.id, "name": self.promt.name} if self.promt else None,
            "analysis_result": self.analysis_result,
            "main_image_filename": main_image.image_path if main_image else None,
        }

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}')>"
