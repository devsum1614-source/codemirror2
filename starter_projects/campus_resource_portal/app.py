"""
Campus Resource Portal - FastAPI Backend Server
Provides API endpoints for campus clubs, equipment, and shared resources.
"""
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
import sqlite3

app = FastAPI(title="Campus Resource Portal")

def get_db():
    conn = sqlite3.connect("campus_portal.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/resources")
def get_resources(category: Optional[str] = None, status: str = "active"):
    # Connects to SQLite and fetches resources
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT r.id, r.title, c.name as category_name, r.status, r.created_at
        FROM resources r
        INNER JOIN categories c ON r.category_id = c.id
        WHERE r.status = ?
    """
    params = [status]
    if category:
        query += " AND LOWER(c.name) = LOWER(?)"
        params.append(category)
        
    query += " ORDER BY r.created_at DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"resources": rows}

@app.post("/api/resources")
def create_resource(data: dict):
    title = (data.get("title") or "").strip()
    if len(title) < 3 or len(title) > 50:
        raise HTTPException(status_code=400, detail="Title length must be between 3 and 50 characters.")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resources (title, category_id, status) VALUES (?, ?, 'active')",
        (title, data.get("category_id", 1))
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "title": title, "status": "active"}
