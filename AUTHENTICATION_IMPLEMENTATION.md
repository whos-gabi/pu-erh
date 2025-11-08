# Implementare Autentificare - Explicații Pas cu Pas

## 📋 Ce am implementat

Am creat sistemul complet de autentificare cu JWT și gestionarea utilizatorilor conform cerințelor tale.

---

## 🔧 Pasul 1: Actualizarea Modelului User

### Ce am făcut:
Am adăugat o **constrângere de bază de date** care permite **maxim un singur SUPERADMIN** în sistem.

### Cod în `apps/core/models.py`:
```python
class User(AbstractUser):
    # ... câmpuri existente ...
    
    class Meta:
        constraints = [
            # Permite maxim UN rând cu is_superuser = True
            models.UniqueConstraint(
                fields=['is_superuser'],
                condition=Q(is_superuser=True),
                name='unique_single_superadmin',
            ),
        ]
```

### Explicație:
- **`UniqueConstraint`**: Creează o constrângere unică în PostgreSQL
- **`condition=Q(is_superuser=True)`**: Constraint-ul se aplică DOAR pentru rândurile unde `is_superuser=True`
- **Rezultat**: Dacă încerci să creezi un al doilea utilizator cu `is_superuser=True`, PostgreSQL va arunca o eroare

### De ce e important:
- Asigură că există un singur SUPERADMIN în sistem
- Validarea se face la nivel de bază de date (nu doar în Python)
- Previne erorile chiar dacă ai bug-uri în cod

---

## 🔐 Pasul 2: Configurarea JWT Authentication

### Ce am făcut:
Am configurat **JWT (JSON Web Tokens)** pentru autentificare în loc de session-based auth.

### Cod în `config/settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Token expiră după 1 oră
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Refresh token expiră după 7 zile
    'ROTATE_REFRESH_TOKENS': True,  # Reînnoiește automat token-ul
}
```

### Explicație:
- **JWT Authentication**: Fiecare request trebuie să includă un token în header-ul `Authorization: Bearer <token>`
- **ACCESS_TOKEN**: Token-ul principal, expiră după 1 oră
- **REFRESH_TOKEN**: Token pentru reînnoire, expiră după 7 zile
- **ROTATE_REFRESH_TOKENS**: Când reînnoiești token-ul, vechiul devine invalid (securitate mai bună)

### De ce JWT:
- **Stateless**: Serverul nu ține minte sesiuni
- **Scalabil**: Funcționează bine cu multiple servere
- **Standard**: Format larg acceptat
- **Flexibil**: Poți adăuga informații în token (ex: `is_superuser`)

---

## 🛡️ Pasul 3: Permission Classes

### Ce am făcut:
Am creat clase de permisiuni reutilizabile pentru controlul accesului.

### Cod în `apps/core/permissions.py`:

#### 1. `IsSuperAdmin`
```python
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser
```
**Folosire**: Doar SUPERADMIN poate accesa endpoint-ul

#### 2. `IsOwner`
```python
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
```
**Folosire**: Doar proprietarul obiectului poate accesa

#### 3. `IsOwnerOrSuperAdmin`
```python
class IsOwnerOrSuperAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user
```
**Folosire**: Proprietarul SAU SUPERADMIN pot accesa

### Explicație:
- **`has_permission`**: Verifică permisiuni la nivel de view (înainte de a accesa obiectul)
- **`has_object_permission`**: Verifică permisiuni la nivel de obiect (după ce obiectul a fost găsit)
- **Reutilizabil**: Poți folosi aceleași clase în multiple viewsets

---

## 📝 Pasul 4: Serializers

### Ce am făcut:
Am creat serializers pentru gestionarea utilizatorilor.

### Cod în `apps/core/serializers.py`:

#### 1. `UserSerializer` - Serializare de bază
```python
class UserSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True)
    team = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        fields = ['id', 'username', 'email', 'is_superuser', ...]
        read_only_fields = ['id', 'is_superuser', ...]
```
**Folosire**: Pentru listare și detalii

#### 2. `UserCreateSerializer` - Creare utilizator
```python
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise ValidationError('Parolele nu se potrivesc.')
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)  # Hash-uiește parola
        return user
```
**Folosire**: Doar pentru creare (POST)

#### 3. `UserProfileSerializer` - Profil utilizator
```python
class UserProfileSerializer(serializers.ModelSerializer):
    # Similar cu UserSerializer, dar pentru /api/me
```
**Folosire**: Pentru endpoint-ul `/api/me`

### Explicație:
- **`write_only=True`**: Câmpul nu este inclus în răspuns (securitate pentru parolă)
- **`validators=[validate_password]`**: Validează parola conform regulilor Django
- **`set_password()`**: Hash-uiește parola înainte de salvare (nu stochează parola în plain text)

---

## 🎯 Pasul 5: ViewSets pentru Autentificare

### Ce am făcut:
Am creat viewsets pentru gestionarea autentificării și profilului.

### Cod în `apps/core/auth_views.py`:

#### 1. `MeViewSet` - Profilul utilizatorului curent
```python
class MeViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']  # Doar read și update
    
    def get_object(self):
        return self.request.user  # Returnează utilizatorul curent
```
**Endpoint**: `GET /api/me/` - Obține profilul
**Endpoint**: `PUT /api/me/` - Actualizează profilul complet
**Endpoint**: `PATCH /api/me/` - Actualizează profilul parțial

#### 2. `UserViewSet` - Gestionarea utilizatorilor
```python
class UserViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'list':
            return [IsSuperAdmin()]  # Doar SUPERADMIN vede lista
        elif self.action == 'retrieve':
            return [IsOwnerOrSuperAdmin()]  # Employee doar propriul profil
        elif self.action in ['create', 'update', 'destroy']:
            return [IsSuperAdmin()]  # Doar SUPERADMIN modifică
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()  # SUPERADMIN vede tot
        return User.objects.filter(id=self.request.user.id)  # Employee doar self
```
**Endpoint**: `GET /api/users/` - Listă (doar SUPERADMIN)
**Endpoint**: `GET /api/users/{id}/` - Detalii (Employee doar self)
**Endpoint**: `POST /api/users/` - Creare (doar SUPERADMIN)
**Endpoint**: `PATCH /api/users/{id}/` - Actualizare (doar SUPERADMIN)
**Endpoint**: `DELETE /api/users/{id}/` - Ștergere (doar SUPERADMIN)

#### 3. `CustomTokenObtainPairView` - Login
```python
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
```
**Endpoint**: `POST /api/auth/login/` - Obține token JWT

### Explicație:
- **`get_permissions()`**: Permite permisiuni diferite pentru acțiuni diferite
- **`get_queryset()`**: Filtrează datele în funcție de permisiuni
- **`http_method_names`**: Limitează metodele HTTP permise

---

## 🔗 Pasul 6: Configurarea URLs

### Ce am făcut:
Am configurat rutele pentru toate endpoint-urile.

### Cod în `config/urls.py`:
```python
# Autentificare JWT
path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

# Router pentru viewsets
router.register(r'me', MeViewSet, basename='me'),
router.register(r'users', UserViewSet, basename='user'),
```

### Endpoint-uri disponibile:

#### Autentificare:
- `POST /api/auth/login/` - Login (obține token)
- `POST /api/auth/refresh/` - Reînnoiește token-ul

#### Profil:
- `GET /api/me/` - Obține profilul curent
- `PUT /api/me/` - Actualizează profilul complet
- `PATCH /api/me/` - Actualizează profilul parțial

#### Utilizatori (doar SUPERADMIN):
- `GET /api/users/` - Listă utilizatori
- `GET /api/users/{id}/` - Detalii utilizator
- `POST /api/users/` - Creează utilizator
- `PATCH /api/users/{id}/` - Actualizează utilizator
- `DELETE /api/users/{id}/` - Șterge utilizator

---

## 🧪 Cum să testezi

### 1. Instalează dependențele:
```bash
pip install -r requirements.txt
```

### 2. Aplică migrațiile:
```bash
python manage.py migrate
```

### 3. Creează un SUPERADMIN:
```bash
python manage.py createsuperuser
```

### 4. Rulează serverul:
```bash
python manage.py runserver
```

### 5. Testează în Swagger:
- Deschide `http://localhost:8000/api/docs/`
- Click pe `POST /api/auth/login/`
- Completează username și password
- Click "Execute"
- Copiază `access` token-ul din răspuns

### 6. Testează endpoint-ul `/api/me/`:
- Click pe `GET /api/me/`
- Click pe butonul "Authorize" (în partea de sus)
- Introdu: `Bearer <token-ul-copiat>`
- Click "Authorize"
- Click "Execute"
- Ar trebui să vezi profilul tău

---

## 📊 Matricea de Permisiuni Implementată

| Endpoint | Method | Employee | SUPERADMIN |
|----------|--------|----------|------------|
| `/api/me` | GET | ✅ Self | ✅ Self |
| `/api/me` | PUT/PATCH | ✅ Self | ✅ Self |
| `/api/users` | GET | ❌ | ✅ All |
| `/api/users/{id}` | GET | ✅ Self only | ✅ All |
| `/api/users` | POST | ❌ | ✅ |
| `/api/users/{id}` | PATCH | ❌ | ✅ |
| `/api/users/{id}` | DELETE | ❌ | ✅ |

---

## 🎓 Concepte importante

### 1. JWT Token Flow:
```
Client → POST /api/auth/login/ → Server
Client ← {access, refresh} ← Server

Client → GET /api/me/ + Header: Authorization: Bearer <access> → Server
Client ← {user data} ← Server
```

### 2. Permission Classes:
- Se verifică **înainte** de a executa view-ul
- Dacă returnează `False`, se aruncă `PermissionDenied`
- Pot verifica la nivel de **view** sau **object**

### 3. Serializers:
- **Input**: Validează datele primite de la client
- **Output**: Formatează datele pentru răspuns
- **Transformare**: Convertește între format Python și JSON

### 4. ViewSets:
- **CRUD automat**: Create, Read, Update, Delete
- **Router**: Generează automat URL-urile
- **Actions**: Poți adăuga acțiuni custom (ex: `approve`, `dismiss`)

---

## ✅ Ce am realizat

1. ✅ Constraint pentru SUPERADMIN unic în baza de date
2. ✅ JWT Authentication configurat
3. ✅ Permission classes (IsSuperAdmin, IsOwner, etc.)
4. ✅ Serializers pentru User (create, update, profile)
5. ✅ ViewSet pentru `/api/me/`
6. ✅ ViewSet pentru `/api/users/` cu permisiuni corecte
7. ✅ Endpoint-uri de login și refresh
8. ✅ Migrații aplicate

---

## 🚀 Următorii pași

Acum poți continua cu:
- Endpoint-uri pentru Rooms, Items, Requests, Appointments
- Implementarea logicii de business pentru Requests (approve/dismiss)
- Implementarea logicii pentru Appointments cu anti-overlap

Totul este pregătit și funcțional! 🎉

