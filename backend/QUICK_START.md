# 🚀 Quick Start - Docker

## Pasul 1: Pornește Docker Desktop

**Windows:**
1. Deschide Docker Desktop din Start Menu
2. Așteaptă până când vezi "Docker Desktop is running" în system tray (colțul din dreapta jos)

## Pasul 2: Verifică că Docker rulează

```bash
docker ps
```

Dacă vezi o listă (chiar dacă e goală), înseamnă că Docker rulează.

## Pasul 3: Pornește containerele

```bash
docker-compose up --build
```

Această comandă va:
- Construi imaginea Docker pentru Django
- Porni PostgreSQL (port 5432)
- Porni Redis (port 6379)
- Rula migrațiile automat
- Porni serverul Django (port 8000)

**Așteaptă** până vezi mesajul:
```
Django version X.X.X, using settings 'config.settings'
Starting development server at http://0.0.0.0:8000/
```

## Pasul 4: Testează aplicația

Deschide în browser:
- **API**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/

## Pasul 5: Creează date de test

Într-un terminal nou (lasă primul să ruleze):

```bash
docker-compose exec web python manage.py seed_data
```

## Pasul 6: Testează login

În Swagger UI (http://localhost:8000/api/docs/):
1. Găsește endpoint-ul `POST /api/auth/login/`
2. Click "Try it out"
3. Introdu:
   ```json
   {
     "username": "super123",
     "password": "super123"
   }
   ```
4. Click "Execute"
5. Copiază `access` token-ul
6. Click butonul "Authorize" (sus în Swagger)
7. Introdu: `Bearer <token-ul-copiat>`
8. Acum poți testa toate endpoint-urile!

## 🛑 Oprește containerele

Când ai terminat, apasă `Ctrl+C` în terminal sau:

```bash
docker-compose down
```

## ❌ Probleme?

### "The system cannot find the file specified"
→ Docker Desktop nu rulează. Pornește-l!

### "port is already allocated"
→ Portul 8000, 5432 sau 6379 este deja folosit. Oprește serviciile care le folosesc sau schimbă porturile în `docker-compose.yml`.

### "database connection refused"
→ Așteaptă câteva secunde pentru ca PostgreSQL să pornească complet. Verifică log-urile:
```bash
docker-compose logs db
```

