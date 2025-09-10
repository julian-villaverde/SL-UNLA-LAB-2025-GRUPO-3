from fastapi import FastAPI


app = FastAPI(title="SL-UNLA-LAB-2025-GRUPO-03-API")


@app.get("/")
def root():
    return {"ok": True}


# Base de datos
from app.core.database import Base, engine  # noqa: E402


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


