-- Enterprise QA Assistant - Database Initialization Script
-- PostgreSQL 16

-- ============================================================
-- Conversation Sessions Table
-- ============================================================
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id              VARCHAR(64) PRIMARY KEY,
    user_id         VARCHAR(64) NOT NULL,
    title           VARCHAR(512),
    status          VARCHAR(32) DEFAULT 'active',  -- active / completed / archived
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX idx_sessions_status ON conversation_sessions(status);
CREATE INDEX idx_sessions_created_at ON conversation_sessions(created_at DESC);

-- ============================================================
-- Conversation Messages Table
-- ============================================================
CREATE TABLE IF NOT EXISTS conversation_messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(16) NOT NULL,  -- user / assistant / system
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    -- RAG related fields
    citations       JSONB DEFAULT '[]',
    confidence      FLOAT,
    model_used      VARCHAR(64),
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_session_id ON conversation_messages(session_id);
CREATE INDEX idx_messages_created_at ON conversation_messages(created_at);

-- ============================================================
-- Documents Table
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id              VARCHAR(64) PRIMARY KEY,
    collection      VARCHAR(128) NOT NULL,
    filename        VARCHAR(512) NOT NULL,
    file_type       VARCHAR(32) NOT NULL,
    file_size       BIGINT,
    file_path       VARCHAR(1024),          -- MinIO / local path
    status          VARCHAR(32) DEFAULT 'uploaded',  -- uploaded / processing / completed / failed
    chunk_count     INTEGER DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_collection ON documents(collection);
CREATE INDEX idx_documents_status ON documents(status);

-- ============================================================
-- LangGraph Checkpoint Table
-- Note: Created automatically by AsyncPostgresSaver.setup()
-- but we reserve the namespace here for clarity
-- ============================================================
