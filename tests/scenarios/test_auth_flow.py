import os
import datetime
import requests

from requests.exceptions import JSONDecodeError


url = 'http://127.0.0.1:5050'


# mock device log
def create_dummy_device_log(mac_address, ip_address):
    return {
        "mac_address": mac_address,
        "ip_address": ip_address,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "location": "Paris"
    }

# mock user
def create_dummy_user(score=100, email="test.user@gmail.com"):
    data = {
        "fname": "Test",
        "lname": "User",
        "email": email,
        "password": "123",
        "score": score
    }
    response = requests.post(f"{url}/register", json=data)
    return response, data["password"]

def login_user(email, password, mac, ip):
    device_log = create_dummy_device_log(mac, ip)
    login_response = requests.post(f"{url}/login", json={
        "email": email,
        "password": password,
        "device_log": device_log
    })
    return login_response

def test_register():
    resp, _ = create_dummy_user()
    
    assert resp.status_code == 201
    data = resp.json()
    assert data["message"] == "User registered successfully"
    assert data["fname"] == "Test"
    assert data["lname"] == "User"

def test_login(score, expected_flag, expected_warning, expected_status=200):
    email = f"test.user.{score}@gmail.com"
    resp, password = create_dummy_user(score=score, email=email)
    user_data = resp.json()

    login_resp = login_user(email, password, "AA:BB:CC:DD:EE:FF", "192.168.0.1")
    assert login_resp.status_code == expected_status

    try:
        login_data = login_resp.json()
    except JSONDecodeError:
        print("Response not JSON, status code:", login_resp.status_code)
        print("Response text:", login_resp.text)
        raise
    
    if expected_status == 200:
        assert login_data["score"] == user_data["score"]
        assert login_data["flag"] == expected_flag
        assert login_data["warning"] == expected_warning
def test_login_trusted():
    test_login(90, "Trusted", None)

def test_login_normal():
    test_login(80, "Normal", "You can make transactions up to €5,000 in 3 months")

def test_login_risky():
    test_login(60, "Risky", "You can make up to 3 transactions over €1,000 in 1 month")

def test_login_fraud_prone():
    test_login(40, "Fraud Prone", "You can make up to 10 transactions per month, each under €100")

def test_login_critical():
    email = f"test.user.20@gmail.com"
    resp, password = create_dummy_user(20, email=email)

    print("User created with score 20, email:", email)
    login_resp = login_user(email, password, "AA:BB:CC:DD:EE:FF", "192.168.0.1")
    print("Login response:", login_resp.text)
    assert login_resp.status_code == 200
    try:
        login_data = login_resp.json()
    except JSONDecodeError:
        print("Response not JSON, status code:", login_resp.status_code)
        print("Response text:", login_resp.text)
        raise

    assert login_data["error"] == "403: Account is locked. Identity verification required"

