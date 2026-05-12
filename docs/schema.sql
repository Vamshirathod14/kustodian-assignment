-- Kustodian Assignment Database Schema

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
);

CREATE TABLE IF NOT EXISTS job_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) REFERENCES jobs(job_id),
    event_type VARCHAR(50),
    message TEXT,
    step_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster lookups
CREATE INDEX idx_jobs_job_id ON jobs(job_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_logs_job_id ON job_logs(job_id);
CREATE INDEX idx_logs_step ON job_logs(step_number);