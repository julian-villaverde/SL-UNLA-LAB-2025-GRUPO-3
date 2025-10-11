from fastapi import HTTPException
from sqlalchemy.orm import Session

from .utils import validar_fecha_pasada
from .models import Persona, Turno


def buscar_persona(db: Session, persona_id: int):

    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    return persona

def buscar_turno(db: Session, turno_id: int):

    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    return turno


def cancelar_turno(db: Session, turno_id: int):
    turno = buscar_turno(db, turno_id)
    
    if turno.estado == "cancelado":
        raise HTTPException(
            status_code=400, 
            detail="El turno ya está cancelado"
        )
    
    validar_fecha_pasada(turno.fecha)
    
    turno.estado = "cancelado"
    db.commit()
    db.refresh(turno)

# ...existing code...

def verificar_persona_existente(db: Session, email: str, dni: str, telefono: str):


    persona_existente = db.query(Persona).filter(
        (Persona.email == email) | 
        (Persona.dni == dni) | 
        (Persona.telefono == telefono)
    ).first()
    
        
    if persona_existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con este email, DNI o telefono")




# ...existing code...