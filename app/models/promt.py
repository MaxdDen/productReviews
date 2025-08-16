from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List, Optional

from app.database.base import Base

if TYPE_CHECKING:
    from .user import User
    from .product import Product


class Promt(Base):
    __tablename__ = "promts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Assuming user_id can be nullable
    user: Mapped[Optional["User"]] = relationship("User", back_populates="promts")

    products: Mapped[List["Product"]] = relationship("Product", back_populates="promt")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Promt(id={self.id}, name='{self.name}')>"

    def to_dict(self, include_user=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
        }
        if include_user and self.user:
            data["user"] = {
                "id": self.user.id,
                "username": self.user.username
            }
        return data
