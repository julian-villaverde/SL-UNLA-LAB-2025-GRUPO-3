from datetime import date
from fastapi import FastAPI, Request, Depends

from .schemas import actualizar_turno_base, turno_base
from .crudPersonas import  obtener_todas_personas, crear_persona, actualizar_persona, buscar_persona
from .crudTurnos import cancelar_turno, confirmar_turno, crear_turno, eliminar_turno, listar_turnos, actualizar_turno, buscar_turno, obtener_turnos_disponibles
from .database import Base, engine
from .utils import get_db, calcular_edad, validar_formato_fecha


app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def inicio():
    return {"ok": True, "mensaje": "API funcionando"}


@app.on_event("startup")
def al_iniciar():
    Base.metadata.create_all(bind=engine)


# Endpoints Turnos
@app.post("/turnos")
def crear_turno_endpoint(turno_data: turno_base, db = Depends(get_db)):

    nuevo_turno = crear_turno(db, turno_data)

    return {
        "id": nuevo_turno.id,
        "persona_id": nuevo_turno.persona_id,
        "fecha": str(nuevo_turno.fecha),
        "hora": str(nuevo_turno.hora),
        "estado": nuevo_turno.estado
    }

@app.get("/turnos")
def listar_turnos_endpoint(db = Depends(get_db)):

    turnos = listar_turnos(db)

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
async def actualizar_turno_endpoint(id: int, turno_data: actualizar_turno_base, db = Depends(get_db)):
    
    turno = actualizar_turno(db, id, turno_data)
    
    return {
        "id": turno.id,
        "persona_id": turno.persona_id,
        "fecha": str(turno.fecha),
        "hora": str(turno.hora),
        "estado": turno.estado
    }

@app.delete("/turnos/{id}")

def eliminar_turno_endpoint(id: int, db = Depends(get_db)):

    eliminar_turno(db, id)

    return {"ok": True, "mensaje": "Turno eliminado"}



# Endpoint - Cálculo de turnos disponibles
@app.get("/turnos-disponibles")
def obtener_turnos_disponibles_endpoint(fecha: str):
    db = next(get_db())

    validar_formato_fecha(fecha)    
    turnos_disponibles = obtener_turnos_disponibles(db, date.fromisoformat(fecha))

    #respuesta del Endpoint
    return {
        "fecha": fecha,
        "horarios_disponibles": turnos_disponibles
    } 

@app.put("/turnos/{turno_id}/cancelar")
def cancelar_turno_endpoint(turno_id: int, db = Depends(get_db)):
    
    turno_cancelado = cancelar_turno(db, turno_id)
        
    return {
        "id": turno_cancelado.id,
        "fecha": turno_cancelado.fecha.strftime("%Y-%m-%d"),
        "hora": turno_cancelado.hora.strftime("%H:%M"),
        "estado": turno_cancelado.estado
    }
    

@app.put("/turnos/{turno_id}/confirmar")
def confirmar_turno_endpoint(turno_id: int, db = Depends(get_db)):
        
    turno_confirmado = confirmar_turno(db, turno_id)
    
    return {
        "id": turno_confirmado.id,
        "fecha": turno_confirmado.fecha.strftime("%Y-%m-%d"),
        "hora": turno_confirmado.hora.strftime("%H:%M"),
        "estado": turno_confirmado.estado
    }


# Endpoints Personas

@app.post("/personas")
async def crear_persona_endpoint(request: Request):
    datos = await request.json()
    db = next(get_db())

    nueva_persona = crear_persona(db, datos)
    
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
    personas = obtener_todas_personas(db)
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
async def actualizar_persona_endpoint(id: int, request: Request):
    datos = await request.json()
    db = next(get_db())
    persona = actualizar_persona(db, id, datos)
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
