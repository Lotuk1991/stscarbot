FROM python:3.11-slim

# Установка компилятора и заголовков Python
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt -c constraints.txt

CMD ["python", "car_import_bot_with_buttons_and_reset_final.py"]
