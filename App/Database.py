from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


URL_BASE_DATOS = "sqlite:///./App/Database.db"


engine = create_engine(URL_BASE_DATOS, echo=True, future=True)
SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

#Acceder a la base de datos
def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()