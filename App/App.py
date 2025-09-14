from fastapi import FastAPI, HTTPException, Request

from .Database import Base, engine, get_db
from .Models import Turno
from datetime import date, time

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