import datetime
import pytest
from helpers import register_user, create_transaction

BASE_EMAIL = "policytest+{}@test.com"
RECIPIENT = {
    "email": "recipient@test.com",
    "fname": "Recep",
    "lname": "Target"
}

@pytest.fixture(scope="module", autouse=True)
def setup_recipient():
    register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)


def iso_now(offset_days=0):
    return (datetime.datetime.utcnow() + datetime.timedelta(days=offset_days)).isoformat()


# trusted user with high score, no limitations
def test_trusted_user_allowed():
    user, _ = register_user(BASE_EMAIL.format("trusted"), "Trusted", score=95)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)

    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Trusted",
        sender_lname="User",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=99999,
        timestamp=iso_now()
    )
    assert res.status_code == 200
    
    
def test_normal_user_exceed_total_limit():
    user, _ = register_user(BASE_EMAIL.format("normal"), "Normal", score=80)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)

    # Gửi 2 transaction trước để tạo tổng = 4800€
    for amount in [2000, 2800]:
        res = create_transaction(
            sender_email=user["email"],
            sender_fname="Normal",
            sender_lname="User",
            recipient_email=RECIPIENT["email"],
            recipient_fname=RECIPIENT["fname"],
            recipient_lname=RECIPIENT["lname"],
            amount=amount,
            timestamp=iso_now(-10),
        )
        assert res.status_code == 200

    # Gửi thêm để vượt 5000€
    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Normal",
        sender_lname="User",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=500,
        timestamp=iso_now(),
    )
    
    # expected result: blocked
    assert res.status_code == 403
    assert "Limit exceeded" in res.text


def test_risky_user_high_txn_limit():
    user, _ = register_user(BASE_EMAIL.format("risky"), "Risky", score=60)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)

    # make 3 transactions > 1000€
    for amt in [1200, 1500, 1300]:
        res = create_transaction(
            sender_email=user["email"],
            sender_fname="Risky",
            sender_lname="User",
            recipient_email=RECIPIENT["email"],
            recipient_fname=RECIPIENT["fname"],
            recipient_lname=RECIPIENT["lname"],
            amount=amt,
            timestamp=iso_now(-2),
        )
        assert res.status_code == 200

    # sending a 4th transaction > 1000€ 
    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Risky",
        sender_lname="User",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=1100,
        timestamp=iso_now(),
    )
    
    # expected result: blocked
    assert res.status_code == 403
    assert "Max 3 transactions" in res.text


def test_fraud_prone_user_exceed_transaction_count():
    user, _ = register_user(BASE_EMAIL.format("fraud_count"), "Fraud", score=40)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)

    for _ in range(10):
        res = create_transaction(
            sender_email=user["email"],
            sender_fname="Fraud",
            sender_lname="Count",
            recipient_email=RECIPIENT["email"],
            recipient_fname=RECIPIENT["fname"],
            recipient_lname=RECIPIENT["lname"],
            amount=50,
            timestamp=iso_now(-1),
        )
        assert res.status_code == 200

    # 10th transactions
    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Fraud",
        sender_lname="Count",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=50,
        timestamp=iso_now(),
    )
    assert res.status_code == 403
    error_json = res.json()
    assert "Max 10 transactions per month" in error_json["error"]


def test_fraud_prone_user_transaction_too_large():
    user, _ = register_user(BASE_EMAIL.format("fraud_amt"), "Fraud", score=35)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)


    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Fraud",
        sender_lname="TooLarge",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=200,
        timestamp=iso_now(),
    )
    
    # expected result: blocked
    assert res.status_code == 403
    error_json = res.json()
    assert "Max €100 per transaction" in error_json["error"]


def test_critical_user_blocked():
    user, _ = register_user(BASE_EMAIL.format("critical"), "Critical", score=10)
    recipient, _ = register_user(RECIPIENT["email"], RECIPIENT["fname"], score=100)

    res = create_transaction(
        sender_email=user["email"],
        sender_fname="Critical",
        sender_lname="Blocked",
        recipient_email=RECIPIENT["email"],
        recipient_fname=RECIPIENT["fname"],
        recipient_lname=RECIPIENT["lname"],
        amount=10,
        timestamp=iso_now(),
    )
    assert res.status_code == 403
    assert "Account is locked" in res.text
