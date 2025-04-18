FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем всё в контейнер
COPY . .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -c constraints.txt

# Запуск бота
CMD ["python", "car_import_bot_with_buttons_and_reset_final.py"]


