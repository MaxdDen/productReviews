from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base


class Promt(Base):
    __tablename__ = "promts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="promts")

    products = relationship("Product", back_populates="promt")

    def __str__(self):
        return self.name
