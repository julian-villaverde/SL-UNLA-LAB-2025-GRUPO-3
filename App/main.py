from fastapi import FastAPI, HTTPException, Request, Depends
from datetime import date, time, datetime, timedelta

from .schemas import turno_base, actualizar_turno
from .crud import verificar_persona_existente
from .database import Base, engine
from .models import Turno, Persona
from .utils import get_db, buscar_persona, buscar_turno, validar_turnos_cancelados, validar_persona_habilitada, validar_fecha_pasada, validar_email, calcular_edad, validar_formato_fecha, validar_fecha_nacimiento


app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def inicio():
    return {"ok": True, "mensaje": "API funcionando"}


@app.on_event("startup")
def al_iniciar():
    Base.metadata.create_all(bind=engine)


# ABM Turnos

@app.post("/turnos")
async def crear_turno(turno_data: turno_base, db = Depends(get_db)):

    persona_id = turno_data.persona_id

    validar_persona_habilitada(db, persona_id)
    validar_turnos_cancelados(db, persona_id)
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
    
    return {
        "id": nuevo_turno.id,
        "persona_id": nuevo_turno.persona_id,
        "fecha": str(nuevo_turno.fecha),
        "hora": str(nuevo_turno.hora),
        "estado": nuevo_turno.estado
    }

@app.get("/turnos")
def listar_turnos(db = Depends(get_db)):
    turnos = db.query(Turno).all()
    return [
        {
            "id": t.id,
            "persona_id": t.persona_id,
            "fecha": str(t.fecha),
            "hora": str(t.hora),
            "estado": t.estado
        }
        for t in turnos
    ]

@app.get("/turnos/{id}")
def obtener_turno(id: int, db = Depends(get_db)):
    turno = buscar_turno(db, id)
    return {
        "id": turno.id,
        "persona_id": turno.persona_id,
        "fecha": str(turno.fecha),
        "hora": str(turno.hora),
        "estado": turno.estado
    }

@app.put("/turnos/{id}")
async def actualizar_turno(id: int, turno_data: actualizar_turno, db = Depends(get_db)):
    turno = buscar_turno(db, id)
    
    if turno_data.fecha is not None:
        # Validar que la fecha no sea pasada
        validar_fecha_pasada(turno_data.fecha)
        turno.fecha = turno_data.fecha
    
    if turno_data.hora is not None:
        turno.hora = turno_data.hora
    
    if turno_data.estado is not None:
        turno.estado = turno_data.estado
    
    db.commit()
    db.refresh(turno)
    
    return {
        "id": turno.id,
        "persona_id": turno.persona_id,
        "fecha": str(turno.fecha),
        "hora": str(turno.hora),
        "estado": turno.estado
    }

@app.delete("/turnos/{id}")
def eliminar_turno(id: int, db = Depends(get_db)):
    turno = buscar_turno(db, id)
    db.delete(turno)
    db.commit()
    return {"ok": True, "mensaje": "Turno eliminado"}


 


# Endpoint - Cálculo de turnos disponibles
@app.get("/turnos-disponibles")
def obtener_turnos_disponibles(fecha: str):
    db = next(get_db())
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    #se generan todos los intervalos de 9:00 a 17:00 cada 30 minutos
    hora_inicio = time(9, 0)
    hora_fin = time(17, 0)
    intervalos = []
    current = datetime.combine(fecha_dt, hora_inicio)
    while current.time() <= hora_fin:
        intervalos.append(current.strftime("%H:%M"))
        current += timedelta(minutes=30)

    #consulta los turnos existentes para esa fecha
    turnos_existentes = db.query(Turno).filter(Turno.fecha == fecha_dt).all()

    #turnos ocupados (cualquier estado menos cancelado)
    ocupados = [t.hora.strftime("%H:%M") for t in turnos_existentes if t.estado != "cancelado"]

    #hacemos el cálculo de los turnos que estan disponibles
    disponibles = []
    for idx, h in enumerate(intervalos):
        if h not in ocupados:
            disponibles.append(h)
        else:
            #si está ocupado, dejamos disponibles sus adyacentes
            if idx > 0 and intervalos[idx - 1] not in ocupados:
                if intervalos[idx - 1] not in disponibles:
                    disponibles.append(intervalos[idx - 1])
            if idx < len(intervalos) - 1 and intervalos[idx + 1] not in ocupados:
                if intervalos[idx + 1] not in disponibles:
                    disponibles.append(intervalos[idx + 1])

    #respuesta del Endpoint
    return {
        "fecha": fecha,
        "horarios_disponibles": sorted(disponibles)
    } 


# ABM Personas

@app.post("/personas")
async def crear_persona(request: Request):
    datos = await request.json()
    db = next(get_db())

    email_normalizado = validar_email(datos["email"])
    verificar_persona_existente(db, email_normalizado, datos["dni"], datos["telefono"])

    # Validar fecha de nacimiento
    validar_formato_fecha(datos["fecha_nacimiento"])

    # Reglas adicionales: no futura y no mayor a 120 años
    validar_fecha_nacimiento(datos["fecha_nacimiento"])

    nueva_persona = Persona(
        nombre=datos["nombre"],
        email=email_normalizado,
        dni=datos["dni"],
        telefono=datos["telefono"],
        fecha_nacimiento=datos["fecha_nacimiento"],
        # Siempre por defecto habilitado 
        habilitado=True
    )
    
    db.add(nueva_persona)
    db.commit()
    db.refresh(nueva_persona)
    
    edad = calcular_edad(nueva_persona.fecha_nacimiento)
    
    return {
        "id": nueva_persona.id,
        "nombre": nueva_persona.nombre,
        "email": nueva_persona.email,
        "dni": nueva_persona.dni,
        "telefono": nueva_persona.telefono,
        "fecha_nacimiento": str(nueva_persona.fecha_nacimiento),
        "edad": edad,
        "habilitado": nueva_persona.habilitado
    }


@app.get("/personas")
def listar_personas():
    db = next(get_db())
    personas = db.query(Persona).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "email": p.email,
            "dni": p.dni,
            "telefono": p.telefono,
            "fecha_nacimiento": str(p.fecha_nacimiento),
            "edad": calcular_edad(p.fecha_nacimiento),
            "habilitado": p.habilitado
        }
        for p in personas
    ]


@app.get("/personas/{id}")
def obtener_persona(id: int):
    db = next(get_db())
    persona = buscar_persona(db, id)
    
    edad = calcular_edad(persona.fecha_nacimiento)
    
    return {
        "id": persona.id,
        "nombre": persona.nombre,
        "email": persona.email,
        "dni": persona.dni,
        "telefono": persona.telefono,
        "fecha_nacimiento": str(persona.fecha_nacimiento),
        "edad": edad,
        "habilitado": persona.habilitado
    }


@app.put("/personas/{id}")
async def actualizar_persona(id: int, request: Request):
    datos = await request.json()
    db = next(get_db())
    persona = buscar_persona(db, id)
    if "dni" in datos:
        raise HTTPException(status_code=400, detail="No se permite modificar el DNI de una persona")
    if "fecha_nacimiento" in datos:
        raise HTTPException(status_code=400, detail="No se permite modificar la fecha de nacimiento de una persona")
    
    
    email_normalizado = None
    if "email" in datos:
        email_normalizado = validar_email(datos["email"])

    # Verifico si el email, DNI o telefono ya existen en otra persona
    if "email" in datos or "dni" in datos or "telefono" in datos:
        email = email_normalizado if email_normalizado else persona.email
        dni = datos.get("dni", persona.dni)
        telefono = datos.get("telefono", persona.telefono)

        persona_existente = db.query(Persona).filter(
            Persona.id != id,
            ((Persona.email == email) | (Persona.dni == dni) | (Persona.telefono == telefono))
        ).first()

        if persona_existente:
            raise HTTPException(status_code=400, detail="Ya existe otra persona con este email, DNI o telefono")

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
    
    edad = calcular_edad(persona.fecha_nacimiento)
    
    return {
        "id": persona.id,
        "nombre": persona.nombre,
        "email": persona.email,
        "dni": persona.dni,
        "telefono": persona.telefono,
        "fecha_nacimiento": str(persona.fecha_nacimiento),
        "edad": edad,
        "habilitado": persona.habilitado
    }


@app.delete("/personas/{id}")
def eliminar_persona(id: int):
    db = next(get_db())
    persona = buscar_persona(db, id)

    db.delete(persona)
    db.commit()
    return {"ok": True, "mensaje": "Persona eliminada"}
