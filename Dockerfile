FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "cd /app/payments && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]