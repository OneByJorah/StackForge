FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app.py .
COPY frontend/ /app/static/

EXPOSE 9500

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9500"]
