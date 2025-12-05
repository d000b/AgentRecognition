-- postgres_init/01-init.sql
-- Скрипт инициализации базы данных

-- Создание пользователя admin если его нет
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin WITH LOGIN PASSWORD 'secure_password123' CREATEDB CREATEROLE;
  END IF;
END
$$;

-- Создание базы данных если она не существует
SELECT 'CREATE DATABASE agentrecognition WITH OWNER = admin ENCODING = ''UTF8'' LOCALE = ''C'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'agentrecognition')\gexec

-- Подключение к новой базе данных
\c agentrecognition

-- Создание таблиц в схеме public
-- Таблица inference_requests
CREATE TABLE IF NOT EXISTS inference_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(36) UNIQUE NOT NULL,
    session_id VARCHAR(36),
    text_prompt TEXT NOT NULL,
    image_paths JSONB,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    result TEXT,
    error_message TEXT,
    processing_time FLOAT,
    tokens_generated INTEGER,
    model_used VARCHAR(100) DEFAULT 'Qwen3-VL-30B-A3B-Instruct',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Таблица file_storage
CREATE TABLE IF NOT EXISTS file_storage (
    id SERIAL PRIMARY KEY,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    size_bytes INTEGER NOT NULL,
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    uploaded_by VARCHAR(100),
    session_id VARCHAR(36),
    is_processed BOOLEAN DEFAULT FALSE NOT NULL,
    processing_result JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0 NOT NULL
);

-- Таблица system_logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10) NOT NULL,
    source VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    CONSTRAINT level_check CHECK (level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG'))
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_inference_requests_request_id ON inference_requests(request_id);
CREATE INDEX IF NOT EXISTS idx_inference_requests_session_id ON inference_requests(session_id);
CREATE INDEX IF NOT EXISTS idx_inference_requests_status ON inference_requests(status);
CREATE INDEX IF NOT EXISTS idx_inference_requests_created_at ON inference_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_file_storage_file_hash ON file_storage(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_storage_session_id ON file_storage(session_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_file_type ON file_storage(file_type);
CREATE INDEX IF NOT EXISTS idx_file_storage_uploaded_at ON file_storage(uploaded_at);

CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(source);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);

-- Предоставление прав пользователю admin
GRANT ALL PRIVILEGES ON DATABASE agentrecognition TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- Настройка поискового пути
ALTER DATABASE agentrecognition SET search_path TO public;

-- Комментарии к таблицам
COMMENT ON TABLE inference_requests IS 'Запросы inference к модели';
COMMENT ON TABLE file_storage IS 'Хранилище загруженных файлов';
COMMENT ON TABLE system_logs IS 'Системные логи приложения';