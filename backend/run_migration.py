import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)

with open("migrations/001_create_tables.sql", "r") as file:
    sql = file.read()

with engine.begin() as conn:
    conn.execute(text(sql))

print("Tables created successfully")