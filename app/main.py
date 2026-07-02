import os
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# ---------------------------------------------------------------------------
# Logging setup — structured, goes to stdout so Docker/NGINX/host can capture it
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Config from environment variables (never hardcode secrets)
# ---------------------------------------------------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "appdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "appuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changeme")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")


def get_db_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        cursor_factory=RealDictCursor,
        connect_timeout=3,
    )


def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=3,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create a simple table if it doesn't exist
    logger.info("Starting up application...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
    yield
    logger.info("Shutting down application...")


app = FastAPI(title="AI Deploy Assignment API", lifespan=lifespan)


class Item(BaseModel):
    name: str


# ---------------------------------------------------------------------------
# Health check endpoint — used by Docker HEALTHCHECK, NGINX, and CI/CD
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    status = {"status": "ok", "checks": {}}

    # Check Postgres
    try:
        conn = get_db_connection()
        conn.close()
        status["checks"]["postgres"] = "ok"
    except Exception as e:
        status["checks"]["postgres"] = f"error: {e}"
        status["status"] = "degraded"

    # Check Redis
    try:
        r = get_redis_client()
        r.ping()
        status["checks"]["redis"] = "ok"
    except Exception as e:
        status["checks"]["redis"] = f"error: {e}"
        status["status"] = "degraded"

    if status["status"] != "ok":
        raise HTTPException(status_code=503, detail=status)

    return status


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "AI Deploy Assignment API is running"}


@app.post("/items")
def create_item(item: Item):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO items (name) VALUES (%s) RETURNING id, name, created_at;", (item.name,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    # Cache-aside example with Redis
    r = get_redis_client()
    r.set(f"item:{row['id']}", item.name, ex=3600)

    logger.info(f"Created item {row['id']}")
    return row


@app.get("/items/{item_id}")
def get_item(item_id: int):
    r = get_redis_client()
    cached = r.get(f"item:{item_id}")
    if cached:
        logger.info(f"Cache hit for item {item_id}")
        return {"id": item_id, "name": cached, "source": "cache"}

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM items WHERE id = %s;", (item_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    r.set(f"item:{item_id}", row["name"], ex=3600)
    logger.info(f"Cache miss for item {item_id}, loaded from DB")
    return {**row, "source": "db"}
