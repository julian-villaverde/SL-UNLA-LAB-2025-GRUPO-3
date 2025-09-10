from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .Database import Base


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
