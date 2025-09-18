from sqlalchemy import Integer, String, Boolean, Date, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, time
from .Database import Base


class Persona(Base):
    __tablename__ = "personas"

    # la primary key hace que no se pueda repetir la id,se identifique cada row como unica, y tambien hace que no se puede dejar el campo en null    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    # unique hace que no se pueda repetir el email, y nullable hace que no se pueda dejar el campo en null
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    #edad se va a calcular en los endpoints de persona, no es necesario que sea un atributo
    # una vez que cancele 5 turnos se deshabilita a la persona
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)

    # esta linea lo que hace es que relaciona turnos con personas
    turnos = relationship("Turno", back_populates="persona", cascade="all, delete-orphan", passive_deletes=True)

class Turno(Base):
    __tablename__ = "turnos"
    #implementa una restricción para que no se puedan crear turnos con la misma fecha y hora
    __table_args__ = (UniqueConstraint("fecha", "hora", name="uq_fecha_hora"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    #evita que se creen turnos con id's de personas inexistentes, si borro la persona tambien tengo que borrar los turnos o nos va a dar error,habria que automatizar que se borren los turnos con las personas
    persona_id: Mapped[int] = mapped_column(Integer, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)

    # lo mismo que la otra linea pero en viceversa 
    persona = relationship("Persona", back_populates="turnos")

    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")

