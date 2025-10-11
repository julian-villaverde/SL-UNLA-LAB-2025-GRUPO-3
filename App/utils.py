from sqlalchemy import event
from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError

from .models import Turno, Persona
from .database import SesionLocal, engine
from .crud import buscar_persona, buscar_turno

#Acceder a la base de datos
def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()


# hace que funcione ondelete cascade  
@event.listens_for(engine, "connect")
def habilitar_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def validar_turnos_cancelados(db: Session, persona_id: int):

    fecha_actual = date.today()
    fecha_limite = fecha_actual - timedelta(days=180)
    
    # Contar turnos cancelados en los últimos 6 meses
    turnos_cancelados = db.query(Turno).filter(
        Turno.persona_id == persona_id,
        Turno.estado == "cancelado",
        Turno.fecha >= fecha_limite
    ).count()
    

    # Deshabilitar la persona si tiene 5 o más cancelaciones
    if turnos_cancelados >= 5:
        persona = buscar_persona(db, persona_id)
        if persona and persona.habilitado:
            persona.habilitado = False
            db.commit()
        
        raise HTTPException(
            status_code=400,
            detail="No se puede asignar turno: la persona tiene 5 o más turnos cancelados en los últimos 6 meses."
        )


def validar_persona_habilitada(db: Session, persona_id: int):

    persona = buscar_persona(db, persona_id)   
    if not persona.habilitado:
        raise HTTPException(status_code=400, detail="La persona está deshabilitada")
    

def validar_fecha_pasada(fecha_turno: date):

    fecha_actual = date.today()
    if fecha_turno < fecha_actual:
        raise HTTPException(
            status_code=400, 
            detail="No se pueden utilizar fechas anteriores a la fecha actual"
        )
    

def validar_email(email: str):
    try:
        valid_email = validate_email(email)
        return valid_email.email  
    except EmailNotValidError as e:

#los errores por default estan en ingles, aca cambio el idioma
        error_msg = str(e).lower()
        if "must have an @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email debe tener un simbolo @")
        elif "must be something after the @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: Debe haber algo despues del simbolo @")
        elif "domain" in error_msg and "invalid" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El dominio del email no es valido")
        elif "local part" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: La parte local del email (antes del @) no es valida")
        elif "too long" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email es demasiado largo")
        elif "empty" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email no puede estar vacio")
        else:
            raise HTTPException(status_code=400, detail=f"email invalido: {str(e)}")

def calcular_edad(fecha_nacimiento: date):
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad

def validar_fecha_nacimiento(fecha_nacimiento: str):
    hoy = date.today()
    
    if fecha_nacimiento > hoy:
        raise HTTPException(status_code=400, detail="La fecha de nacimiento no puede ser futura")
    
    limite_antiguedad = date(hoy.year - 120, hoy.month, hoy.day)

    if fecha_nacimiento < limite_antiguedad:
        raise HTTPException(status_code=400, detail="La fecha de nacimiento no puede superar 120 años")
    

def validar_formato_fecha(fecha_str:str):
    try:
        date.fromisoformat(fecha_str)  # YYYY-MM-DD
    except (KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Formato esperado YYYY-MM-DD")