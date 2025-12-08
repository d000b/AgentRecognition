FROM nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3.12       \
    python3.12-venv  \
    python3-pip      && \
    ln -s /usr/bin/python3.12 /usr/bin/python

RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu130

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
