# 📧 Ghid: Verificare Notificări în Django Admin

## 🎯 Pași pentru Verificare

### 1. Accesează Django Admin

Deschide în browser:
```
http://localhost:8000/admin/
```

**Login:**
- Username: `super123`
- Password: `super123`

---

### 2. Navighează la Notifications

În panoul stâng, găsește secțiunea **NOTIFICATIONS** și vei vedea:

- **Notification Events** - Evenimentele create
- **Email Outbox** - Mesajele de trimis
- **Email Deliveries** - Istoricul livrărilor
- **User Email Preferences** - Preferințele utilizatorilor

---

## 📊 1. Notification Events

**Ce vezi aici:**
- Toate evenimentele de notificare create în sistem
- Tipul evenimentului (APPOINTMENT_SUMMARY, REQUEST_STATUS, DESK_RELEASE_ASK)
- Utilizatorul pentru care este notificarea
- Actorul care a declanșat evenimentul
- Data și ora creării
- Payload-ul (datele evenimentului)

**Cum să filtrezi:**
- Click pe **Type** pentru a filtra după tip
- Click pe **Created at** pentru a filtra după dată
- Folosește bara de căutare pentru a căuta după username sau email

**Exemplu:**
```
Type: APPOINTMENT_SUMMARY
Subject user: super123
Created at: 2025-11-08 18:11
Payload: {"appointment_id": 13, "item_id": 1, "room_id": 1}
```

---

## 📬 2. Email Outbox (Cel Mai Important!)

**Ce vezi aici:**
- Toate mesajele de email care trebuie trimise sau au fost trimise
- Status-ul fiecărui mesaj (În așteptare, Trimis, Eșuat)
- Numărul de încercări
- Erorile (dacă există)

### Coloane Disponibile:

| Coloană | Descriere |
|---------|-----------|
| **ID** | ID-ul unic al mesajului |
| **To** | Adresa de email destinatar |
| **Template** | Tipul de template (appointment_summary, request_status, desk_release_ask) |
| **Locale** | Limba (ro, en) |
| **Scheduled at** | Când ar trebui trimis |
| **Sent at** | Când a fost trimis efectiv (null = încă neprocesat) |
| **Attempts** | Numărul de încercări |
| **Status** | ✓ Trimis / ⏳ În așteptare / ✗ Eșuat |

### Filtrare:

- **Template** - Filtrează după tipul de notificare
- **Locale** - Filtrează după limbă
- **Sent at** - Filtrează după status (trimis/ne trimis)
- **Scheduled at** - Filtrează după dată programată

### Căutare:

Poți căuta după:
- Adresa de email (`to`)
- Tipul de template (`template`)
- Tipul de eveniment (`event__type`)

### Detalii Mesaj:

Click pe un mesaj pentru a vedea:
- **Event** - Evenimentul care a generat mesajul
- **To** - Destinatarul
- **Template** - Template-ul folosit
- **Context** - Datele folosite în template (JSON)
- **Idempotency key** - Cheia pentru prevenirea duplicate-urilor
- **Scheduled at** - Când ar trebui trimis
- **Attempts** - Numărul de încercări
- **Locked at** - Când a fost blocat pentru procesare
- **Sent at** - Când a fost trimis
- **Error** - Mesajul de eroare (dacă există)

---

## ✅ 3. Email Deliveries

**Ce vezi aici:**
- Istoricul complet al livrărilor
- Status-ul fiecărei livrări (SENT, FAILED)
- ID-ul mesajului de la provider (dacă folosești un provider extern)
- Data și ora livrării

**Utilizare:**
- Audit și trasabilitate
- Debugging pentru probleme de livrare
- Statistici despre email-uri trimise

---

## ⚙️ 4. User Email Preferences

**Ce vezi aici:**
- Preferințele fiecărui utilizator pentru notificări
- On/off pentru fiecare tip de notificare
- Frecvența (instant sau daily digest)

**Cum să modifici:**
1. Click pe un utilizator
2. Modifică preferințele:
   - **Appointment summary** - Primește email când creează programare?
   - **Request status** - Primește email când se schimbă statusul cererii?
   - **Desk release ask** - Primește email când i se cere să elibereze biroul?
   - **Frequency** - Instant sau Daily digest
3. Click **Save**

---

## 🧪 Testare Rapidă

### Pasul 1: Creează Notificări de Test

Într-un terminal:
```powershell
docker-compose exec web python test_notifications.py
```

### Pasul 2: Procesează Email-urile

```powershell
docker-compose exec web python manage.py send_emails
```

### Pasul 3: Verifică în Admin

1. Deschide http://localhost:8000/admin/
2. Mergi la **Notifications** → **Email Outbox**
3. Vezi mesajele create și statusul lor

---

## 📈 Interpretare Status

### Status: ⏳ În așteptare
- Mesajul nu a fost încă procesat
- `sent_at` este null
- `attempts` este 0 sau mai mic decât 3

**Acțiune:** Rulează `python manage.py send_emails`

### Status: ✓ Trimis
- Mesajul a fost trimis cu succes
- `sent_at` are o valoare
- `attempts` este mai mare decât 0

**Acțiune:** Verifică în **Email Deliveries** pentru detalii

### Status: ✗ Eșuat
- Mesajul a depășit numărul maxim de încercări (3)
- `sent_at` este încă null
- `attempts` este >= 3
- `error` conține mesajul de eroare

**Acțiune:** Verifică câmpul `error` pentru detalii

---

## 🔍 Debugging

### Mesajele nu sunt procesate

**Verifică:**
1. Rulează `python manage.py send_emails`
2. Verifică log-urile: `docker-compose logs web`
3. Verifică câmpul `error` în Email Outbox

### Mesajele sunt procesate dar nu sunt trimise

**Verifică:**
1. `EMAIL_BACKEND` în `settings.py`
2. Pentru development, ar trebui să fie `console.EmailBackend`
3. Email-urile ar trebui să apară în consolă

### Erori la renderizarea template-urilor

**Verifică:**
1. Template-urile există în `templates/emails/ro/`
2. Context-ul este corect (vezi câmpul `context` în Email Outbox)
3. Verifică log-urile pentru erori detaliate

---

## 📝 Exemple de Utilizare

### Exemplu 1: Verifică toate notificările pentru un utilizator

1. Mergi la **Email Outbox**
2. În bara de căutare, introdu email-ul utilizatorului
3. Vezi toate mesajele pentru acel utilizator

### Exemplu 2: Găsește mesajele eșuate

1. Mergi la **Email Outbox**
2. Filtrează după **Sent at** → "Empty"
3. Sortează după **Attempts** (descrescător)
4. Vezi mesajele care au cel mai multe încercări

### Exemplu 3: Verifică statistici

1. Mergi la **Email Outbox**
2. Vezi totalul de mesaje
3. Filtrează după **Template** pentru a vedea câte de fiecare tip
4. Filtrează după **Sent at** pentru a vedea câte sunt trimise vs în așteptare

---

## ✅ Checklist Verificare

După ce rulezi testele, verifică:

- [ ] **Notification Events** - Există evenimente create?
- [ ] **Email Outbox** - Există mesaje în outbox?
- [ ] **Status** - Mesajele au status corect?
- [ ] **Sent at** - Mesajele procesate au `sent_at` setat?
- [ ] **Email Deliveries** - Există înregistrări de livrare?
- [ ] **Context** - Context-ul mesajelor este corect?
- [ ] **Errors** - Nu există erori în câmpul `error`?

---

## 🎉 Rezultat Așteptat

După testare, ar trebui să vezi:

1. **Notification Events:** 2-3 evenimente (appointment_summary, request_status)
2. **Email Outbox:** 2-3 mesaje cu status "✓ Trimis"
3. **Email Deliveries:** 2-3 înregistrări cu status "SENT"
4. **Context:** Datele corecte pentru fiecare mesaj

---

## 💡 Tips

- Folosește filtrele pentru a găsi rapid mesajele
- Click pe un mesaj pentru a vedea toate detaliile
- Verifică câmpul `context` pentru a vedea datele folosite în template
- Verifică `error` pentru debugging
- Folosește bara de căutare pentru a găsi mesaje specifice

