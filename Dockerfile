# Dockerfile
FROM nvidia/cuda:12.1-base-ubuntu22.04

# Установка Python
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий для хранения
RUN mkdir -p /mnt/nvme/uploads /mnt/raid/processed

# Копирование исходного кода
COPY . .

# Запуск сервера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]