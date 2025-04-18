FROM python:3.11-slim

# Установка зависимостей для сборки пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "car_import_bot_with_buttons_and_reset_final.py"]



