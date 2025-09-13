from sqlalchemy import Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from Database import Base

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
    # para el tp no importa ya que no va a pasar mucho tiempo, pero lo ideal seria calcular la edad de manera dinamica,
    #pero si lo hago usando una propiedad 'edad' dejaria de ser un atributo de la tabla propiamente dicho, preguntarle al profe
    edad: Mapped[int] = mapped_column(Integer, nullable=False)
    # una vez que cancele 5 turnos se deshabilita a la persona
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)

    # esta linea lo que hace es que relaciona turnos con personas
    turnos = relationship("Turno", back_populates="persona")

class Turno(Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    #evita que se creen turnos con id's de personas inexistentes, si borro la persona tambien tengo que borrar los turnos o nos va a dar error,habria que automatizar que se borren los turnos con las personas
    persona_id: Mapped[int] = mapped_column(Integer, ForeignKey("personas.id"), nullable=False)
    # lo mismo que la otra linea pero en viceversa 
    persona = relationship("Persona", back_populates="turnos")