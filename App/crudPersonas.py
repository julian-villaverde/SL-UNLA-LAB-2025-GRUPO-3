from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session


from .utils import validar_email, validar_formato_fecha, validar_fecha_nacimiento
from .models import Persona, Turno
from .config import MAX_TURNOS_CANCELADOS, DIAS_LIMITE_CANCELACIONES, ESTADO_CANCELADO


def crear_persona(db: Session, datos: dict):
    # Validar email
    email_normalizado = validar_email(datos["email"])
    
    # Verificar que no exista otra persona con los mismos datos
    verificar_persona_existente(db, email_normalizado, datos["dni"], datos["telefono"])

    # Validar fecha de nacimiento
    validar_formato_fecha(datos["fecha_nacimiento"])
    validar_fecha_nacimiento(date.fromisoformat(datos["fecha_nacimiento"]))

    # Crear persona
    nueva_persona = Persona(
        nombre=datos["nombre"],
        email=email_normalizado,
        dni=datos["dni"],
        telefono=datos["telefono"],
        fecha_nacimiento=date.fromisoformat(datos["fecha_nacimiento"]),
        habilitado=True
    )
    
    db.add(nueva_persona)
    db.commit()
    db.refresh(nueva_persona)
    
    return nueva_persona

def obtener_todas_personas(db: Session):
    return db.query(Persona).all()


def actualizar_persona(db: Session, persona_id: int, datos: dict):
    persona = buscar_persona(db, persona_id)
    
    if "dni" in datos:
        raise HTTPException(status_code=400, detail="No se permite modificar el DNI de una persona")
    if "fecha_nacimiento" in datos:
        raise HTTPException(status_code=400, detail="No se permite modificar la fecha de nacimiento de una persona")
    
    email_normalizado = None
    if "email" in datos:
        email_normalizado = validar_email(datos["email"])

    # Verificar duplicados si se están actualizando campos únicos
    if "email" in datos or "telefono" in datos:
        email = email_normalizado if email_normalizado else persona.email
        telefono = datos.get("telefono", persona.telefono)
        
        persona_existente = db.query(Persona).filter(
            Persona.id != persona_id,
            ((Persona.email == email) | (Persona.telefono == telefono))
        ).first()

        if persona_existente:
            raise HTTPException(status_code=400, detail="Ya existe otra persona con este email o teléfono")

    # actualizar campos
    if "nombre" in datos:
        persona.nombre = datos["nombre"]
    if "email" in datos:
        persona.email = email_normalizado
    if "dni" in datos:
        persona.dni = datos["dni"]
    if "telefono" in datos:
        persona.telefono = datos["telefono"]
    
    if "habilitado" in datos:
        nuevo_estado_habilitado = datos["habilitado"]
        if nuevo_estado_habilitado is False:
            # Verificar 5 cancelaciones en los ultimos 6 meses antes de deshabilitar
            fecha_actual = date.today()
            fecha_limite = fecha_actual - timedelta(days=DIAS_LIMITE_CANCELACIONES)
            turnos_cancelados = db.query(Turno).filter(
                Turno.persona_id == persona.id,
                Turno.estado == ESTADO_CANCELADO,
                Turno.fecha >= fecha_limite
            ).count()
            if turnos_cancelados < MAX_TURNOS_CANCELADOS:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se puede deshabilitar: la persona no tiene al menos {MAX_TURNOS_CANCELADOS} turnos cancelados en los ultimos 6 meses"
                )
        persona.habilitado = nuevo_estado_habilitado
    
    db.commit()
    db.refresh(persona)
    return persona


def buscar_persona(db: Session, persona_id: int):

    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    return persona


def validar_persona_habilitada(db: Session, persona_id: int):

    persona = buscar_persona(db, persona_id)   
    if not persona.habilitado:
        raise HTTPException(status_code=400, detail="La persona está deshabilitada")

def cambiar_estado_persona(db: Session, persona_id: int):

    persona = buscar_persona(db, persona_id)
    
    # si esta habilitada la deshabilita, y viceversa
    persona.habilitado = not persona.habilitado
    
    db.commit()
    db.refresh(persona)


def verificar_persona_existente(db: Session, email: str, dni: str, telefono: str):


    persona_existente = db.query(Persona).filter(
        (Persona.email == email) | 
        (Persona.dni == dni) | 
        (Persona.telefono == telefono)
    ).first()
    
    if persona_existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con este email, DNI o telefono")
