# Edge Cases și Testare Endpoint-uri

## 🎯 Edge Cases Identificate

### 1. Policy Endpoints

#### POST /api/policy/required-days/
**Edge Cases**:
- ✅ Valori valide: 0, 1, 2, 3, 4, 5, 6, 7
- ❌ Valori invalide: -1, 8, 10, "abc", null
- ✅ Actualizare de la 2 la 3: echipele cu required_days=1 sau 2 trebuie să fie ridicate
- ✅ Actualizare de la 3 la 2: echipele cu required_days=3 sau mai mare NU trebuie scăzute
- ✅ Echipe cu required_days_per_week=null: rămân null (folosesc default-ul org)

#### PATCH /api/teams/{id}/presence-policy/
**Edge Cases**:
- ✅ Manager modifică propria echipă: permis
- ❌ Manager modifică altă echipă: 403 Forbidden
- ❌ Employee modifică echipă: 403 Forbidden
- ✅ SUPERADMIN modifică orice echipă: permis
- ✅ required_days_per_week=null: folosește default-ul org
- ✅ required_weekdays=null: fără restricții pe zile
- ❌ required_weekdays=[0, 0, 1]: duplicate trebuie eliminate
- ❌ required_weekdays=[-1, 8]: valori out of range
- ✅ required_weekdays=[6, 0, 3]: trebuie sortat automat

### 2. Desk Over-Quota

#### GET /api/appointments/desk-overquota?date=YYYY-MM-DD
**Edge Cases**:
- ❌ date lipsă: 400 Bad Request
- ❌ date format invalid: "2024-01-15T10:00:00", "15/01/2024": 400 Bad Request
- ❌ Categoria "birou" nu există: 404 Not Found
- ✅ Fără rezervări în ziua respectivă: returnează lista goală
- ✅ User fără echipă: folosește default-ul org
- ✅ Echipă fără required_days_per_week: folosește default-ul org
- ✅ User cu exact required_days: INCLUS în over-quota (>=)
- ✅ User cu mai puțin decât required_days: EXCLUS din over-quota
- ✅ Săptămâna ISO calculată corect (Luni-Duminică)
- ✅ Zile distincte (nu numără duplicatele în aceeași zi)

### 3. Team Management

#### POST /api/teams/
**Edge Cases**:
- ❌ Employee creează echipă: 403 Forbidden
- ✅ SUPERADMIN creează echipă: permis
- ✅ Echipă fără manager: permis (manager=null)
- ❌ Nume duplicat: 400 Bad Request (unique constraint)

#### PATCH /api/teams/{id}/presence-policy/
**Edge Cases**:
- ❌ Manager modifică echipă fără manager: 403 (dacă nu e SUPERADMIN)
- ✅ Manager modifică echipă unde el este manager: permis
- ❌ Manager modifică echipă unde altcineva este manager: 403

### 4. Appointment Overlap

#### POST /api/appointments/
**Edge Cases**:
- ❌ Suprapunere pe același item: ExclusionConstraint ar trebui să blocheze
- ✅ Suprapunere pe item-uri diferite: permis
- ❌ end_at <= start_at: CheckConstraint + ValidationError

### 5. Request Approval

#### POST /api/requests/{id}/approve/
**Edge Cases**:
- ❌ Employee aprobă: 403 Forbidden
- ❌ Request nu e în status WAITING: 400 Bad Request
- ✅ SUPERADMIN aprobă: permis
- ✅ decided_by setat automat la SUPERADMIN

---

## 🧪 Script de Testare

Vom crea un script Python pentru testare automată.

