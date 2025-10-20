from datetime import date, time
from pydantic import BaseModel
from typing import Optional

from .config import ESTADO_PENDIENTE


# Validación de Turnos (Ingreso de datos)
class turno_base(BaseModel):
    persona_id: int
    fecha: date
    hora: time
    estado: Optional[str] = ESTADO_PENDIENTE


class actualizar_turno_base(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[time] = None
    estado: Optional[str] = None

