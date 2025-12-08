FROM pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime

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
ENTRYPOINT ["./entrypoint.sh"]
