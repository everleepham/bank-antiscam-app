import datetime
import requests
from helpers import register_user, login, create_transaction, url, random_email


def test_high_transaction_amount():
    email_sender = "sender.highamount@gmail.com"
    email_recipient = "email_recipienthigh.amount@gmail.com"
    sender, password = register_user(email_sender, "Sender", score=100)
    recipient, _ = register_user(email_recipient, "Recipient", score=100)

    login(email_sender, password, "AA:AA:AA:AA:AA:01", "192.168.0.10")

    # transaction > 2.5 plafond
    resp = create_transaction(
        sender["email"],
        sender["fname"],
        sender["lname"],
        recipient["email"],
        recipient["fname"],
        recipient["lname"],
        amount=5000,
        timestamp=datetime.datetime.utcnow().isoformat(),
    )

    login_res = login(email_sender, password, "AA:AA:AA:AA:AA:01", "192.168.0.10")
    score = login_res.json()["score"]

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "suspicious"
    assert "exceeds user plafond" in data["flag_reason"]
    # new account and high transaction amount
    # 100 - 5 - 20 = 75
    assert score == 75  # new account and high transaction amount


def test_suspicious_monthly_spent():
    email_sender = "monthly.suspicious.sender@gmail.com"
    email_recipient = "monthly.suspicious.recipient@gmail.com"

    sender, password = register_user(email_sender, "Sender", new_user=False)
    recipient, _ = register_user(email_recipient, "Recipient", new_user=False)

    login(email_sender, password, "BB:BB:BB:BB:BB:01", "192.168.0.11")

    # create transaction 2 months ago
    two_months_ago_date = (
        (datetime.datetime.utcnow() - datetime.timedelta(days=60))
        .replace(day=15)
        .isoformat()
    )
    resp1 = create_transaction(
        sender["email"],
        sender["fname"],
        sender["lname"],
        recipient["email"],
        recipient["fname"],
        recipient["lname"],
        amount=100,
        timestamp=two_months_ago_date,
    )
    if resp1.status_code == 500:
        print(f"Error 500 on first transaction creation: {resp1.text}")
    assert resp1.status_code == 200

    resp2 = create_transaction(
        sender["email"],
        sender["fname"],
        sender["lname"],
        recipient["email"],
        recipient["fname"],
        recipient["lname"],
        amount=150,
        timestamp=two_months_ago_date,
    )
    if resp2.status_code == 500:
        print(f"Error 500 on second transaction creation: {resp2.text}")
    assert resp2.status_code == 200

    # create transaction 1 months ago
    one_month_ago_date = (
        (datetime.datetime.utcnow() - datetime.timedelta(days=30))
        .replace(day=15)
        .isoformat()
    )
    resp3 = create_transaction(
        sender["email"],
        sender["fname"],
        sender["lname"],
        recipient["email"],
        recipient["fname"],
        recipient["lname"],
        amount=200,
        timestamp=one_month_ago_date,
    )
    if resp3.status_code == 500:
        print(f"Error 500 on third transaction creation: {resp3.text}")
    assert resp3.status_code == 200

    # sum of avg 2 months = (250 + 200)/2 = 225

    # sum of transactions this month is 500 > 2 * 225 => flagged suspicious
    current_month_date = datetime.datetime.utcnow().replace(day=15).isoformat()
    resp4 = create_transaction(
        sender["email"],
        sender["fname"],
        sender["lname"],
        recipient["email"],
        recipient["fname"],
        recipient["lname"],
        amount=500,
        timestamp=current_month_date,
    )
    if resp4.status_code == 500:
        print(f"Error 500 on fourth transaction creation: {resp4.text}")
    assert resp4.status_code == 200

    # get new score
    login_res = login(email_sender, password, "BB:BB:BB:BB:BB:01", "192.168.0.11")
    score = login_res.json().get("score")

    trust_resp = requests.post(f"{url}/score/calculate", json={"email": email_sender})
    if trust_resp.status_code == 500:
        print(f"Error 500 on score calculate: {trust_resp.text}")
    assert trust_resp.status_code == 200
    trust_data = trust_resp.json()
    assert trust_data["score_calculated"] == 80
    assert trust_data["reasons"] == ["high_monthly_spent"]


def test_multiple_devices_login():
    email = "many.devices@gmail.com"
    user, password = register_user(email, "Devices", score=100, new_user=False)

    for i in range(6):
        mac = f"CC:CC:CC:CC:CC:{i:02X}"
        ip = f"10.0.0.{i}"
        login(email, password, mac, ip)

    resp = requests.post(f"{url}/score/calculate", json={"email": email})
    assert resp.status_code == 200
    data = resp.json()
    assert data["score_calculated"] == 80
    assert data["reasons"] == ["has_multiple_devices"]


def test_shared_device_detection():
    # User A
    email_a = "shared.device.a@gmail.com"
    user_a, pwd_a = register_user(email_a, "Shared_a", score=100, new_user=False)

    # User B → E
    for i in range(5):
        email_other = f"shared.device.{i}@gmail.com"
        register_user(email_other, "Shared_o", score=100)
        login(email_other, "123456", "DD:DD:DD:DD:DD:00", "192.168.1.1")

    # user A log in with them shared device
    login(email_a, pwd_a, "DD:DD:DD:DD:DD:00", "192.168.1.1")

    resp = requests.post(f"{url}/score/calculate", json={"email": email_a})
    assert resp.status_code == 200
    data = resp.json()
    assert data["reasons"] == ['shared_device_count']
    assert data["score_calculated"] == 80
    
def test_has_suspicious_connection():
    email = "connection.suspicious@gmail.com"
    user, password = register_user(email, "User", score=100, new_user=False)
    
    # create 4 suspicious users
    suspicious_users = []
    for i in range(4):
        sus_email = f"sus.user{i}@gmail.com"
        sus_user, _ = register_user(sus_email, "Sus", score=30, new_user=False)
        suspicious_users.append(sus_user)
    
    login(email, password, "AA:AA:AA:AA:AA:01", "192.168.0.10")
    
    # make a transaction to 4 suspicious users
    for sus_user in suspicious_users:
        create_transaction(
            user["email"],
            user["fname"],
            user["lname"],
            sus_user["email"],
            sus_user["fname"],
            sus_user["lname"],
            amount=200,
            timestamp=datetime.datetime.utcnow().isoformat(),
        )
    
    resp = requests.post(f"{url}/score/calculate", json={"email": email})
    assert resp.status_code == 200
    data = resp.json()
    assert "suspicious_connections" in data["reasons"]
    assert data["score_calculated"] == 80
    

def test_circular_transactions_detection():
    # create 4 users
    user1, _ = register_user(random_email(), "User1", score=100, new_user=False)
    user2, _ = register_user(random_email(), "User2", score=100, new_user=False)
    user3, _ = register_user(random_email(), "User3", score=100, new_user=False)
    user4, _ = register_user(random_email(), "User4", score=100, new_user=False)

    # create transactions that form a circular flow
    # user1 -> user2 -> user3 -> user4 -> user1
    now = datetime.datetime.utcnow().isoformat()
    create_transaction(
        user1["email"], user1["fname"], user1["lname"],
        user2["email"], user2["fname"], user2["lname"],
        amount=100,
        timestamp=now
    )
    create_transaction(
        user2["email"], user2["fname"], user2["lname"],
        user3["email"], user3["fname"], user3["lname"],
        amount=150,
        timestamp=now
    )
    create_transaction(
        user3["email"], user3["fname"], user3["lname"],
        user4["email"], user4["fname"], user4["lname"],
        amount=200,
        timestamp=now
    )
    create_transaction(
        user4["email"], user4["fname"], user4["lname"],
        user1["email"], user1["fname"], user1["lname"],
        amount=50,
        timestamp=now
    )

    resp = requests.post(f"{url}/score/calculate", json={"email": user1["email"]})

    # check response
    assert resp.status_code == 200
    data = resp.json()
    assert "circular_transaction_detected" in data["reasons"]
    assert data["score_calculated"] == 70



