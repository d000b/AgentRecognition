#!/bin/bash
# entrypoint.sh

set -e

echo "================================================================"
echo "              AGENT RECOGNITION SYSTEM STARTUP"
echo "================================================================"

# Проверка переменных окружения
echo "📋 Environment variables:"
echo "  - MODEL_PATH: ${MODEL_PATH:-/app/model_weights}"
echo "  - UPLOAD_DIR: ${UPLOAD_DIR:-/app/uploads}"
echo "  - PROCESSED_DIR: ${PROCESSED_DIR:-/app/processed}"
echo "  - TEMP_DIR: ${TEMP_DIR:-/app/temp}"
echo "  - LOG_DIR: ${LOG_DIR:-/app/logs}"
echo "  - DB_PATH: ${DB_PATH:-/app/database}"
echo "  - CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-0}"

# Проверка CUDA
echo "🔍 Checking CUDA availability..."
if python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"; then
    echo "✅ CUDA is available"
    python3 -c "import torch; print(f'Device count: {torch.cuda.device_count()}'); [torch.cuda.device_count() > 0] and print(f'Device 0: {torch.cuda.get_device_name(0)}')"
else
    echo "⚠️  CUDA is NOT available - running in CPU mode"
fi

# Проверка монтирования volumes
echo "📂 Checking mounted volumes..."
python3 /app/check_mounts.py

if [ $? -ne 0 ]; then
    echo "❌ Volume check failed!"
    echo "Please check your docker-compose.yml volume mounts."
    exit 1
fi

# Создание директорий
echo "📁 Creating directories..."
python3 -c "
import os
from config import config
config.init_directories()
print('Directories created successfully')
"

# Создание таблиц БД
echo "🗄️  Initializing database..."
python3 -c "
from database import create_tables
create_tables()
print('Database initialized successfully')
"

# Запуск приложения
echo "🚀 Starting application..."
echo "================================================================"
echo "  API Documentation: http://localhost:8000/docs"
echo "  Web Interface:     http://localhost:8000/web"
echo "  Health Check:      http://localhost:8000/health"
echo "================================================================"

# Запуск сервера
exec python3 main.py