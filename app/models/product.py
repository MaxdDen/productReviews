from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base


# Продукты
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    ean = Column(String(13), nullable=True)
    upc = Column(String(12), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    promt_id = Column(Integer, ForeignKey("promts.id"), nullable=True)
    analysis_result = Column(Text)

    user = relationship("User", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    category = relationship("Category", back_populates="products")
    promt = relationship("Promt", back_populates="products")

    reviews = relationship("Review", back_populates="product", cascade="all, delete")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete")

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
