CREATE TABLE IF NOT EXISTS users (
    sub TEXT PRIMARY KEY,
    request_at DATE,
    email TEXT,
    file_name TEXT,
    summary_type TEXT,
    custom_prompt TEXT,
    audience_context TEXT,
    screenshots BOOLEAN,
    output_format TEXT,
    detail_level INTEGER,
    summary_files BYTEA,
    processing_timestamp TIMESTAMPTZ DEFAULT now()
);