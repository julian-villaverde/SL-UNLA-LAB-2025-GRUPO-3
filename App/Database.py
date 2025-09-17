from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


URL_BASE_DATOS = "sqlite:///./App/Database.db"


engine = create_engine(URL_BASE_DATOS, echo=True, future=True)

# hace que funcione ondelete cascade  
@event.listens_for(engine, "connect")
def habilitar_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

#Acceder a la base de datos
def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()