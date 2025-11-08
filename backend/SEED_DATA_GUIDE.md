# Ghid Date de Test (Seed Data)

## 📋 Ce am creat

Am creat un management command Django care generează date de test pentru toate modelele aplicației.

## 🚀 Cum să folosești

### Rulare simplă:
```bash
python manage.py seed_data
```

### Rulare cu ștergere date existente:
```bash
python manage.py seed_data --clear
```

## 📊 Date create

### 1. Roles (4)
- ADMIN
- MANAGER
- EMPLOYEE
- DEVELOPER

### 2. Teams (4)
- IT Department (manager: superadmin)
- HR Department
- Sales Team
- Marketing

### 3. Users - Employee (4)
Toți utilizatorii au parola: **`test123`**

| Username | Email | First Name | Last Name | Team | Role |
|----------|-------|------------|-----------|------|------|
| john.doe | john.doe@example.com | John | Doe | IT Department | EMPLOYEE |
| jane.smith | jane.smith@example.com | Jane | Smith | IT Department | EMPLOYEE |
| bob.wilson | bob.wilson@example.com | Bob | Wilson | HR Department | EMPLOYEE |
| alice.brown | alice.brown@example.com | Alice | Brown | Sales Team | DEVELOPER |

**Notă**: SUPERADMIN-ul tău (`super123`) nu este afectat de acest command.

### 4. Rooms (6)
| Code | Name | Capacity | Features | Status |
|------|------|----------|----------|--------|
| B1-101 | Sala de conferinte A | 20 | projector, whiteboard, video_conference | Active |
| B1-102 | Sala de conferinte B | 15 | projector, whiteboard | Active |
| B1-203 | Birou individual 1 | 1 | desk, monitor | Active |
| B1-204 | Birou individual 2 | 1 | desk, monitor | Active |
| B2-301 | Sala de training | 30 | projector, whiteboard, computers: 15 | Active |
| B2-302 | Sala inactiva | 10 | - | **Inactive** |

### 5. Item Categories (5)
- Laptop
- Monitor
- Proiector
- Tableta
- Mouse

### 6. Items (10)
| Name | Category | Room | Status |
|------|----------|------|--------|
| LT-001 | Laptop | B1-101 | ACTIVE |
| LT-002 | Laptop | B1-101 | ACTIVE |
| LT-003 | Laptop | B1-102 | ACTIVE |
| LT-004 | Laptop | B1-203 | ACTIVE |
| LT-005 | Laptop | B1-204 | **BROKEN** |
| MON-001 | Monitor | B1-203 | ACTIVE |
| MON-002 | Monitor | B1-204 | ACTIVE |
| PROJ-001 | Proiector | B1-101 | ACTIVE |
| PROJ-002 | Proiector | B1-102 | ACTIVE |
| TAB-001 | Tableta | B1-101 | ACTIVE |

### 7. Requests (5)
- **2 cereri WAITING** (în așteptare de aprobare)
- **2 cereri APPROVED** (aprobate de superadmin)
- **1 cerere DISMISSED** (respinsă de superadmin)

### 8. Appointments (6)
- **2 programări în trecut** (finalizate)
- **2 programări active** (în prezent)
- **2 programări în viitor**

## 🔑 Credențiale pentru testare

### SUPERADMIN:
- **Username**: `super123`
- **Password**: `super123`

### EMPLOYEE (toți au aceeași parolă):
- **Password**: `test123`
- **Usernames**:
  - `john.doe`
  - `jane.smith`
  - `bob.wilson`
  - `alice.brown`

## 🧪 Scenarii de testare

### 1. Testare autentificare
```bash
# Login ca Employee
POST /api/auth/login/
{
  "username": "john.doe",
  "password": "test123"
}

# Login ca SUPERADMIN
POST /api/auth/login/
{
  "username": "super123",
  "password": "super123"
}
```

### 2. Testare permisiuni
- **Employee** (`john.doe`):
  - ✅ Poate vedea propriul profil (`GET /api/me/`)
  - ✅ Poate vedea propriile cereri (`GET /api/requests/`)
  - ❌ NU poate vedea lista de utilizatori (`GET /api/users/`)
  - ❌ NU poate crea/utilizatori noi

- **SUPERADMIN** (`super123`):
  - ✅ Poate vedea tot
  - ✅ Poate crea/edita/șterge utilizatori
  - ✅ Poate aproba/respinge cereri

### 3. Testare cereri (Requests)
- Cereri **WAITING**: pot fi aprobate/respinse de SUPERADMIN
- Cereri **APPROVED**: au fost aprobate de superadmin
- Cereri **DISMISSED**: au fost respinse de superadmin

### 4. Testare programări (Appointments)
- Programări **în trecut**: finalizate
- Programări **active**: în curs
- Programări **în viitor**: planificate

### 5. Testare ExclusionConstraint
Încearcă să creezi o programare care se suprapune cu una existentă pe același item:
```bash
POST /api/appointments/
{
  "item": 1,  # LT-001
  "start_at": "2024-01-15T10:00:00Z",
  "end_at": "2024-01-15T11:00:00Z"
}
```
Ar trebui să eșueze cu eroare de suprapunere.

## 📝 Structura Command-ului

Command-ul este organizat în metode separate pentru fiecare tip de date:

1. `create_roles()` - Creează roluri
2. `create_teams()` - Creează echipe
3. `create_users()` - Creează utilizatori Employee
4. `create_rooms()` - Creează camere
5. `create_item_categories()` - Creează categorii
6. `create_items()` - Creează item-uri
7. `create_requests()` - Creează cereri
8. `create_appointments()` - Creează programări

## 🔄 Re-rulare

Dacă vrei să re-creezi datele:

```bash
# Șterge datele existente și creează altele noi
python manage.py seed_data --clear
```

**Atenție**: `--clear` va șterge:
- ✅ Toate Appointments
- ✅ Toate Requests
- ✅ Toate Items
- ✅ Toate ItemCategories
- ✅ Toate Rooms
- ✅ Toate Teams
- ✅ Toate Roles
- ❌ **NU** șterge User-ii (păstrează superadmin și employee-ii)

## 💡 Sfaturi

1. **Rulează seed data după migrații**: Asigură-te că ai aplicat toate migrațiile înainte
2. **Folosește `--clear` cu grijă**: Verifică că nu ai date importante înainte de ștergere
3. **Modifică datele după nevoie**: Poți edita `seed_data.py` pentru a adăuga mai multe date
4. **Testează scenarii diferite**: Folosește datele create pentru a testa toate endpoint-urile

## 🎯 Următorii pași

Acum că ai date de test, poți:
1. Testa endpoint-urile de autentificare
2. Testa permisiunile (Employee vs SUPERADMIN)
3. Testa CRUD operations pe toate resursele
4. Testa logica de business (approve/dismiss requests)
5. Testa ExclusionConstraint pentru appointments

---

**Fișier**: `apps/core/management/commands/seed_data.py`

