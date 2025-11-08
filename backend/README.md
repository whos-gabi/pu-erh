# Office Smart Appointments Management System (Molson Coors)

Sistem de management pentru rezervări de birouri, camere și echipamente în birou.

## 🚀 Tehnologii

- **Backend**: Django 5.x + Django REST Framework
- **Database**: PostgreSQL 14+
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Notifications**: Django + Celery (Redis) - în dezvoltare
- **Containerization**: Docker + Docker Compose

## 📋 Cerințe

- Docker și Docker Compose instalate
- Git

## 🐳 Rulare cu Docker

### 1. Clonează repository-ul

```bash
git clone <repository-url>
cd ProgramMe
```

### 2. Pornește containerele

```bash
docker-compose up --build
```

Această comandă va:
- Construi imaginea Docker pentru Django
- Porni PostgreSQL (port 5432)
- Porni Redis (port 6379)
- Rula migrațiile automat
- Porni serverul Django (port 8000)

### 3. Accesează aplicația

- **API**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin**: http://localhost:8000/admin/

### 4. Creează superadmin (opțional)

```bash
docker-compose exec web python manage.py createsuperuser
```

Sau folosește datele de test:

```bash
docker-compose exec web python manage.py seed_data
```

Credențiale default:
- Username: `super123`
- Password: `super123`

## 🔧 Comenzi utile

### Oprește containerele

```bash
docker-compose down
```

### Oprește și șterge volume-urile (resetează baza de date)

```bash
docker-compose down -v
```

### Vezi log-urile

```bash
docker-compose logs -f web
```

### Rulează comenzi Django

```bash
docker-compose exec web python manage.py <comanda>
```

### Accesează shell-ul containerului

```bash
docker-compose exec web bash
```

### Reconstruiește imaginea (după modificări în requirements.txt)

```bash
docker-compose build --no-cache
docker-compose up
```

## 📁 Structura proiectului

```
ProgramMe/
├── apps/
│   ├── core/           # Aplicația principală (models, viewsets, serializers)
│   └── notify/         # Sistem de notificări (în dezvoltare)
├── config/             # Setări Django (settings, urls)
├── templates/          # Template-uri email
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔐 Variabile de mediu

Poți crea un fișier `.env` în root pentru a seta variabilele (vezi `.env.example` pentru template):

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
POSTGRES_DB=office_appointments
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

**Notă**: `.env.example` conține doar exemple. Creează un fișier `.env` real cu valorile tale (nu commit-ui `.env` în Git!).

## 📚 API Endpoints

### Autentificare
- `POST /api/auth/login/` - Login (obține JWT token)
- `POST /api/auth/refresh/` - Refresh token

### Utilizatori
- `GET /api/me/` - Profilul utilizatorului curent
- `GET /api/users/` - Listă utilizatori (SUPERADMIN)

### Echipe
- `GET /api/teams/` - Listă echipe
- `POST /api/teams/` - Creează echipă (SUPERADMIN)
- `PATCH /api/teams/{id}/presence-policy/` - Actualizează politica de prezență

### Programări
- `GET /api/appointments/` - Listă programări
- `POST /api/appointments/` - Creează programare
- `GET /api/appointments/desk-overquota/?date=YYYY-MM-DD` - Utilizatori over-quota

### Cereri
- `GET /api/requests/` - Listă cereri
- `POST /api/requests/{id}/approve/` - Aprobă cerere (SUPERADMIN)
- `POST /api/requests/{id}/dismiss/` - Respinge cerere (SUPERADMIN)

### Policy
- `GET /api/policy/` - Obține politica organizațională
- `POST /api/policy/required-days/` - Actualizează zilele obligatorii (SUPERADMIN)

## 🧪 Testare

### Rulare seed data

```bash
docker-compose exec web python manage.py seed_data
```

### Verificare migrații

```bash
docker-compose exec web python manage.py showmigrations
```

## 🐛 Troubleshooting

### Portul 8000 este deja folosit

Modifică portul în `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Schimbă 8001 cu alt port
```

### Baza de date nu se conectează

Verifică că serviciul `db` este healthy:
```bash
docker-compose ps
```

### Erori la migrații

Resetează baza de date:
```bash
docker-compose down -v
docker-compose up
```

## 📝 Notă

- În dezvoltare, serverul Django rulează cu `runserver` (nu este optim pentru producție)
- Pentru producție, folosește `gunicorn` sau `uwsgi`
- Celery worker nu este configurat încă (notificările sunt pregătite dar nu trimit email-uri efectiv)

## 👥 Contribuitori

- Backend: [Nume]
- Frontend: [Nume]

## 📄 Licență

[Specifică licența]

