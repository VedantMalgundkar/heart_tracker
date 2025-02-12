from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")

# Create a temporary connection to PostgreSQL (without specifying the DB)
def create_database():
    try:
        conn = psycopg2.connect(
            dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ Database '{DB_NAME}' created successfully!")
        else:
            print(f"✅ Database '{DB_NAME}' already exists.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error creating database: {e}")

# Call function to ensure DB exists before connecting
create_database()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close() 