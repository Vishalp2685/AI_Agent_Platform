from sqlalchemy import create_engine
from sqlalchemy.orm import Session,DeclarativeBase,sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=disable"

engine = create_engine(DATABASE_URL,pool_pre_ping=True)

SessionLocal = sessionmaker(bind = engine)

class Base(DeclarativeBase):
    pass

def test_db_connection():
    # Test the connection
    try:
        with engine.connect() as connection:
            print("Connection successful!")
            print("Trying to create the tables in db....")
        Base.metadata.create_all(engine)
        print("Tables created successfully....")
        return True

    except Exception as e:
        print(f"Failed to connect: {e}")
        return False