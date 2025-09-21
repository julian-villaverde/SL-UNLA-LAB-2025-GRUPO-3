from fastapi import FastAPI, HTTPException, Request

from .Database import Base, engine, get_db
from .Models import Turno, Persona
from datetime import date, time, datetime
from email_validator import validate_email, EmailNotValidError

app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def inicio():
    return {"ok": True, "mensaje": "API funcionando"}


@app.on_event("startup")
def al_iniciar() -> None:
    Base.metadata.create_all(bind=engine)



#ABM Turnos
#Faltan validaciones:
#Ingreso de datos(usar pydantic) y reglas de negocio
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


#Personas
#Faltan validaciones

def validar_email(email: str) -> str:
    try:
        valid_email = validate_email(email)
        return valid_email.email  
    except EmailNotValidError as e:
        # Personalizar mensajes en español
        error_msg = str(e).lower()
        if "must have an @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El email debe tener un símbolo @")
        elif "must be something after the @-sign" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: Debe haber algo después del símbolo @")
        elif "domain" in error_msg and "invalid" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: El dominio del email no es válido")
        elif "local part" in error_msg:
            raise HTTPException(status_code=400, detail="email invalido: La parte local del email (antes del @) no es válida")
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


# ABM Personas
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