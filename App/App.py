from fastapi import FastAPI

from .Database import Base, engine


app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def inicio():
    return {"ok": True, "mensaje": "API funcionando"}


@app.on_event("startup")
def al_iniciar() -> None:
    Base.metadata.create_all(bind=engine)
