from datetime import date, time, timedelta, datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from App.schemas import turno_base

from .utils import validar_email, validar_fecha_pasada, validar_formato_fecha, validar_fecha_nacimiento
from .models import Persona, Turno

# ======== ABM Personas ========

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
            # Verificar 5 cancelaciones en los últimos 6 meses antes de deshabilitar
            fecha_actual = date.today()
            fecha_limite = fecha_actual - timedelta(days=180)
            turnos_cancelados = db.query(Turno).filter(
                Turno.persona_id == persona.id,
                Turno.estado == "cancelado",
                Turno.fecha >= fecha_limite
            ).count()
            if turnos_cancelados < 5:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede deshabilitar: la persona no tiene al menos 5 turnos cancelados en los ultimos 6 meses"
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

def validar_turnos_cancelados(db: Session, persona_id: int):
    
    # Contar turnos cancelados en los últimos 6 meses
    turnos_cancelados = contar_turnos_cancelados(db, persona_id, 180)
    

    # Deshabilitar la persona si tiene 5 o más cancelaciones
    if turnos_cancelados >= 5:
        persona = buscar_persona(db, persona_id)
        if persona and persona.habilitado:
            cambiar_estado_persona(db, persona_id)
            return True

    return False


def validar_persona_habilitada(db: Session, persona_id: int):

    persona = buscar_persona(db, persona_id)   
    if not persona.habilitado:
        raise HTTPException(status_code=400, detail="La persona está deshabilitada")

def cambiar_estado_persona(db: Session, persona_id: int):

    persona = buscar_persona(db, persona_id)
    
    # si está habilitada la deshabilita, y viceversa
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


# ======== ABM Turnos ========

def crear_turno(db: Session, turno_data: turno_base):

    persona_id = turno_data.persona_id
    
    validar_persona_habilitada(db, persona_id)

    turnos_cancelados = validar_turnos_cancelados(db, persona_id)
    if turnos_cancelados:
        raise HTTPException(
            status_code=400, 
            detail="No se puede asignar turno: la persona tiene 5 o más turnos cancelados en los últimos 6 meses."
        )
    
    validar_fecha_pasada(turno_data.fecha)
    
    nuevo_turno = Turno(
        persona_id=persona_id,
        fecha=turno_data.fecha,
        hora=turno_data.hora,
        estado=turno_data.estado
    )
    
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)
    
    return nuevo_turno

def listar_turnos(db: Session):
    return db.query(Turno).all()

def actualizar_turno(db: Session, turno_id: int, turno_data: turno_base):

    turno = buscar_turno(db, turno_id)

    if turno_data.fecha is not None:
        turno.fecha = turno_data.fecha
    
    if turno_data.hora is not None:
        turno.hora = turno_data.hora
    
    if turno_data.estado is not None:
        turno.estado = turno_data.estado
    
    db.commit()
    db.refresh(turno)
    
    return turno

def eliminar_turno(db: Session, turno_id: int):

    turno = buscar_turno(db, turno_id)
    db.delete(turno)
    db.commit()


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

def contar_turnos_cancelados(db: Session, persona_id: int, dias_limite: int):

    fecha_actual = date.today()
    fecha_limite = fecha_actual - timedelta(days=dias_limite)

    turnos_cancelados = db.query(Turno).filter(
        Turno.persona_id == persona_id,
        Turno.estado == "cancelado",
        Turno.fecha >= fecha_limite
    ).count()
    
    return turnos_cancelados

def obtener_turnos_por_fecha(db: Session, fecha: date):
    return db.query(Turno).filter(Turno.fecha == fecha).all()


def obtener_turnos_disponibles(db: Session, fecha: date):

    # Generar todos los intervalos de 9:00 a 17:00 cada 30 minutos
    hora_inicio = time(9, 0)
    hora_fin = time(17, 0)
    intervalos = []
    current = datetime.combine(fecha, hora_inicio)
    
    while current.time() <= hora_fin:
        intervalos.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)

    # Consultar los turnos existentes para esa fecha
    turnos_existentes = obtener_turnos_por_fecha(db, fecha)

    # Turnos ocupados (cualquier estado menos cancelado)
    ocupados = [t.hora.strftime("%H:%M") for t in turnos_existentes if t.estado != "cancelado"]

    # Calcular los turnos que están disponibles
    disponibles = []
    for idx, h in enumerate(intervalos):
        if h not in ocupados:
            disponibles.append(h)
        else:
            # Si está ocupado, dejamos disponibles sus adyacentes
            if idx > 0 and intervalos[idx - 1] not in ocupados:
                if intervalos[idx - 1] not in disponibles:
                    disponibles.append(intervalos[idx - 1])
            if idx < len(intervalos) - 1 and intervalos[idx + 1] not in ocupados:
                if intervalos[idx + 1] not in disponibles:
                    disponibles.append(intervalos[idx + 1])

    return sorted(disponibles)