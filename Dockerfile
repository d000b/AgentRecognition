FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# 2. Set up Python 3.10 (well-supported)
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# 3. Install PyTorch with CUDA 12.4 support
# Option A: Install from PyPI with CUDA 12.4 (if available)
RUN pip install --no-cache-dir \
    torch==2.5.0 \
    torchvision==0.20.0 \
    torchaudio==2.5.0 \
    --index-url https://download.pytorch.org/whl/cu124

# If CUDA 12.4 packages aren't available yet, try:
# Option B: Install PyTorch 2.5 with CUDA 12.1 (should work with 5060 Ti)
# RUN pip install --no-cache-dir \
#     torch==2.5.0 \
#     torchvision==0.20.0 \
#     torchaudio==2.5.0 \
#     --index-url https://download.pytorch.org/whl/cu121

# Option C: For RTX 5060 Ti, you might need nightly build
# RUN pip install --no-cache-dir \
#     --pre torch torchvision torchaudio \
#     --index-url https://download.pytorch.org/whl/nightly/cu124


# 4. Install transformers from git (or specific version)
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
