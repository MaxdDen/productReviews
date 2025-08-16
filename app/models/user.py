from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List

from app.database.base import Base

if TYPE_CHECKING:
    from .product import Product
    from .brand import Brand
    from .category import Category
    from .promt import Promt
    from .image import ProductImage
    from .review import Review


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="user", cascade="all, delete")
    brands: Mapped[List["Brand"]] = relationship("Brand", back_populates="user", cascade="all, delete")
    categories: Mapped[List["Category"]] = relationship("Category", back_populates="user", cascade="all, delete")
    promts: Mapped[List["Promt"]] = relationship("Promt", back_populates="user", cascade="all, delete")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="user", cascade="all, delete")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
