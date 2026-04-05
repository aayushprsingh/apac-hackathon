"""
PostgreSQL Database Tools for Cortex
Provides tools for memory, tasks, projects, sessions, and action logging
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Any, Optional
from datetime import datetime

# Database connection parameters from environment
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "cortex"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# =============================================================================
# MEMORY TOOLS
# =============================================================================


def memory_get(key: str) -> dict:
    """
    Retrieve a value from the user's persistent memory model.
    
    Args:
        key: The memory key (e.g., 'rahul_context', 'current_project', 'working_hours')
    
    Returns:
        dict with key, value, confidence, source, updated_at
        Returns None if key not found.
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT key, value, confidence, source, updated_at FROM user_model WHERE key = %s",
                    (key,)
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None
    finally:
        conn.close()


def memory_put(key: str, value: dict, confidence: float = 1.0, source: str = "chat") -> dict:
    """
    Store or update a value in the user's persistent memory model.
    
    Args:
        key: The memory key
        value: The value to store (will be JSON serialized)
        confidence: How confident we are (0.0 to 1.0)
        source: Where this came from ('chat', 'email', 'calendar', 'explicit')
    
    Returns:
        dict with the stored record
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Upsert (insert or update on conflict)
                cur.execute("""
                    INSERT INTO user_model (key, value, confidence, source, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        confidence = EXCLUDED.confidence,
                        source = EXCLUDED.source,
                        updated_at = NOW()
                    RETURNING key, value, confidence, source, updated_at
                """, (key, json.dumps(value), confidence, source))
                row = cur.fetchone()
                return dict(row)
    finally:
        conn.close()


def memory_search(query: str, limit: int = 10) -> list:
    """
    Search memory for keys/values matching a query.
    Searches both keys and JSON value content.
    
    Args:
        query: Search string
        limit: Max results to return
    
    Returns:
        list of matching memory records
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                search_pattern = f"%{query}%"
                cur.execute("""
                    SELECT key, value, confidence, source, updated_at
                    FROM user_model
                    WHERE key ILIKE %s OR value::text ILIKE %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (search_pattern, search_pattern, limit))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    finally:
        conn.close()


def memory_list_all(limit: int = 50) -> list:
    """List all memory entries, most recent first."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT key, value, confidence, source, updated_at
                    FROM user_model
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    finally:
        conn.close()


def memory_delete(key: str) -> bool:
    """Delete a memory entry. Returns True if deleted."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_model WHERE key = %s RETURNING key", (key,))
                deleted = cur.fetchone() is not None
                return deleted
    finally:
        conn.close()


# =============================================================================
# TASK TOOLS
# =============================================================================


def task_create(title: str, description: str = "", priority: str = "medium",
                deadline: str = None, project_id: int = None) -> dict:
    """
    Create a new task.
    
    Args:
        title: Task title
        description: Optional description
        priority: 'low', 'medium', 'high', 'urgent'
        deadline: ISO timestamp for deadline
        project_id: Optional linked project ID
    
    Returns:
        dict with the created task
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tasks (title, description, priority, deadline, project_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, title, description, status, priority, deadline, project_id, created_at
                """, (title, description, priority, deadline, project_id))
                row = cur.fetchone()
                return dict(row)
    finally:
        conn.close()


def task_get(task_id: int) -> dict:
    """Get a task by ID."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, description, status, priority, deadline, project_id, created_at, updated_at
                    FROM tasks WHERE id = %s
                """, (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()


def task_list(status: str = None, priority: str = None, limit: int = 20) -> list:
    """
    List tasks with optional filters.
    
    Args:
        status: Filter by status ('pending', 'in_progress', 'blocked', 'done')
        priority: Filter by priority ('low', 'medium', 'high', 'urgent')
        limit: Max results
    
    Returns:
        list of tasks
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM tasks WHERE 1=1"
                params = []
                if status:
                    query += " AND status = %s"
                    params.append(status)
                if priority:
                    query += " AND priority = %s"
                    params.append(priority)
                query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC LIMIT %s"
                params.append(limit)
                cur.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    finally:
        conn.close()


def task_update(task_id: int, status: str = None, title: str = None,
                 description: str = None, priority: str = None) -> dict:
    """Update a task."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                updates = []
                params = []
                if status:
                    updates.append("status = %s")
                    params.append(status)
                if title:
                    updates.append("title = %s")
                    params.append(title)
                if description is not None:
                    updates.append("description = %s")
                    params.append(description)
                if priority:
                    updates.append("priority = %s")
                    params.append(priority)
                updates.append("updated_at = NOW()")
                params.append(task_id)
                
                cur.execute(f"""
                    UPDATE tasks SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id, title, description, status, priority, deadline, project_id, created_at, updated_at
                """, params)
                row = cur.fetchone()
                return dict(row) if row else None
    finally:
        conn.close()


def task_delete(task_id: int) -> bool:
    """Delete a task. Returns True if deleted."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
                return cur.fetchone() is not None
    finally:
        conn.close()


# =============================================================================
# PROJECT TOOLS
# =============================================================================


def project_create(name: str, description: str = "", deadline: str = None) -> dict:
    """Create a new project."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO projects (name, description, deadline)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, description, status, deadline, created_at
                """, (name, description, deadline))
                row = cur.fetchone()
                return dict(row)
    finally:
        conn.close()


def project_list(status: str = None, limit: int = 20) -> list:
    """List projects."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                if status:
                    cur.execute("SELECT * FROM projects WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                               (status, limit))
                else:
                    cur.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT %s", (limit,))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    finally:
        conn.close()


# =============================================================================
# ACTION LOG TOOLS
# =============================================================================


def log_action(session_id: str, agent: str, action: str,
               payload: dict = None, result: dict = None) -> dict:
    """
    Log an agent action for audit trail.
    
    Args:
        session_id: Current session identifier
        agent: Which agent acted (e.g., 'memory', 'email', 'scheduler')
        action: Action type (e.g., 'memory_get', 'email_sent', 'task_created')
        payload: What the agent received as input
        result: What the agent produced as output
    
    Returns:
        dict with the log entry
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO action_log (session_id, agent, action, payload, result)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, session_id, agent, action, created_at
                """, (session_id, json.dumps(payload) if payload else None,
                      agent, action, json.dumps(result) if result else None))
                row = cur.fetchone()
                return dict(row)
    finally:
        conn.close()


def get_session_history(session_id: str, limit: int = 20) -> list:
    """Get action history for a session."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM action_log
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (session_id, limit))
                rows = cur.fetchall()
                return [dict(row) for row in rows]
    finally:
        conn.close()
