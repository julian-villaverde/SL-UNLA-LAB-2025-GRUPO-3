from fastapi import APIRouter, Response


router = APIRouter(prefix="/personas", tags=["Personas"])


@router.get("/")
def listar_personas():
    return Response(status_code=501)


@router.get("/{id}")
def obtener_persona(id: int):
    return Response(status_code=501)


@router.post("/")
def crear_persona():
    return Response(status_code=501)


@router.put("/{id}")
def modificar_persona(id: int):
    return Response(status_code=501)


@router.delete("/{id}")
def eliminar_persona(id: int):
    return Response(status_code=501)


