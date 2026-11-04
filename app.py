import os
import time
import psycopg2
from fastapi import FastAPI

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "secret"),
    "dbname": os.getenv("DB_NAME", "postgres"),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.on_event("startup")
def init_db():
    # база может быть ещё не готова: пробуем несколько раз
    for attempt in range(10):
        try:
            conn = get_connection()
            break
        except psycopg2.OperationalError:
            print(f"DB not ready, retry {attempt + 1}/10")
            time.sleep(2)
    else:
        raise RuntimeError("Could not connect to DB")
    with conn, conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id SERIAL PRIMARY KEY, text TEXT NOT NULL)"
        )
    conn.close()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/notes")
def add_note(text: str):
    conn = get_connection()
    with conn, conn.cursor() as cur:
        cur.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id", (text,))
        note_id = cur.fetchone()[0]
    conn.close()
    return {"id": note_id, "text": text}

@app.get("/notes")
def list_notes():
    conn = get_connection()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT id, text FROM notes ORDER BY id")
        rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1]} for r in rows]