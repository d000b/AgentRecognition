FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

# Basic libs
RUN apt update && apt install -y \
    git wget curl libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
WORKDIR /app

CMD ["python"]
