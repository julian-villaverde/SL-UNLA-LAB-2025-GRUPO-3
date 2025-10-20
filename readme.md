# Integrantes

- Julian Villaverde
- Agustin Torres Valenzuela
  
# Separación de tareas (Hito 2)
## Julian Villaverde
- Punto E (Endpoints de reportes)
- Documentación postman


### Endpoints (Hito 2)
- GET /reportes/turnos-por-fecha
- GET /reportes/turnos-cancelados-por-mes
- GET /reportes/turnos-por-persona
- GET /reportes/turnos-cancelados
- GET /reportes/turnos-confirmados
- GET /reportes/estado-personas

## Agustin Torres Valenzuela
- Reestructura del proyecto
- Punto D (Endpoints de Estado de Turno)
- Fix punto C (Calculo turnos disponibles)
- Variables de entorno
- Documentación postman

### Endpoints
- PUT /turnos/{turno_id}/cancelar
- PUT /turnos/{turno_id}/confirmar

# Separación de tareas (Hito 1)

## Julian Villaverde
- Creacion de la documentacion y testeo en postman
- Punto A (ABM Personas)

### Endpoints (Hito 1)
- GET / (Verifica funcionamiento de la API) 

- POST /personas
- GET /personas
- GET /personas/{id}
- PUT /personas/{id}
- DELETE /personas/{id} (verificaciones incluidas)

## Agustin Torres Valenzuela
- Punto B (ABM Turnos)
- DER

### Endpoints (Hito 1)
- POST /turnos
- GET /turnos
- GET /turnos/{id}
- PUT /turnos/{id}
- DELETE /turnos/{id}

## Valentin Mesa
- Punto C (Calculo turnos disponibles)

### Endpoints
- GET /turnos-disponibles?fecha=YYYY-MM-DD

## Gabriela Pedicino
- Validaciones (Personas, Turnos) (Julian, Valentin, Agustin)
- Validador de Emails (Julian)
- Reglas de negocio (Turnos) (Agustin)


## Documentacion:
- Coleccion Postman: https://www.postman.com/julianagustinvillaverde-2391323/workspace/grupo03/collection/48509537-0edd7cd0-4238-445c-8c03-a3d3a176fd9f?action=share&creator=48509537
- DER https://drive.google.com/file/d/10Wc69fFGzbVahQCzB7g9bROYeQFTHv13/view?usp=sharing
- videos:https://drive.google.com/drive/folders/1iTqdZDBh8eZlC2myHAEaruq2zYT_QD3v?usp=sharing    
