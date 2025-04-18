FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt -c constraints.txt

CMD ["python", "car_import_bot_with_buttons_and_reset_final.py"]
