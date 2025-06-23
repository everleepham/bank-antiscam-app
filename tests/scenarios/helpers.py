
import datetime
import requests
import pytest


url = "http://localhost:5050"


def register_user(email, fname, score=100, new_user=True):
    data = {
        "fname": fname,
        "lname": "Suspicious",
        "email": email,
        "password": "123456",
        "score": score,
        "new_user": new_user,
    }
    resp = requests.post(f"{url}/register", json=data)
    assert resp.status_code == 201
    return resp.json(), data["password"]


def login(email, password, mac, ip):
    device_log = {
        "mac_address": mac,
        "ip_address": ip,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "location": "Paris",
    }
    resp = requests.post(
        f"{url}/login",
        json={"email": email, "password": password, "device_log": device_log},
    )
    return resp


def create_transaction(
    sender_email,
    sender_fname,
    sender_lname,
    recipient_email,
    recipient_fname,
    recipient_lname,
    amount,
    timestamp,
    device_id="001",
):
    txn = {
        "sender": {
            "user_email": sender_email,
            "user_fname": sender_fname,
            "user_lname": sender_lname,
        },
        "sender_device_id": device_id,
        "recipient": {
            "user_email": recipient_email,
            "user_fname": recipient_fname,
            "user_lname": recipient_lname,
        },
        "amount": amount,
        "timestamp": timestamp or datetime.datetime.utcnow().isoformat(),
    }
    resp = requests.post(f"{url}/transactions", json=txn)
    return resp


