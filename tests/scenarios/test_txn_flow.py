import pytest
from datetime import datetime
from app.services.score_service import update_score_mongo

alice = {
    "user_id": "001",
    "user_fname": "Alice",
    "user_lname": "Wonder"
}

bob = {
    "user_id": "002",
    "user_fname": "Bob",
    "user_lname": "Builder"
}

device_id = "003"


def set_user_score(user_id, score):
    update_score_mongo(user_id, score)

class TestTransactionLimits:

    def login_user(self, client, score):
        set_user_score(alice["user_id"], score)
        login_data = {
            "email": "alice@example.com",
            "password": "password123",
            "device_log": {
                "device_id": device_id,
                "ip": "127.0.0.1",
                "timestamp": datetime.now().isoformat()
            }
        }
        return client.post("/login", json=login_data)

    def create_transaction(self, client, amount, txn_id="001"):
        txn_data = {
            "transaction_id": txn_id.zfill(3),
            "sender": alice,
            "recipient": bob,
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
            "sender_device_id": device_id
        }
        return client.post("/transactions/", json=txn_data)

    def test_trusted_user_no_limit(self, client):
        # You are Alice with score 95 (Trusted user)
        login_resp = self.login_user(client, 95)
        assert login_resp.status_code == 200
        assert login_resp.json.get("trust_score", 0) >= 90

        # Big transaction > 5000€ allowed
        txn_resp = self.create_transaction(client, 10000, txn_id="010")
        assert txn_resp.status_code == 200
        assert txn_resp.json["message"] == "Transaction created successfully"

    def test_normal_user_limit_5000_in_3_months(self, client):
        # You are Alice with score 80 (Normal user)
        login_resp = self.login_user(client, 80)
        assert login_resp.status_code == 200

        # 3 transactions total 4900€ allowed
        for i, amount in enumerate([2000, 1500, 1400], start=1):
            resp = self.create_transaction(client, amount, txn_id=str(i))
            assert resp.status_code == 200

        # 4th transaction exceeding 5000€ total blocked
        resp = self.create_transaction(client, 200, txn_id="004")
        assert resp.status_code in (400, 403)

    def test_risky_user_limit_3_big_tx_in_1_month(self, client):
        # Alice with score 60 (Risky user)
        login_resp = self.login_user(client, 60)
        assert login_resp.status_code == 200

        # 3 transactions > 1000€ allowed
        for i in range(1, 4):
            resp = self.create_transaction(client, 1200, txn_id=str(i))
            assert resp.status_code == 200

        # 4th big transaction > 1000€ blocked
        resp = self.create_transaction(client, 1500, txn_id="004")
        assert resp.status_code in (400, 403)

        # Smaller transaction <= 1000€ allowed
        resp = self.create_transaction(client, 900, txn_id="005")
        assert resp.status_code == 200

    def test_fraud_prone_user_limit_10_tx_max_100_each(self, client):
        # Alice with score 40 (Fraud-prone)
        login_resp = self.login_user(client, 40)
        assert login_resp.status_code == 200

        # 10 transactions < 100€ allowed
        for i in range(1, 11):
            resp = self.create_transaction(client, 90, txn_id=str(i))
            assert resp.status_code == 200

        # 11th transaction < 100€ blocked
        resp = self.create_transaction(client, 90, txn_id="011")
        assert resp.status_code in (400, 403)

        # Transaction > 100€ blocked immediately
        resp = self.create_transaction(client, 150, txn_id="012")
        assert resp.status_code in (400, 403)

    def test_critical_user_blocked(self, client):
        # Alice with score 20 (Critical user)
        login_resp = self.login_user(client, 20)
        # Login blocked
        assert login_resp.status_code in (401, 403)

        # Any transaction blocked
        resp = self.create_transaction(client, 50, txn_id="001")
        assert resp.status_code in (401, 403)
