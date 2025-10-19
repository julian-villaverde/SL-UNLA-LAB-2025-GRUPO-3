import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Variables de base de datos (arreglar el espacio)
URL_BASE_DATOS = os.getenv("URL_BASE_DATOS")

# Variables de turnos
HORARIO_INICIO = os.getenv("HORARIO_INICIO")
HORARIO_FIN = os.getenv("HORARIO_FIN")
INTERVALO_TURNOS_MINUTOS = int(os.getenv("INTERVALO_TURNOS_MINUTOS"))
MAX_TURNOS_CANCELADOS = int(os.getenv("MAX_TURNOS_CANCELADOS"))
DIAS_LIMITE_CANCELACIONES = int(os.getenv("DIAS_LIMITE_CANCELACIONES"))

# Variables de personas
MAX_EDAD_PERMITIDA = int(os.getenv("MAX_EDAD_PERMITIDA"))

# Estados de turnos
ESTADO_PENDIENTE = os.getenv("ESTADO_PENDIENTE")
ESTADO_CONFIRMADO = os.getenv("ESTADO_CONFIRMADO")
ESTADO_CANCELADO = os.getenv("ESTADO_CANCELADO")
ESTADO_ASISTIDO = os.getenv("ESTADO_ASISTIDO")