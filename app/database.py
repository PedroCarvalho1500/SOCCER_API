from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base 
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

engine = create_engine(SQLALCHEMY_DATABASE_URL,pool_size=7, max_overflow=5,pool_pre_ping=True,pool_timeout=30)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()