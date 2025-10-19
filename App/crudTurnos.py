from datetime import date, time, timedelta, datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from App.schemas import turno_base

from .utils import validar_fecha_pasada, validar_turno_modificable
from .crudPersonas import validar_persona_habilitada, buscar_persona, cambiar_estado_persona
from .models import Turno
from .config import HORARIO_INICIO, HORARIO_FIN, INTERVALO_TURNOS_MINUTOS, MAX_TURNOS_CANCELADOS, DIAS_LIMITE_CANCELACIONES, ESTADO_PENDIENTE, ESTADO_CONFIRMADO, ESTADO_CANCELADO, ESTADO_ASISTIDO


def crear_turno(db: Session, turno_data: turno_base):

    persona_id = turno_data.persona_id
    
    validar_persona_habilitada(db, persona_id)

    turnos_cancelados = validar_turnos_cancelados(db, persona_id)
    if turnos_cancelados:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede asignar turno: la persona tiene {MAX_TURNOS_CANCELADOS} o más turnos cancelados en los últimos 6 meses."
        )
    
    validar_fecha_pasada(turno_data.fecha)

    horarios_disponibles = obtener_turnos_disponibles(db, turno_data.fecha)
    hora_solicitada = turno_data.hora.strftime("%H:%M")

    print(f"🔍 Hora solicitada: {hora_solicitada}")
    print(f"🔍 Horarios disponibles: {horarios_disponibles}")
    
    if hora_solicitada not in horarios_disponibles:
        raise HTTPException(
            status_code=400, 
            detail=f"El horario {hora_solicitada} del día {turno_data.fecha} no está disponible"
        )
    
    
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
    
    validar_turno_modificable(turno)

    if turno_data.fecha is not None:
        validar_fecha_pasada(turno_data.fecha)
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
    
    validar_turno_modificable(turno)
    
    validar_fecha_pasada(turno.fecha)
    
    turno.estado = ESTADO_CANCELADO
    db.commit()
    db.refresh(turno)

    return turno
    

def contar_turnos_cancelados(db: Session, persona_id: int, dias_limite: int):

    fecha_actual = date.today()
    fecha_limite = fecha_actual - timedelta(days=dias_limite)

    turnos_cancelados = db.query(Turno).filter(
        Turno.persona_id == persona_id,
        Turno.estado == ESTADO_CANCELADO,
        Turno.fecha >= fecha_limite
    ).count()
    
    return turnos_cancelados

def obtener_turnos_por_fecha(db: Session, fecha: date):
    return db.query(Turno).filter(Turno.fecha == fecha).all()


def obtener_turnos_disponibles(db: Session, fecha: date):
    
    validar_fecha_pasada(fecha)
    
    horarios_posibles = []
    hora_actual = time.fromisoformat(HORARIO_INICIO) 
    hora_limite = time.fromisoformat(HORARIO_FIN)

    while hora_actual <= hora_limite:
        horarios_posibles.append(hora_actual)
        
        datetime_temp = datetime.combine(fecha, hora_actual) + timedelta(minutes=INTERVALO_TURNOS_MINUTOS)
        hora_actual = datetime_temp.time()
        
    turnos_ocupados = db.query(Turno.hora).filter(
        Turno.fecha == fecha,
        Turno.estado != ESTADO_CANCELADO
    ).all()
    
    horas_ocupadas = {turno.hora for turno in turnos_ocupados}
    
    return [
        hora.strftime("%H:%M") 
        for hora in horarios_posibles 
        if hora not in horas_ocupadas
    ]


def validar_turnos_cancelados(db: Session, persona_id: int):
    
    turnos_cancelados = contar_turnos_cancelados(db, persona_id, DIAS_LIMITE_CANCELACIONES)

    # Deshabilitar la persona si tiene 5 o más cancelaciones
    if turnos_cancelados >= MAX_TURNOS_CANCELADOS:
        persona = buscar_persona(db, persona_id)
        if persona and persona.habilitado:
            cambiar_estado_persona(db, persona_id)
            return True

    return False


def confirmar_turno(db: Session, turno_id: int):
    
    turno = buscar_turno(db, turno_id)
    
    validar_turno_modificable(turno)
    
    if turno.estado != ESTADO_PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden confirmar turnos pendientes"
        )
    
    turno.estado = ESTADO_CONFIRMADO
    db.commit()
    db.refresh(turno)
    
    return turno


def marcar_asistencia_turno(db: Session, turno_id: int):
    
    turno = buscar_turno(db, turno_id)

    if turno.estado != ESTADO_CONFIRMADO:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede marcar asistencia en turnos confirmados"
        )
    
    turno.estado = ESTADO_ASISTIDO
    db.commit()
    db.refresh(turno)
    
    return turno