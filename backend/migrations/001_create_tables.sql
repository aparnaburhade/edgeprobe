-- migrations/001_create_tables.sql
-- Run this file once against your PostgreSQL database to set up the schema.

CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    prompt_text TEXT NOT NULL,
    reference_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    request_id TEXT,
    prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    response_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'started',
    error_message TEXT,
    completed_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS claims (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    verdict VARCHAR(50),
    evidence_text TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
