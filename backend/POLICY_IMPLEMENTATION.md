# Implementare Politici de Prezență și Desk Over-Quota

## 📋 Ce am implementat

Am implementat sistemul complet de politici de prezență fizică și logica de identificare a utilizatorilor over-quota pentru birouri.

---

## 🏗️ 1. Modele noi și extinderi

### OrgPolicy (Singleton)
Model singleton pentru politica organizațională:
- `default_required_days_per_week`: numărul default de zile obligatorii (default: 2)
- `updated_at`: data ultimei actualizări

**Caracteristici**:
- Singleton pattern: există un singur rând (pk=1)
- Metodă `get_policy()`: returnează policy-ul existent sau creează unul default

### Team (extins)
Am adăugat două câmpuri noi:
- `required_days_per_week`: PositiveSmallIntegerField (nullable) - override la nivel de echipă
- `required_weekdays`: ArrayField(IntegerField) (nullable) - lista zilelor din săptămână (0=Luni, ..., 6=Duminică)

**Metodă nouă**:
- `get_required_days_per_week()`: returnează required_days pentru echipă (fallback: team override → org default)

---

## 🔗 2. Endpoint-uri implementate

### Policy Organizațională

#### GET /api/policy/
**Permisiuni**: SUPERADMIN
**Descriere**: Returnează politica organizațională curentă

**Răspuns**:
```json
{
  "default_required_days_per_week": 2,
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### POST /api/policy/required-days/
**Permisiuni**: SUPERADMIN
**Descriere**: Setează noul minim global de zile obligatorii

**Request Body**:
```json
{
  "default_required_days_per_week": 3
}
```

**Logica**:
1. Actualizează policy-ul organizațional
2. **Ridică automat** echipele care au `required_days_per_week < new_days`
3. **Nu scade** echipele care au valori mai mari

**Răspuns**:
```json
{
  "message": "Policy actualizat de la 2 la 3 zile/săptămână",
  "default_required_days_per_week": 3,
  "updated_teams_count": 2
}
```

### Politica de Prezență pentru Echipă

#### PATCH /api/teams/{id}/presence-policy/
**Permisiuni**: SUPERADMIN
**Descriere**: Actualizează politica de prezență pentru o echipă

**Request Body**:
```json
{
  "required_days_per_week": 3,
  "required_weekdays": [0, 2, 4]  // Luni, Miercuri, Vineri
}
```

**Câmpuri**:
- `required_days_per_week`: integer (0-7) sau null (folosește default-ul org)
- `required_weekdays`: array de integers (0-6) sau null (fără restricții pe zile)

**Validări**:
- `required_days_per_week`: între 0 și 7
- `required_weekdays`: valori între 0 (Luni) și 6 (Duminică)
- Elimină duplicatele și sortează automat

### Desk Over-Quota

#### GET /api/appointments/desk-overquota?date=YYYY-MM-DD
**Permisiuni**: IsAuthenticated (toți utilizatorii autentificați)
**Descriere**: Returnează utilizatorii care au rezervat birou în ziua specificată și au atins deja norma de zile fizice

**Parametri**:
- `date` (required): data pentru care se verifică (format: YYYY-MM-DD)

**Logica de calcul**:
1. Găsește toate appointment-urile pentru birouri (`ItemCategory.slug="birou"`) în ziua specificată
2. Pentru fiecare user care are rezervare în acea zi:
   - Calculează săptămâna de lucru (Luni-Vineri, 5 zile lucrătoare)
   - Numără zilele distincte din săptămâna de lucru în care userul are cel puțin o rezervare pe birou
   - Determină `required_days` pentru user (team override → org default)
   - Verifică dacă `actual_days >= required_days`
3. Returnează doar userii care au atins deja norma

**Notă**: Săptămâna de lucru este hardcodată ca Luni-Vineri (nu include weekend-ul).

**Răspuns**:
```json
{
  "date": "2024-01-15",
  "week_start": "2024-01-15",
  "week_end": "2024-01-19",
  "over_quota_users": [
    {
      "user_id": 1,
      "username": "john.doe",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "team": "IT Department",
      "required_days": 2,
      "actual_days": 3,
      "appointments_on_date": [
        {
          "id": 1,
          "item": "DESK-001",
          "start_at": "2024-01-15T09:00:00Z",
          "end_at": "2024-01-15T17:00:00Z"
        }
      ]
    }
  ],
  "total_over_quota": 1
}
```

---

## 🧮 3. Logica de calcul

### Calculul zilelor fizice
```python
# Pentru fiecare user:
1. Găsește toate appointment-urile pentru birouri în săptămâna ISO
2. Extrage zilele distincte (start_at__date)
3. Numără zilele distincte
4. Compară cu required_days (team.get_required_days_per_week() sau org default)
```

### Fallback pentru required_days
```
1. Dacă user.team.required_days_per_week există → folosește-l
2. Altfel → folosește OrgPolicy.default_required_days_per_week
```

### Săptămâna de lucru
- **Început**: Luni (weekday = 0)
- **Sfârșit**: Vineri (weekday = 4)
- **Durată**: 5 zile lucrătoare (hardcodată)
- Calcul: `week_start = target_date - timedelta(days=target_date.weekday())`, `week_end = week_start + timedelta(days=4)`

---

## 📊 4. Exemple de utilizare

### Exemplu 1: Setare policy organizațională
```bash
# SUPERADMIN setează minimul global la 3 zile/săptămână
POST /api/policy/required-days/
{
  "default_required_days_per_week": 3
}

# Rezultat: toate echipele cu required_days_per_week < 3 vor fi actualizate la 3
```

### Exemplu 2: Setare policy pentru echipă
```bash
# SUPERADMIN setează politica pentru "IT Department"
PATCH /api/teams/1/presence-policy/
{
  "required_days_per_week": 4,
  "required_weekdays": [0, 2, 4]  // Luni, Miercuri, Vineri obligatorii
}
```

### Exemplu 3: Verificare over-quota
```bash
# Verifică utilizatorii over-quota pentru 15 ianuarie 2024
GET /api/appointments/desk-overquota?date=2024-01-15

# Rezultat: lista cu toți utilizatorii care:
# - Au rezervat birou în 15 ianuarie
# - Au deja >= required_days zile fizice în săptămâna 15-21 ianuarie
```

---

## 🔍 5. Detalii tehnice

### Singleton Pattern pentru OrgPolicy
```python
def save(self, *args, **kwargs):
    self.pk = 1  # Forțează pk=1 pentru singleton
    super().save(*args, **kwargs)

@classmethod
def get_policy(cls):
    policy, created = cls.objects.get_or_create(pk=1)
    return policy
```

### ArrayField pentru required_weekdays
- Folosește `ArrayField(IntegerField)` din PostgreSQL
- Permite stocarea unei liste de integers
- Nullable: unele echipe nu au restricții pe zile specifice

### Calcul eficient
- Folosește `select_related()` pentru optimizare
- Folosește `values('start_at__date').distinct()` pentru zile distincte
- Filtrare la nivel de bază de date (eficient)

---

## ✅ 6. Validări implementate

### OrgPolicy
- `default_required_days_per_week`: între 0 și 7

### Team
- `required_days_per_week`: între 0 și 7 sau null
- `required_weekdays`: array de integers între 0 și 6, sau null
- Eliminare automată a duplicatelor și sortare

### Desk Over-Quota
- Validare format date (YYYY-MM-DD)
- Verificare existență categorie "birou"
- Gestionare cazuri edge (fără rezervări, fără echipe)

---

## 🎯 7. Cazuri de utilizare

### Scenariu 1: Schimbare policy organizațională
1. SUPERADMIN decide să crească minimul de la 2 la 3 zile/săptămână
2. POST `/api/policy/required-days/` cu `default_required_days_per_week: 3`
3. Sistemul actualizează automat toate echipele cu `required_days_per_week < 3` la 3
4. Echipele cu `required_days_per_week >= 3` rămân neschimbate

### Scenariu 2: Politică specifică pentru echipă
1. SUPERADMIN setează pentru "Sales Team" să lucreze 4 zile/săptămână
2. PATCH `/api/teams/{id}/presence-policy/` cu `required_days_per_week: 4`
3. Echipa "Sales Team" va folosi 4 zile, restul folosesc default-ul org

### Scenariu 3: Identificare utilizatori over-quota
1. În 15 ianuarie, un angajat încearcă să rezerve birou dar nu găsește loc
2. Sistemul apelează `GET /api/appointments/desk-overquota?date=2024-01-15`
3. Returnează lista utilizatorilor care au deja >= required_days zile fizice
4. Sistemul de notificări (viitor) trimite email-uri către acești utilizatori
5. Când unul acceptă să elibereze locul, sistemul alocă biroul angajatului care a căutat

---

## 📝 8. Note importante

### Categoria "birou"
- Endpoint-ul `desk-overquota` caută `ItemCategory.slug="birou"`
- **Important**: Trebuie să existe o categorie cu slug="birou" în sistem
- Dacă nu există, endpoint-ul returnează 404

### Săptămâna ISO
- Săptămâna începe Luni (weekday=0) și se termină Duminică (weekday=6)
- Calculul este corect pentru toate zilele săptămânii

### Fallback logic
- Dacă userul nu are echipă → folosește default-ul org
- Dacă echipa nu are `required_days_per_week` setat → folosește default-ul org
- Dacă echipa are `required_days_per_week` setat → folosește valoarea echipei

---

## 🚀 9. Pași următori (viitor)

1. **Sistem de notificări**: Integrare cu serviciu de email pentru notificări
2. **Auto-reallocation**: Când un utilizator acceptă să elibereze, alocare automată
3. **Dashboard**: Interfață pentru vizualizare policy-uri și statistici
4. **Reporting**: Rapoarte despre utilizarea birourilor și respectarea normelor

---

## 🧪 10. Testare

### Test 1: Creare policy organizațională
```bash
# Verifică policy-ul (ar trebui să returneze default=2)
GET /api/policy/

# Actualizează la 3 zile
POST /api/policy/required-days/
{
  "default_required_days_per_week": 3
}
```

### Test 2: Setare policy pentru echipă
```bash
# Setează politica pentru echipă
PATCH /api/teams/1/presence-policy/
{
  "required_days_per_week": 4,
  "required_weekdays": [0, 2, 4]
}
```

### Test 3: Verificare over-quota
```bash
# Creează categoria "birou" (dacă nu există)
POST /api/item-categories/
{
  "name": "Birou",
  "slug": "birou",
  "description": "Birouri pentru lucru fizic"
}

# Creează item-uri de tip birou
POST /api/items/
{
  "name": "DESK-001",
  "room": 1,
  "category": <id_categorie_birou>,
  "status": "ACTIVE"
}

# Creează appointment-uri pentru testare
# Apoi verifică over-quota
GET /api/appointments/desk-overquota?date=2024-01-15
```

---

**Fișiere modificate**:
- `apps/core/models.py` - OrgPolicy și extinderi Team
- `apps/core/migrations/0003_*.py` - Migrație pentru noile câmpuri
- `apps/core/policy_views.py` - OrgPolicyViewSet
- `apps/core/api.py` - TeamViewSet cu action `update_presence_policy`
- `apps/core/viewsets.py` - AppointmentViewSet cu action `desk_overquota`
- `apps/core/admin.py` - Admin pentru OrgPolicy
- `config/urls.py` - Routing pentru policy endpoints

