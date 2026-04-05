-- Cortex Database Schema
-- Google Cloud Gen AI Academy APAC 2026 — Cohort 1 Hackathon

-- ============================================================================
-- USER MEMORY MODEL
-- ============================================================================
-- The persistent memory layer that makes Cortex different from stateless bots.
-- Every interaction can update this — over time Cortex "knows" the user.

CREATE TABLE IF NOT EXISTS user_model (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(50) DEFAULT 'chat' CHECK (source IN ('chat', 'email', 'calendar', 'explicit', 'task')),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast key lookups and JSONB content searches
CREATE INDEX IF NOT EXISTS idx_user_model_key ON user_model(key);
CREATE INDEX IF NOT EXISTS idx_user_model_updated ON user_model(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_model_value ON user_model USING GIN (value);

-- ============================================================================
-- TASKS
-- ============================================================================
-- Task management with priorities and deadlines.

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'blocked', 'done')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    deadline TIMESTAMP,
    project_id INT REFERENCES projects(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);

-- ============================================================================
-- PROJECTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'archived')),
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================================================
-- SESSIONS
-- ============================================================================
-- For tracking conversation continuity across sessions.

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    context JSONB DEFAULT '{}',
    last_interaction TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_last ON sessions(last_interaction DESC);

-- ============================================================================
-- ACTION LOG
-- ============================================================================
-- Full audit trail of all agent actions for transparency and debugging.

CREATE TABLE IF NOT EXISTS action_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    agent VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    payload JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_action_log_session ON action_log(session_id);
CREATE INDEX IF NOT EXISTS idx_action_log_agent ON action_log(agent);
CREATE INDEX IF NOT EXISTS idx_action_log_created ON action_log(created_at DESC);
