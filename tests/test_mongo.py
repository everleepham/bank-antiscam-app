from app.models.mongo_model import User, DeviceLog, Transaction, UserInfo


def create_dummy_user(mongo_service, email="a@example.com"):
    return mongo_service.create_user(
        User(
            fname="Test",
            lname="User",
            email=email,
            password="pass",
            new_user=False,
            score=100,
            plafond=1000.0,
        )
    )
    
def test_connection(mongo_service):
    assert mongo_service is not None
    assert mongo_service.user_model is not None
    assert mongo_service.transaction_model is not None
    assert mongo_service.device_log_model is not None
    user = create_dummy_user(mongo_service)
    fetched = mongo_service.user_model.read(user.user_id)
    assert fetched is not None
    assert fetched['email'] == "a@example.com"


def test_get_score_and_update_score(mongo_service):
    user = create_dummy_user(mongo_service)
    assert mongo_service.get_score(user.user_id) == 100

    mongo_service.update_score(user.user_id, score=150)
    assert mongo_service.get_score(user.user_id) == 150


def test_get_users_by_device(mongo_service):
    user1 = create_dummy_user(mongo_service, email="u1@example.com")
    user2 = create_dummy_user(mongo_service, email="u2@example.com")

    mongo_service.log_device(
        DeviceLog(
            user_id=user1.user_id,
            mac_address="11:22:33:44:55:66",
            ip_address="1.1.1.1",
            location="Paris",
        )
    )
    mongo_service.log_device(
        DeviceLog(
            user_id=user2.user_id,
            mac_address="11:22:33:44:55:66",
            ip_address="1.1.1.2",
            location="Paris",
        )
    )

    result = mongo_service.get_users_by_device("112233445566")
    assert set(result) == {user1.user_id, user2.user_id}


def test_get_transactions_by_sender_and_recipient(mongo_service):
    sender = create_dummy_user(mongo_service, email="sender@example.com")
    recipient = create_dummy_user(mongo_service, email="recipient@example.com")

    txn1 = Transaction(
        sender=UserInfo(
            user_id=sender.user_id, user_fname=sender.fname, user_lname=sender.lname
        ),
        recipient=UserInfo(
            user_id=recipient.user_id,
            user_fname=recipient.fname,
            user_lname=recipient.lname,
        ),
        sender_device_id="abc123",
        amount=500.0,
    )
    mongo_service.create_transaction(txn1)

    txn2 = Transaction(
        sender=UserInfo(
            user_id=recipient.user_id,
            user_fname=recipient.fname,
            user_lname=recipient.lname,
        ),
        recipient=UserInfo(
            user_id=sender.user_id, user_fname=sender.fname, user_lname=sender.lname
        ),
        sender_device_id="xyz456",
        amount=300.0,
    )
    mongo_service.create_transaction(txn2)

    sent_by_sender = mongo_service.get_transactions_by_sender(sender.user_id)
    assert len(sent_by_sender) == 1
    assert sent_by_sender[0]["amount"] == 500.0

    received_by_sender = mongo_service.get_transactions_by_recipient(sender.user_id)
    assert len(received_by_sender) == 1
    assert received_by_sender[0]["amount"] == 300.0


def test_get_devices_by_user(mongo_service):
    user = create_dummy_user(mongo_service)

    mongo_service.log_device(
        DeviceLog(
            user_id=user.user_id,
            mac_address="aa:bb:cc:dd:ee:ff",
            ip_address="8.8.8.8",
            location="Lille",
        )
    )
    mongo_service.log_device(
        DeviceLog(
            user_id=user.user_id,
            mac_address="11:22:33:44:55:66",
            ip_address="8.8.4.4",
            location="Nantes",
        )
    )

    device_ids = mongo_service.get_devices_by_user(user.user_id)
    assert set(device_ids) == {"AABBCCDDEEFF", "112233445566"}
