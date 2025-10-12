from datetime import date, time
from pydantic import BaseModel, Field, validator
from typing import Optional


#Validacion de Turnos(Ingreso de datos)
class turno_base(BaseModel):
    persona_id: int = Field(..., gt=0, description="ID de la persona que solicita el turno")
    fecha: date
    hora: time
    estado: Optional[str] = "pendiente"

    @validator("estado")
    def validar_estado(cls, v):
        estados_validos = ["pendiente", "cancelado", "confirmado", "asistido"]
        if v not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        return v

    @validator("hora")
    def validar_horario(cls, v):
        if not (time(9, 0) <= v <= time(17, 0)):
            raise ValueError("La hora debe estar entre 09:00 y 17:00")
        if v.minute not in (0, 30):
            raise ValueError("Los turnos solo pueden ser en intervalos de 30 minutos")
        return v

class actualizar_turno_base(BaseModel):
    fecha: Optional[date]
    hora: Optional[time]
    estado: Optional[str]

    @validator("estado")
    def validar_estado(cls, v):
        if v:
            estados_validos = ["pendiente", "cancelado", "confirmado", "asistido"]
            if v not in estados_validos:
                raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        return v

    @validator("hora")
    def validar_horario(cls, v):
        if v:
            if not (time(9, 0) <= v <= time(17, 0)):
                raise ValueError("La hora debe estar entre 09:00 y 17:00")
            if v.minute not in (0, 30):
                raise ValueError("Los turnos solo pueden ser en intervalos de 30 minutos")
        return v