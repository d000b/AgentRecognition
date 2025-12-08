FROM nvidia/cuda:12.1.1-cudnn-runtime-ubuntu22.04

# Python + venv
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv

# Создание виртуального окружения
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Обновление pip / setuptools / wheel
RUN pip install --upgrade pip setuptools wheel

# Установка PyTorch с поддержкой CUDA 13.0
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# If CUDA 12.4 packages aren't available yet, try:
# Option B: Install PyTorch 2.5 with CUDA 12.1 (should work with 5060 Ti)
# RUN pip install --no-cache-dir \
#     torch==2.5.0 \
#     torchvision==0.20.0 \
#     torchaudio==2.5.0 \
#     --index-url https://download.pytorch.org/whl/cu121

RUN  apt-get install -y git \
  && pip install --no-cache-dir git+https://github.com/huggingface/transformers

# Установка остальных зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание структуры директорий внутри контейнера
RUN mkdir -p \
    /root/.cache/huggingface \
    /app/logs \
    /app/temp

WORKDIR /app
# Копирование исходного кода
COPY . /app/

# Установка прав
RUN chmod +x /app/entrypoint.sh

# Точка входа
ENTRYPOINT ["./entrypoint.sh"]
