from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import URL_BASE_DATOS


engine = create_engine(URL_BASE_DATOS, echo=True, future=True)

SesionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()