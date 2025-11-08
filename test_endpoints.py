"""
Script pentru testarea endpoint-urilor și edge case-urilor.
Rulează: python test_endpoints.py
"""
import os
import django
import requests
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import Team, OrgPolicy, ItemCategory, Item, Room, Appointment

User = get_user_model()

BASE_URL = 'http://localhost:8000/api'
print("=" * 80)
print("TESTARE ENDPOINT-URI - EDGE CASES")
print("=" * 80)

# Colori pentru output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}[TEST]{Colors.END} {name}")

def print_success(message):
    print(f"{Colors.GREEN}[OK]{Colors.END} {message}")

def print_error(message):
    print(f"{Colors.RED}[FAIL]{Colors.END} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {message}")

def get_token(username, password):
    """Obține token JWT pentru un user."""
    response = requests.post(
        f'{BASE_URL}/auth/login/',
        json={'username': username, 'password': password}
    )
    if response.status_code == 200:
        return response.json()['access']
    return None

def test_policy_endpoints():
    """Testează endpoint-urile de policy."""
    print_test("POLICY ENDPOINTS")
    
    # Obține token pentru superadmin
    token = get_token('super123', 'super123')
    if not token:
        print_error("Nu s-a putut obține token pentru superadmin")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: GET policy
    print("  → GET /api/policy/")
    response = requests.get(f'{BASE_URL}/policy/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print_success(f"Policy curent: {data.get('default_required_days_per_week')} zile")
    else:
        print_error(f"Status: {response.status_code}")
    
    # Test 2: POST policy - valoare validă
    print("  → POST /api/policy/required-days/ (valoare validă: 3)")
    response = requests.post(
        f'{BASE_URL}/policy/required-days/',
        headers=headers,
        json={'default_required_days_per_week': 3}
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Policy actualizat: {data.get('default_required_days_per_week')} zile")
        print_success(f"Echipe actualizate: {data.get('updated_teams_count')}")
    else:
        print_error(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test 3: POST policy - valoare invalidă (out of range)
    print("  → POST /api/policy/required-days/ (valoare invalidă: 10)")
    response = requests.post(
        f'{BASE_URL}/policy/required-days/',
        headers=headers,
        json={'default_required_days_per_week': 10}
    )
    if response.status_code == 400:
        print_success("Validare corectă: valoare out of range respinsă")
    else:
        print_error(f"Ar trebui să fie 400, dar este {response.status_code}")
    
    # Test 4: POST policy - valoare invalidă (string)
    print("  → POST /api/policy/required-days/ (valoare invalidă: 'abc')")
    response = requests.post(
        f'{BASE_URL}/policy/required-days/',
        headers=headers,
        json={'default_required_days_per_week': 'abc'}
    )
    if response.status_code == 400:
        print_success("Validare corectă: string respins")
    else:
        print_error(f"Ar trebui să fie 400, dar este {response.status_code}")

def test_team_presence_policy():
    """Testează endpoint-ul pentru politica de prezență a echipei."""
    print_test("TEAM PRESENCE POLICY")
    
    # Obține token pentru superadmin
    superadmin_token = get_token('super123', 'super123')
    if not superadmin_token:
        print_error("Nu s-a putut obține token pentru superadmin")
        return
    
    # Obține token pentru un employee (care nu e manager)
    employee_token = get_token('john.doe', 'test123')
    if not employee_token:
        print_error("Nu s-a putut obține token pentru employee")
        return
    
    # Găsește o echipă
    team = Team.objects.first()
    if not team:
        print_warning("Nu există echipe în baza de date")
        return
    
    print(f"  → Testăm cu echipa: {team.name} (ID: {team.id})")
    
    # Test 1: SUPERADMIN modifică politica
    print("  → PATCH /api/teams/{id}/presence-policy/ (SUPERADMIN)")
    headers = {'Authorization': f'Bearer {superadmin_token}'}
    response = requests.patch(
        f'{BASE_URL}/teams/{team.id}/presence-policy/',
        headers=headers,
        json={'required_days_per_week': 3}
    )
    if response.status_code == 200:
        print_success("SUPERADMIN poate modifica politica")
    else:
        print_error(f"Status: {response.status_code}, Response: {response.text}")
    
    # Test 2: Employee încearcă să modifice (ar trebui să eșueze)
    print("  → PATCH /api/teams/{id}/presence-policy/ (Employee - ar trebui să eșueze)")
    headers = {'Authorization': f'Bearer {employee_token}'}
    response = requests.patch(
        f'{BASE_URL}/teams/{team.id}/presence-policy/',
        headers=headers,
        json={'required_days_per_week': 2}
    )
    if response.status_code == 403:
        print_success("Employee corect respins (403)")
    else:
        print_error(f"Ar trebui să fie 403, dar este {response.status_code}")
    
    # Test 3: Manager modifică propria echipă
    if team.manager:
        manager_token = get_token(team.manager.username, 'test123')
        if manager_token:
            print(f"  → PATCH /api/teams/{team.id}/presence-policy/ (Manager: {team.manager.username})")
            headers = {'Authorization': f'Bearer {manager_token}'}
            response = requests.patch(
                f'{BASE_URL}/teams/{team.id}/presence-policy/',
                headers=headers,
                json={'required_days_per_week': 2, 'required_weekdays': [0, 2, 4]}
            )
            if response.status_code == 200:
                print_success("Manager poate modifica politica echipei sale")
            else:
                print_error(f"Status: {response.status_code}, Response: {response.text}")
        else:
            print_warning(f"Nu s-a putut obține token pentru manager {team.manager.username}")
    else:
        print_warning(f"Echipa {team.name} nu are manager setat")
    
    # Test 4: Validare required_weekdays - duplicate
    print("  → PATCH /api/teams/{id}/presence-policy/ (duplicate în required_weekdays)")
    headers = {'Authorization': f'Bearer {superadmin_token}'}
    response = requests.patch(
        f'{BASE_URL}/teams/{team.id}/presence-policy/',
        headers=headers,
        json={'required_weekdays': [0, 0, 1, 1, 2]}
    )
    if response.status_code == 200:
        data = response.json()
        weekdays = data.get('required_weekdays', [])
        if weekdays == [0, 1, 2]:
            print_success("Duplicate-urile au fost eliminate și sortate corect")
        else:
            print_error(f"Duplicate-urile nu au fost eliminate: {weekdays}")
    else:
        print_error(f"Status: {response.status_code}")

def test_desk_overquota():
    """Testează endpoint-ul desk-overquota."""
    print_test("DESK OVER-QUOTA")
    
    # Obține token
    token = get_token('super123', 'super123')
    if not token:
        print_error("Nu s-a putut obține token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: date lipsă
    print("  → GET /api/appointments/desk-overquota/ (fără parametru date)")
    response = requests.get(
        f'{BASE_URL}/appointments/desk-overquota/',
        headers=headers
    )
    if response.status_code == 400:
        print_success("Validare corectă: date lipsă respins")
    else:
        print_error(f"Ar trebui să fie 400, dar este {response.status_code}")
    
    # Test 2: date format invalid
    print("  → GET /api/appointments/desk-overquota/?date=invalid")
    response = requests.get(
        f'{BASE_URL}/appointments/desk-overquota/?date=invalid',
        headers=headers
    )
    if response.status_code == 400:
        print_success("Validare corectă: format invalid respins")
    else:
        print_error(f"Ar trebui să fie 400, dar este {response.status_code}")
    
    # Test 3: date validă (dacă există categoria "birou")
    today = datetime.now().date()
    print(f"  → GET /api/appointments/desk-overquota/?date={today}")
    response = requests.get(
        f'{BASE_URL}/appointments/desk-overquota/?date={today.isoformat()}',
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print_success(f"Endpoint funcționează: {data.get('total_over_quota', 0)} utilizatori over-quota")
    elif response.status_code == 404:
        print_warning("Categoria 'birou' nu există. Creează-o pentru a testa complet.")
    else:
        print_error(f"Status: {response.status_code}, Response: {response.text}")

def test_appointment_overlap():
    """Testează ExclusionConstraint pentru suprapuneri."""
    print_test("APPOINTMENT OVERLAP (ExclusionConstraint)")
    
    # Găsește un item activ
    item = Item.objects.filter(status=Item.ACTIVE).first()
    if not item:
        print_warning("Nu există item-uri active pentru testare")
        return
    
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print_warning("Nu există useri non-superadmin pentru testare")
        return
    
    token = get_token('super123', 'super123')
    if not token:
        print_error("Nu s-a putut obține token")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Creează prima programare
    now = datetime.now()
    start1 = now + timedelta(days=1, hours=10)
    end1 = start1 + timedelta(hours=2)
    
    print(f"  → POST /api/appointments/ (prima programare: {start1} - {end1})")
    response = requests.post(
        f'{BASE_URL}/appointments/',
        headers=headers,
        json={
            'user': user.id,
            'item': item.id,
            'start_at': start1.isoformat(),
            'end_at': end1.isoformat()
        }
    )
    if response.status_code == 201:
        appointment1 = response.json()
        print_success(f"Prima programare creată: ID {appointment1.get('id')}")
        
        # Încearcă să creezi o programare suprapusă
        start2 = start1 + timedelta(hours=1)  # Suprapunere
        end2 = end1 + timedelta(hours=1)
        
        print(f"  → POST /api/appointments/ (suprapunere: {start2} - {end2})")
        response2 = requests.post(
            f'{BASE_URL}/appointments/',
            headers=headers,
            json={
                'user': user.id,
                'item': item.id,
                'start_at': start2.isoformat(),
                'end_at': end2.isoformat()
            }
        )
        if response2.status_code == 400:
            print_success("ExclusionConstraint funcționează: suprapunerea a fost respinsă")
        else:
            print_error(f"Ar trebui să fie 400, dar este {response2.status_code}")
            print_error(f"Response: {response2.text}")
    else:
        print_error(f"Nu s-a putut crea prima programare: {response.status_code}")

def main():
    """Rulează toate testele."""
    print("\n" + "=" * 80)
    print("INCEPE TESTAREA")
    print("=" * 80)
    print("\n[!] Asigura-te ca serverul Django ruleaza: python manage.py runserver")
    print("[!] Asigura-te ca exista date de test: python manage.py seed_data")
    print("\n[!] Incepem testarea in 2 secunde...")
    import time
    time.sleep(2)
    
    try:
        test_policy_endpoints()
        test_team_presence_policy()
        test_desk_overquota()
        test_appointment_overlap()
        
        print("\n" + "=" * 80)
        print("TESTARE FINALIZATĂ")
        print("=" * 80)
    except requests.exceptions.ConnectionError:
        print_error("Nu s-a putut conecta la server. Asigură-te că rulează: python manage.py runserver")
    except Exception as e:
        print_error(f"Eroare neașteptată: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

