FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

RUN apt update && apt-get install -y git \
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
ENTRYPOINT ["/app/entrypoint.sh"]
