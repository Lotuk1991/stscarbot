FROM python:3.11-slim

# Установка необходимых системных пакетов для сборки aiohttp
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
# Устанавливаем зависимости, используя только бинарники
RUN pip install --only-binary=:all: -r requirements.txt

CMD ["python", "car_import_bot_with_buttons_and_reset_final.py"]




