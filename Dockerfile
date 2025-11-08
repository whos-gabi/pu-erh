# Dockerfile pentru Django Backend
# Folosim Python 3.11 (compatibil cu Django 5.x)

FROM python:3.11-slim

# Setăm variabile de mediu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalăm dependențe sistem
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Creează directorul de lucru
WORKDIR /app

# Copiază requirements.txt și instalează dependențele Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiază codul aplicației
COPY . .

# Creează directorul pentru static files (dacă e nevoie)
RUN mkdir -p /app/staticfiles

# Expune portul 8000 (Django development server)
EXPOSE 8000

# Comandă default: rulează scriptul de inițializare
# Scriptul rulează migrațiile, creează superadmin-ul și datele de test, apoi pornește serverul
# În producție, folosește gunicorn sau uwsgi
CMD ["python", "init_docker.py"]

