# Sistem de Notificări - Implementare Completă

## 📋 Rezumat

Sistemul de notificări prin email este acum complet implementat pentru cele 3 tipuri de notificări:

1. **Rezumat Programare** (`APPOINTMENT_SUMMARY`) - trimis când se creează o programare nouă
2. **Schimbare Status Cerere** (`REQUEST_STATUS`) - trimis când se schimbă statusul unei cereri (APPROVED/DISMISSED)
3. **Cerere Eliberare Birou** (`DESK_RELEASE_ASK`) - trimis când se cere eliberarea unui birou (over-quota)

## 🏗️ Arhitectură

### Modele

1. **NotificationEvent** - Evenimentul brut produs de business logic (immutable)
2. **EmailOutbox** - Coadă tranzacțională pentru email-uri de trimis (transactional outbox pattern)
3. **EmailDelivery** - Audit final pentru livrare (trasabilitate)
4. **UserEmailPreference** - Preferințe per user (on/off per tip + frecvență)

### Servicii

- `notify_appointment_summary(appointment)` - Creează eveniment și mesaj în outbox pentru rezumat programare
- `notify_request_status(request_obj)` - Creează eveniment și mesaj în outbox pentru schimbare status
- `notify_desk_release_batch(date_obj, overquota_users, requester_user)` - Creează evenimente și mesaje pentru eliberare birou

### Email Sender

- `render_email_template(outbox)` - Renderizează template-urile HTML și text
- `send_email_from_outbox(outbox)` - Trimite email-ul efectiv
- `process_outbox_message(outbox)` - Procesează un mesaj din outbox (cu retry logic)

### Management Command

- `python manage.py send_emails` - Procesează coada de email-uri

## 🚀 Utilizare

### 1. Configurare Email

În `settings.py`, email-urile sunt configurate pentru development (console backend):

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@molsoncoors.com'
```

Pentru producție, configurează SMTP sau un serviciu extern (SendGrid, AWS SES, etc.):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### 2. Procesare Email-uri

Rulează management command-ul pentru a procesa coada de email-uri:

```bash
# Procesează toate mesajele din coadă
python manage.py send_emails

# Procesează un număr limitat de mesaje
python manage.py send_emails --max-messages 100

# Procesează în batch-uri mai mici
python manage.py send_emails --batch-size 25

# Simulează procesarea (dry-run)
python manage.py send_emails --dry-run
```

### 3. Automatizare (Recomandat)

Pentru producție, configurează un cron job sau Celery task pentru a rula periodic:

```bash
# Cron job (rulează la fiecare 5 minute)
*/5 * * * * cd /path/to/project && python manage.py send_emails
```

Sau folosește Celery (viitor):

```python
# tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def process_email_queue():
    call_command('send_emails')
```

## 📧 Tipuri de Notificări

### 1. Rezumat Programare

**Când se declanșează:**
- Când se creează un Appointment nou (în `AppointmentViewSet.perform_create`)

**Template:**
- `templates/emails/ro/appointment_summary.html`
- `templates/emails/ro/appointment_summary.txt`

**Context:**
- `user` - informații despre utilizator
- `item` - informații despre item (birou, sală, etc.)
- `room` - informații despre cameră
- `start_at` - data și ora de început (format: `dd.mm.yyyy HH:MM`)
- `end_at` - data și ora de sfârșit (format: `dd.mm.yyyy HH:MM`)

### 2. Schimbare Status Cerere

**Când se declanșează:**
- Când o Request trece din WAITING în APPROVED sau DISMISSED (în `RequestViewSet.approve` și `RequestViewSet.dismiss`)

**Template:**
- `templates/emails/ro/request_status.html`
- `templates/emails/ro/request_status.txt`

**Context:**
- `user` - informații despre utilizator
- `room` - informații despre cameră
- `status` - statusul cererii (APPROVED/DISMISSED)
- `status_display` - statusul afișat (formatat)
- `note` - notă adăugată (dacă există)
- `decided_by` - numele persoanei care a decis

### 3. Cerere Eliberare Birou

**Când se declanșează:**
- Când se apelează endpoint-ul `desk-overquota` și există utilizatori over-quota (în `AppointmentViewSet.desk_overquota`)

**Template:**
- `templates/emails/ro/desk_release_ask.html`
- `templates/emails/ro/desk_release_ask.txt`

**Context:**
- `user` - utilizatorul care trebuie să elibereze biroul
- `date` - data pentru care se cere eliberarea (format: `dd.mm.yyyy`)
- `requester` - informații despre utilizatorul care cere eliberarea
- `appointments` - lista de programări ale utilizatorului pentru data respectivă

## 🔧 Debugging

### Admin Interface

Toate modelele sunt înregistrate în Django Admin pentru debugging:

- **NotificationEvent** - vezi toate evenimentele create
- **EmailOutbox** - vezi toate mesajele din coadă (status, attempts, errors)
- **EmailDelivery** - vezi istoricul livrărilor
- **UserEmailPreference** - gestionează preferințele utilizatorilor

### Logging

Sistemul folosește Python logging. Verifică log-urile pentru:
- Erori la renderizarea template-urilor
- Erori la trimiterea email-urilor
- Mesaje procesate cu succes

### Verificare Status

```python
from apps.notify.models import EmailOutbox

# Mesaje în așteptare
pending = EmailOutbox.objects.filter(sent_at__isnull=True)

# Mesaje trimise
sent = EmailOutbox.objects.filter(sent_at__isnotnull=True)

# Mesaje eșuate (depășit numărul maxim de încercări)
failed = EmailOutbox.objects.filter(attempts__gte=3, sent_at__isnull=True)
```

## ⚙️ Configurare Preferințe Utilizator

Utilizatorii pot controla ce notificări primesc prin modelul `UserEmailPreference`:

```python
from apps.notify.models import UserEmailPreference
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='john')

# Obține sau creează preferințe
prefs, created = UserEmailPreference.objects.get_or_create(user=user)

# Dezactivează notificările pentru appointment summary
prefs.appointment_summary = False
prefs.save()
```

## 🔄 Retry Logic

Sistemul include retry logic automat:

- **Max attempts:** 3 încercări (configurabil în `process_outbox_message`)
- **Lock mechanism:** Mesajele sunt blocate timp de 10 minute pentru a evita procesarea paralelă
- **Error tracking:** Erorile sunt salvate în câmpul `error` al modelului `EmailOutbox`

## 📝 Note Importante

1. **Idempotency:** Sistemul folosește `idempotency_key` pentru a preveni duplicate-urile
2. **Transactional Outbox:** Pattern-ul asigură consistența datelor (ACID)
3. **Template-uri:** Template-urile sunt în `templates/emails/ro/` (pentru limba română)
4. **Development:** În development, email-urile se afișează în consolă (console backend)
5. **Production:** Pentru producție, configurează SMTP sau un serviciu extern

## 🔄 Celery Integration (Completat)

Sistemul folosește acum Celery pentru procesarea automată a email-urilor:

### Configurare

- **Worker:** `celery_worker` - procesează task-urile
- **Beat:** `celery_beat` - programează task-urile periodice
- **Schedule:** Procesează coada de email-uri la fiecare 60 de secunde

### Task-uri Disponibile

1. **`notify.process_email_queue`** - Procesează toate mesajele din EmailOutbox
   - Rulează automat la fiecare 60 de secunde (configurat în Beat)
   - Poate fi apelat manual: `process_email_queue.delay()`

2. **`notify.send_single_email`** - Trimite un singur email
   - Utilizat pentru retry-uri sau trimitere imediată
   - Apel: `send_single_email.delay(outbox_id)`

### Verificare Status

```bash
# Verifică worker-ul
docker-compose logs celery_worker

# Verifică beat scheduler
docker-compose logs celery_beat

# Verifică toate containerele
docker-compose ps
```

## 🚧 Pași Următori (Opțional)

1. **Email Provider:** Integrare cu SendGrid, AWS SES, sau alt provider
2. **Webhooks:** Webhooks pentru status updates de la provider
3. **Analytics:** Dashboard pentru statistici despre notificări
4. **Templates Multiple Languages:** Suport pentru mai multe limbi
5. **Retry Strategy:** Strategie avansată de retry cu exponential backoff

