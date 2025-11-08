"""
Script pentru testarea endpoint-urilor Room și Request după modificări.
Rulează: python test_room_request_endpoints.py
"""
import os
import django
import requests
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import Room, Request

User = get_user_model()

BASE_URL = 'http://localhost:8000/api'
print("=" * 80)
print("TESTARE ENDPOINT-URI ROOM ȘI REQUEST")
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
    try:
        response = requests.post(
            f'{BASE_URL}/auth/login/',
            json={'username': username, 'password': password}
        )
        if response.status_code == 200:
            return response.json()['access']
    except Exception as e:
        print_error(f"Eroare la obținerea token-ului: {e}")
    return None

def test_room_endpoints():
    """Testează endpoint-urile pentru Room."""
    print_test("ROOM ENDPOINTS")
    
    # Obține token pentru superadmin
    token = get_token('super123', 'super123')
    if not token:
        print_error("Nu s-a putut obține token pentru superadmin")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    success = True
    
    # Test 1: GET rooms - verifică că is_active nu mai există
    print("  → GET /api/rooms/")
    try:
        response = requests.get(f'{BASE_URL}/rooms/', headers=headers)
        if response.status_code == 200:
            rooms = response.json()
            if rooms:
                room = rooms[0]
                if 'is_active' in room:
                    print_error("Câmpul 'is_active' încă există în răspuns!")
                    success = False
                else:
                    print_success("Câmpul 'is_active' a fost eliminat corect")
                    print_success(f"Camere găsite: {len(rooms)}")
            else:
                print_warning("Nu există camere în sistem")
        else:
            print_error(f"Status: {response.status_code}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    # Test 2: POST room - verifică că is_active nu mai este acceptat
    print("  → POST /api/rooms/ (fără is_active)")
    try:
        room_data = {
            'code': 'TEST-001',
            'name': 'Sala de test',
            'capacity': 10,
            'features': {'projector': True}
        }
        response = requests.post(
            f'{BASE_URL}/rooms/',
            headers=headers,
            json=room_data
        )
        if response.status_code == 201:
            room = response.json()
            if 'is_active' in room:
                print_error("Câmpul 'is_active' apare în răspuns!")
                success = False
            else:
                print_success(f"Cameră creată: {room.get('code')}")
                # Șterge camera de test
                room_id = room.get('id')
                if room_id:
                    requests.delete(f'{BASE_URL}/rooms/{room_id}/', headers=headers)
        else:
            print_error(f"Status: {response.status_code}, Response: {response.text}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    # Test 3: POST room cu is_active (ar trebui să fie ignorat sau să cauzeze eroare)
    print("  → POST /api/rooms/ (cu is_active - ar trebui ignorat)")
    try:
        room_data = {
            'code': 'TEST-002',
            'name': 'Sala de test 2',
            'capacity': 5,
            'is_active': True  # Acest câmp nu ar trebui să fie acceptat
        }
        response = requests.post(
            f'{BASE_URL}/rooms/',
            headers=headers,
            json=room_data
        )
        if response.status_code == 201:
            room = response.json()
            if 'is_active' not in room:
                print_success("Câmpul 'is_active' a fost ignorat corect")
            else:
                print_warning("Câmpul 'is_active' a fost acceptat (ar putea fi ignorat de serializer)")
            # Șterge camera de test
            room_id = room.get('id')
            if room_id:
                requests.delete(f'{BASE_URL}/rooms/{room_id}/', headers=headers)
        else:
            print_error(f"Status: {response.status_code}, Response: {response.text}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    return success

def test_request_endpoints():
    """Testează endpoint-urile pentru Request."""
    print_test("REQUEST ENDPOINTS")
    
    # Obține token pentru un user normal
    token = get_token('john.doe', 'test123')
    if not token:
        print_error("Nu s-a putut obține token pentru user")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    success = True
    
    # Găsește o cameră
    room = Room.objects.first()
    if not room:
        print_error("Nu există camere în sistem pentru testare")
        return False
    
    print(f"  → Folosim camera: {room.code} (ID: {room.id})")
    
    # Test 1: POST request fără date_start și date_end (ar trebui să eșueze)
    print("  → POST /api/requests/ (fără date_start și date_end - ar trebui să eșueze)")
    try:
        request_data = {
            'room': room.id,
            'note': 'Test request fără date'
        }
        response = requests.post(
            f'{BASE_URL}/requests/',
            headers=headers,
            json=request_data
        )
        if response.status_code == 400:
            print_success("Validare corectă: date_start și date_end sunt obligatorii")
        else:
            print_error(f"Ar trebui să fie 400, dar este {response.status_code}")
            print_error(f"Response: {response.text}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    # Test 2: POST request cu date_start și date_end valide
    print("  → POST /api/requests/ (cu date_start și date_end valide)")
    try:
        now = datetime.now()
        request_data = {
            'room': room.id,
            'date_start': (now + timedelta(days=1)).isoformat(),
            'date_end': (now + timedelta(days=1, hours=4)).isoformat(),
            'note': 'Test request valid'
        }
        response = requests.post(
            f'{BASE_URL}/requests/',
            headers=headers,
            json=request_data
        )
        if response.status_code == 201:
            request_obj = response.json()
            if 'date_start' in request_obj and 'date_end' in request_obj:
                print_success("Request creat cu succes cu date_start și date_end")
                print_success(f"  date_start: {request_obj.get('date_start')}")
                print_success(f"  date_end: {request_obj.get('date_end')}")
            else:
                print_error("date_start sau date_end lipsesc din răspuns!")
                success = False
        else:
            print_error(f"Status: {response.status_code}, Response: {response.text}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    # Test 3: POST request cu date_end < date_start (ar trebui să eșueze)
    print("  → POST /api/requests/ (cu date_end < date_start - ar trebui să eșueze)")
    try:
        now = datetime.now()
        request_data = {
            'room': room.id,
            'date_start': (now + timedelta(days=2)).isoformat(),
            'date_end': (now + timedelta(days=1)).isoformat(),  # date_end < date_start
            'note': 'Test request invalid'
        }
        response = requests.post(
            f'{BASE_URL}/requests/',
            headers=headers,
            json=request_data
        )
        if response.status_code == 400:
            print_success("Validare corectă: date_end trebuie să fie după date_start")
        else:
            print_error(f"Ar trebui să fie 400, dar este {response.status_code}")
            print_error(f"Response: {response.text}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    # Test 4: GET requests - verifică că date_start și date_end sunt în răspuns
    print("  → GET /api/requests/")
    try:
        response = requests.get(f'{BASE_URL}/requests/', headers=headers)
        if response.status_code == 200:
            requests_list = response.json()
            if requests_list:
                req = requests_list[0]
                if 'date_start' in req and 'date_end' in req:
                    print_success("date_start și date_end sunt prezente în răspuns")
                    print_success(f"  Request ID: {req.get('id')}")
                    print_success(f"  date_start: {req.get('date_start')}")
                    print_success(f"  date_end: {req.get('date_end')}")
                else:
                    print_error("date_start sau date_end lipsesc din răspuns!")
                    success = False
            else:
                print_warning("Nu există request-uri în sistem")
        else:
            print_error(f"Status: {response.status_code}")
            success = False
    except Exception as e:
        print_error(f"Eroare: {e}")
        success = False
    
    return success

def main():
    """Rulează toate testele."""
    print("\n" + "=" * 80)
    print("ÎNCEPE TESTAREA")
    print("=" * 80)
    print("\n[!] Asigură-te că serverul Django rulează: python manage.py runserver")
    print("[!] Asigură-te că există date de test: python manage.py seed_data")
    print("\n[!] Începem testarea în 2 secunde...")
    import time
    time.sleep(2)
    
    results = []
    
    try:
        results.append(("Room Endpoints", test_room_endpoints()))
        results.append(("Request Endpoints", test_request_endpoints()))
        
        print("\n" + "=" * 80)
        print("REZULTATE TESTARE")
        print("=" * 80)
        
        all_passed = all(result[1] for result in results])
        
        for test_name, passed in results:
            status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
            print(f"{status} {test_name}")
        
        if all_passed:
            print(f"\n{Colors.GREEN}✅ Toate testele au trecut!{Colors.END}")
        else:
            print(f"\n{Colors.RED}❌ Unele teste au eșuat!{Colors.END}")
        
    except requests.exceptions.ConnectionError:
        print_error("Nu s-a putut conecta la server. Asigură-te că rulează: python manage.py runserver")
    except Exception as e:
        print_error(f"Eroare neașteptată: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

