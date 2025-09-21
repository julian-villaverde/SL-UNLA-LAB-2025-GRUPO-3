from fastapi import FastAPI, HTTPException, Request
from .Database import Base, engine, get_db
from .Models import Turno, Persona
from datetime import date, time, datetime, timedelta
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, Field, validator
from typing import Optional


app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def inicio():
    return {"ok": True, "mensaje": "API funcionando"}


@app.on_event("startup")
def al_iniciar() -> None:
    Base.metadata.create_all(bind=engine)


# ABM Turnos
#Faltan validaciones:
#Ingreso de datos(usar pydantic) y reglas de negocio

#Validacion de Turnos(Ingreso de datos)
class turno_base(BaseModel):
    persona_id: int = Field(..., gt=0, description="ID de la persona que solicita el turno")
    fecha: date
    hora: time
    estado: Optional[str] = "pendiente"

    @validador("estado")
    def validar_estado(cls, v):
        estados_validos = ["pendiente", "cancelado", "confirmado", "asistido"]
        if v not in estados_validos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        return v

    @validador("hora")
    def validar_horario(cls, v):
        if not (time(9, 0) <= v <= time(17, 0)):
            raise ValueError("La hora debe estar entre 09:00 y 17:00")
        if v.minute not in (0, 30):
            raise ValueError("Los turnos solo pueden ser en intervalos de 30 minutos")
        return v

class actualizar_turno(BaseModel):
    fecha: Optional[date]
    hora: Optional[time]
    estado: Optional[str]

    @validador("estado")
    def validar_estado(cls, v):
        if v:
            estados_validos = ["pendiente", "cancelado", "confirmado", "asistido"]
            if v not in estados_validos:
                raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        return v

    @validador("hora")
    def validar_horario(cls, v):
        if v:
            if not (time(9, 0) <= v <= time(17, 0)):
                raise ValueError("La hora debe estar entre 09:00 y 17:00")
            if v.minute not in (0, 30):
                raise ValueError("Los turnos solo pueden ser en intervalos de 30 minutos")
        return v


@app.post("/turnos")
async def crear_turno(request: Request):
    datos = await request.json()
    db = next(get_db())
    nuevo_turno = Turno(
        persona_id=datos["persona_id"],
        fecha=date.fromisoformat(datos["fecha"]),
        hora=time.fromisoformat(datos["hora"])
        # estado definido como default "pendiente" en models.py
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
def listar_turnos():
    db = next(get_db())
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
def obtener_turno(id: int):
    db = next(get_db())
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {
        "id": turno.id,
        "persona_id": turno.persona_id,
        "fecha": str(turno.fecha),
        "hora": str(turno.hora),
        "estado": turno.estado
    }

@app.put("/turnos/{id}")
async def actualizar_turno(id: int, request: Request):
    datos = await request.json()
    db = next(get_db())
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    turno.persona_id = datos["persona_id"]
    turno.fecha = date.fromisoformat(datos["fecha"])
    turno.hora = time.fromisoformat(datos["hora"])
    turno.estado = datos["estado"]
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
def eliminar_turno(id: int):
    db = next(get_db())
    turno = db.query(Turno).filter(Turno.id == id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
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
#Faltan validaciones

def validar_email(email: str) -> str:
    try:
        valid_email = validate_email(email)
        return valid_email.email  
    except EmailNotValidError as e:

#los errores por default estan en ingles, aca cambio el idioma
        error_msg = str(e).lower()
        if "must have an @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email debe tener un simbolo @")
        elif "must be something after the @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: Debe haber algo después del simbolo @")
        elif "domain" in error_msg and "invalid" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El dominio del email no es valido")
        elif "local part" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: La parte local del email (antes del @) no es valida")
        elif "too long" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email es demasiado largo")
        elif "empty" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email no puede estar vacío")
        else:
            raise HTTPException(status_code=400, detail=f"email invalido: {str(e)}")

def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad


@app.post("/personas")
async def crear_persona(request: Request):
    datos = await request.json()
    db = next(get_db())

    # Validar y normalizar email
    email_normalizado = validar_email(datos["email"])

    # me fijo si ya existe una persona con el mismo email o DNI
    persona_existente = db.query(Persona).filter(
        (Persona.email == email_normalizado) | (Persona.dni == datos["dni"])
    ).first()

    if persona_existente:
        raise HTTPException(status_code=400, detail="Ya existe una persona con este email o DNI")

    nueva_persona = Persona(
        nombre=datos["nombre"],
        email=email_normalizado,
        dni=datos["dni"],
        telefono=datos["telefono"],
        fecha_nacimiento=date.fromisoformat(datos["fecha_nacimiento"]),
        habilitado=datos.get("habilitado", True)  # Por defecto habilitado
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
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
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
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    # Validar email si se está actualizando
    email_normalizado = None
    if "email" in datos:
        email_normalizado = validar_email(datos["email"])

    # Verificar si el email o DNI ya existen en otra persona
    if "email" in datos or "dni" in datos:
        email = email_normalizado if email_normalizado else persona.email
        dni = datos.get("dni", persona.dni)

        persona_existente = db.query(Persona).filter(
            Persona.id != id,
            ((Persona.email == email) | (Persona.dni == dni))
        ).first()

        if persona_existente:
            raise HTTPException(status_code=400, detail="Ya existe otra persona con este email o DNI")

    # Actualizar campos
    if "nombre" in datos:
        persona.nombre = datos["nombre"]
    if "email" in datos:
        persona.email = email_normalizado
    if "dni" in datos:
        persona.dni = datos["dni"]
    if "telefono" in datos:
        persona.telefono = datos["telefono"]
    if "fecha_nacimiento" in datos:
        persona.fecha_nacimiento = date.fromisoformat(datos["fecha_nacimiento"])
    if "habilitado" in datos:
        persona.habilitado = datos["habilitado"]
    
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
    persona = db.query(Persona).filter(Persona.id == id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    db.delete(persona)
    db.commit()
    return {"ok": True, "mensaje": "Persona eliminada"}
