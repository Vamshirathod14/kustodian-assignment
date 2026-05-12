import os
import asyncpg
from datetime import datetime
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vamshirathod@localhost/kustodian")

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_connection()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            job_id VARCHAR(50) UNIQUE NOT NULL,
            url TEXT NOT NULL,
            goal TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            result JSONB,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS job_logs (
            id SERIAL PRIMARY KEY,
            job_id VARCHAR(50) REFERENCES jobs(job_id),
            event_type VARCHAR(50),
            message TEXT,
            step_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.close()

async def create_job(job_id: str, url: str, goal: str):
    conn = await get_connection()
    await conn.execute(
        "INSERT INTO jobs (job_id, url, goal, status) VALUES ($1, $2, $3, 'pending')",
        job_id, url, goal
    )
    await conn.close()

async def update_job_status(job_id: str, status: str, result: dict = None, error: str = None):
    conn = await get_connection()
    if result:
        await conn.execute(
            "UPDATE jobs SET status = $1, result = $2, updated_at = NOW() WHERE job_id = $3",
            status, json.dumps(result), job_id
        )
    elif error:
        await conn.execute(
            "UPDATE jobs SET status = $1, error = $2, updated_at = NOW() WHERE job_id = $3",
            status, error, job_id
        )
    else:
        await conn.execute(
            "UPDATE jobs SET status = $1, updated_at = NOW() WHERE job_id = $2",
            status, job_id
        )
    await conn.close()

async def add_log(job_id: str, event_type: str, message: str, step_number: int):
    conn = await get_connection()
    await conn.execute(
        "INSERT INTO job_logs (job_id, event_type, message, step_number) VALUES ($1, $2, $3, $4)",
        job_id, event_type, message, step_number
    )
    await conn.close()

async def get_job(job_id: str):
    conn = await get_connection()
    row = await conn.fetchrow("SELECT * FROM jobs WHERE job_id = $1", job_id)
    await conn.close()
    return dict(row) if row else None

async def get_logs(job_id: str):
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM job_logs WHERE job_id = $1 ORDER BY step_number", job_id)
    await conn.close()
    return [dict(row) for row in rows]
