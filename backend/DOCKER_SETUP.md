# 🐳 Ghid de Setup Docker

## ⚠️ Pași Prealabili

### 1. Pornește Docker Desktop

**Windows:**
- Deschide Docker Desktop din Start Menu
- Așteaptă până când vezi "Docker Desktop is running" în system tray

**Verifică că Docker rulează:**
```bash
docker ps
```

Dacă vezi eroarea `The system cannot find the file specified`, înseamnă că Docker Desktop nu rulează.

## 🚀 Rulare Docker

### 1. Construiește și pornește containerele

```bash
docker-compose up --build
```

Sau în background (detached mode):
```bash
docker-compose up --build -d
```

### 2. Verifică statusul

```bash
docker-compose ps
```

Ar trebui să vezi 3 servicii:
- `office_appointments_db` (PostgreSQL)
- `office_appointments_redis` (Redis)
- `office_appointments_web` (Django)

### 3. Verifică log-urile

```bash
docker-compose logs -f web
```

### 4. Testează API-ul

După ce containerele sunt pornite, accesează:
- **API**: http://localhost:8000/api/
- **Swagger**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/

## 📝 Comenzi Utile

### Oprește containerele

```bash
docker-compose down
```

### Oprește și șterge volume-urile (resetează baza de date)

```bash
docker-compose down -v
```

### Reconstruiește imaginea

```bash
docker-compose build --no-cache
docker-compose up
```

### Rulează comenzi Django

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py createsuperuser
```

### Accesează shell-ul containerului

```bash
docker-compose exec web bash
```

### Accesează PostgreSQL

```bash
docker-compose exec db psql -U postgres -d office_appointments
```

## 🐛 Troubleshooting

### Eroare: "The system cannot find the file specified"

**Soluție**: Pornește Docker Desktop.

### Eroare: "port is already allocated"

**Soluție**: Schimbă porturile în `docker-compose.yml` sau oprește serviciile care folosesc acele porturi.

### Eroare: "database connection refused"

**Soluție**: 
1. Verifică că serviciul `db` este healthy: `docker-compose ps`
2. Așteaptă câteva secunde pentru ca PostgreSQL să pornească complet
3. Verifică log-urile: `docker-compose logs db`

### Eroare: "migration failed"

**Soluție**:
```bash
docker-compose down -v
docker-compose up --build
```

## ✅ Verificare Finală

După ce totul rulează, testează:

1. **API Health Check:**
   ```bash
   curl http://localhost:8000/api/
   ```

2. **Swagger UI:**
   Deschide http://localhost:8000/api/docs/ în browser

3. **Creează date de test:**
   ```bash
   docker-compose exec web python manage.py seed_data
   ```

4. **Login:**
   - Username: `super123`
   - Password: `super123`

