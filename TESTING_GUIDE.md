# Ghid de Testare - Edge Cases

## Setup Initial

1. **Porneste serverul Django:**
   ```bash
   python manage.py runserver
   ```

2. **Asigura-te ca exista date de test:**
   ```bash
   python manage.py seed_data
   ```

3. **Obține token JWT pentru superadmin:**
   ```bash
   POST http://localhost:8000/api/auth/login/
   {
     "username": "super123",
     "password": "super123"
   }
   ```
   Salvează `access` token pentru request-urile următoare.

---

## 1. Policy Endpoints

### GET /api/policy/
**Test 1: SUPERADMIN accesează**
```bash
GET http://localhost:8000/api/policy/
Authorization: Bearer <superadmin_token>
```
**Expected**: 200 OK cu `default_required_days_per_week` și `updated_at`

**Test 2: Employee încearcă**
```bash
GET http://localhost:8000/api/policy/
Authorization: Bearer <employee_token>
```
**Expected**: 403 Forbidden (doar SUPERADMIN)

---

### POST /api/policy/required-days/

**Test 1: Valoare validă (3)**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <superadmin_token>
{
  "default_required_days_per_week": 3
}
```
**Expected**: 200 OK, `updated_teams_count` > 0 dacă există echipe cu required_days < 3

**Test 2: Valoare out of range (10)**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <superadmin_token>
{
  "default_required_days_per_week": 10
}
```
**Expected**: 400 Bad Request cu mesaj de eroare

**Test 3: Valoare negativă (-1)**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <superadmin_token>
{
  "default_required_days_per_week": -1
}
```
**Expected**: 400 Bad Request

**Test 4: Valoare string ("abc")**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <superadmin_token>
{
  "default_required_days_per_week": "abc"
}
```
**Expected**: 400 Bad Request

**Test 5: Câmp lipsă**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <superadmin_token>
{}
```
**Expected**: 400 Bad Request

**Test 6: Employee încearcă**
```bash
POST http://localhost:8000/api/policy/required-days/
Authorization: Bearer <employee_token>
{
  "default_required_days_per_week": 3
}
```
**Expected**: 403 Forbidden

**Test 7: Actualizare care ridică echipele**
- Creează o echipă cu `required_days_per_week = 1`
- Setează policy la 3
- Verifică că echipa a fost actualizată la 3

**Test 8: Actualizare care NU scade echipele**
- Creează o echipă cu `required_days_per_week = 5`
- Setează policy la 3
- Verifică că echipa rămâne la 5 (nu se scade)

---

## 2. Team Presence Policy

### PATCH /api/teams/{id}/presence-policy/

**Test 1: SUPERADMIN modifică orice echipă**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_days_per_week": 3
}
```
**Expected**: 200 OK

**Test 2: Manager modifică propria echipă**
```bash
# Obține token pentru manager-ul echipei
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <manager_token>
{
  "required_days_per_week": 2,
  "required_weekdays": [0, 2, 4]
}
```
**Expected**: 200 OK

**Test 3: Manager modifică altă echipă**
```bash
# Manager-ul echipei 1 încearcă să modifice echipa 2
PATCH http://localhost:8000/api/teams/2/presence-policy/
Authorization: Bearer <manager_team1_token>
{
  "required_days_per_week": 2
}
```
**Expected**: 403 Forbidden

**Test 4: Employee încearcă să modifice**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <employee_token>
{
  "required_days_per_week": 2
}
```
**Expected**: 403 Forbidden

**Test 5: Manager modifică echipă fără manager**
```bash
# Creează o echipă fără manager (manager=null)
# Employee încearcă să o modifice
PATCH http://localhost:8000/api/teams/{id}/presence-policy/
Authorization: Bearer <employee_token>
{
  "required_days_per_week": 2
}
```
**Expected**: 403 Forbidden

**Test 6: required_days_per_week = null**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_days_per_week": null
}
```
**Expected**: 200 OK, echipa folosește default-ul org

**Test 7: required_weekdays cu duplicate**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_weekdays": [0, 0, 1, 1, 2]
}
```
**Expected**: 200 OK, `required_weekdays` = [0, 1, 2] (duplicate eliminate, sortat)

**Test 8: required_weekdays cu valori out of range**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_weekdays": [-1, 8]
}
```
**Expected**: 400 Bad Request

**Test 9: required_weekdays = null**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_weekdays": null
}
```
**Expected**: 200 OK, fără restricții pe zile

**Test 10: required_weekdays nu e listă**
```bash
PATCH http://localhost:8000/api/teams/1/presence-policy/
Authorization: Bearer <superadmin_token>
{
  "required_weekdays": "not a list"
}
```
**Expected**: 400 Bad Request

---

## 3. Desk Over-Quota

### GET /api/appointments/desk-overquota?date=YYYY-MM-DD

**Test 1: Parametru date lipsă**
```bash
GET http://localhost:8000/api/appointments/desk-overquota/
Authorization: Bearer <superadmin_token>
```
**Expected**: 400 Bad Request cu mesaj "date este obligatoriu"

**Test 2: Format date invalid**
```bash
GET http://localhost:8000/api/appointments/desk-overquota/?date=2024-01-15T10:00:00
Authorization: Bearer <superadmin_token>
```
**Expected**: 400 Bad Request

**Test 3: Format date invalid (alt format)**
```bash
GET http://localhost:8000/api/appointments/desk-overquota/?date=15/01/2024
Authorization: Bearer <superadmin_token>
```
**Expected**: 400 Bad Request

**Test 4: Categoria "birou" nu există**
```bash
GET http://localhost:8000/api/appointments/desk-overquota/?date=2024-01-15
Authorization: Bearer <superadmin_token>
```
**Expected**: 404 Not Found cu mesaj "Categoria 'birou' nu există"

**Test 5: Fără rezervări în ziua respectivă**
```bash
# Data viitoare fără rezervări
GET http://localhost:8000/api/appointments/desk-overquota/?date=2025-12-31
Authorization: Bearer <superadmin_token>
```
**Expected**: 200 OK, `over_quota_users` = []

**Test 6: User fără echipă**
- Creează un user fără echipă
- Creează rezervări pentru birou
- Verifică că folosește default-ul org

**Test 7: Echipă fără required_days_per_week**
- Creează o echipă cu `required_days_per_week = null`
- Verifică că folosește default-ul org

**Test 8: User cu exact required_days (>=)**
- User are 2 zile rezervate, required_days = 2
- **Expected**: User INCLUS în over-quota (>=)

**Test 9: User cu mai puțin decât required_days**
- User are 1 zi rezervată, required_days = 2
- **Expected**: User EXCLUS din over-quota

**Test 10: Calcul corect săptămâna de lucru (Luni-Vineri)**
- Data: 2024-01-17 (Miercuri)
- Săptămâna de lucru: 2024-01-15 (Luni) - 2024-01-19 (Vineri)
- Verifică că `week_start` și `week_end` sunt corecte
- Verifică că doar zilele Luni-Vineri sunt luate în calcul

**Test 11: Zile distincte (nu numără duplicatele)**
- User are 2 rezervări în aceeași zi (15 ianuarie)
- **Expected**: Numără doar 1 zi distinctă

---

## 4. Appointment Overlap (ExclusionConstraint)

### POST /api/appointments/

**Test 1: Suprapunere pe același item**
```bash
# Prima programare
POST http://localhost:8000/api/appointments/
Authorization: Bearer <superadmin_token>
{
  "user": 1,
  "item": 1,
  "start_at": "2024-01-15T10:00:00Z",
  "end_at": "2024-01-15T12:00:00Z"
}

# A doua programare suprapusă
POST http://localhost:8000/api/appointments/
Authorization: Bearer <superadmin_token>
{
  "user": 2,
  "item": 1,
  "start_at": "2024-01-15T11:00:00Z",
  "end_at": "2024-01-15T13:00:00Z"
}
```
**Expected**: Prima 201 Created, a doua 400 Bad Request (ExclusionConstraint)

**Test 2: Suprapunere pe item-uri diferite**
```bash
# Prima programare pe item 1
POST http://localhost:8000/api/appointments/
Authorization: Bearer <superadmin_token>
{
  "user": 1,
  "item": 1,
  "start_at": "2024-01-15T10:00:00Z",
  "end_at": "2024-01-15T12:00:00Z"
}

# A doua programare suprapusă pe item 2
POST http://localhost:8000/api/appointments/
Authorization: Bearer <superadmin_token>
{
  "user": 2,
  "item": 2,
  "start_at": "2024-01-15T11:00:00Z",
  "end_at": "2024-01-15T13:00:00Z"
}
```
**Expected**: Ambele 201 Created (permis, item-uri diferite)

**Test 3: end_at <= start_at**
```bash
POST http://localhost:8000/api/appointments/
Authorization: Bearer <superadmin_token>
{
  "user": 1,
  "item": 1,
  "start_at": "2024-01-15T12:00:00Z",
  "end_at": "2024-01-15T10:00:00Z"
}
```
**Expected**: 400 Bad Request (CheckConstraint sau ValidationError)

---

## 5. Request Approval

### POST /api/requests/{id}/approve/

**Test 1: SUPERADMIN aprobă**
```bash
POST http://localhost:8000/api/requests/1/approve/
Authorization: Bearer <superadmin_token>
```
**Expected**: 200 OK, `status` = "APPROVED", `decided_by` = superadmin

**Test 2: Employee încearcă să aprobe**
```bash
POST http://localhost:8000/api/requests/1/approve/
Authorization: Bearer <employee_token>
```
**Expected**: 403 Forbidden

**Test 3: Request nu e în status WAITING**
```bash
# Aprobă un request deja aprobat
POST http://localhost:8000/api/requests/1/approve/
Authorization: Bearer <superadmin_token>
```
**Expected**: 400 Bad Request cu mesaj că request-ul nu e în status WAITING

---

## 6. Team Management

### POST /api/teams/

**Test 1: SUPERADMIN creează echipă**
```bash
POST http://localhost:8000/api/teams/
Authorization: Bearer <superadmin_token>
{
  "name": "New Team",
  "manager": null
}
```
**Expected**: 201 Created

**Test 2: Employee încearcă să creeze**
```bash
POST http://localhost:8000/api/teams/
Authorization: Bearer <employee_token>
{
  "name": "New Team"
}
```
**Expected**: 403 Forbidden

**Test 3: Nume duplicat**
```bash
POST http://localhost:8000/api/teams/
Authorization: Bearer <superadmin_token>
{
  "name": "IT Department"  # Nume deja existent
}
```
**Expected**: 400 Bad Request (unique constraint)

---

## Checklist Final

- [ ] Toate endpoint-urile de policy funcționează
- [ ] Validările pentru required_days_per_week funcționează
- [ ] Validările pentru required_weekdays funcționează
- [ ] Permisiunile pentru manager funcționează
- [ ] Desk over-quota calculează corect
- [ ] ExclusionConstraint blochează suprapuneri
- [ ] Toate edge case-urile sunt acoperite

