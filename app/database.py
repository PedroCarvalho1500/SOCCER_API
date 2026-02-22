from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base 
#from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from .config import settings


def connect_to_db():
    while True:
        try:
            conn = psycopg2.connect(
                dbname="soccer_database",
                user="postgres",
                password="admin",
                host="localhost",
                port="5432",
                cursor_factory=RealDictCursor
            )   

            return conn
        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)    


def get_players_from_db(conn, limit: int = 10, skip: int = 0):
    cursor = conn.cursor()
    #SELECT EVERYTHING EXCEPT PHOTO

    #cursor.execute("SELECT name,position,value FROM players LIMIT %s OFFSET %s", (limit, skip))
    players = cursor.fetchall()
    cursor.close()
    return players

SQLALCHEMY_DATABASE_URL = f"{settings.DATABASE_URL}"

#engine = create_engine(SQLALCHEMY_DATABASE_URL,pool_size=7, max_overflow=5,pool_pre_ping=True,pool_timeout=30, pool_recycle=1800) # Adjust pool settings as needed

engine = create_engine(SQLALCHEMY_DATABASE_URL,    pool_size=5,
   max_overflow=10,
   pool_pre_ping=True,
   pool_timeout=30,
   pool_recycle=1800,) # Adjust pool settings as needed

#engine = create_async_engine(
#    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
#    pool_size=10,
#    max_overflow=20,
#    pool_pre_ping=True,
#)



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#SessionLocal = sessionmaker(
#    engine,
#    expire_on_commit=False,
#    class_=AsyncSession
#)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#async def get_db():
#    async with SessionLocal() as session:
#        yield session