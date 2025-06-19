import pytest
from datetime import datetime, timedelta

from app.models.neo4j_model import (
    Neo4jUserModel,
    Neo4jTransactionModel,
    Neo4jDeviceModel,
    UserSchema,
    TransactionSchema,
    DeviceSchema,
)
from app.services.neo4j_service import Neo4jService
from app.models.mongo_model import TransactionStatus


@pytest.fixture
def user_model():
    return Neo4jUserModel()

@pytest.fixture
def txn_model():
    return Neo4jTransactionModel()

@pytest.fixture
def device_model():
    return Neo4jDeviceModel()

@pytest.fixture
def test_user():
    return UserSchema(
        user_id="001",
        fname="Test",
        lname="User",
        score=100
    )

@pytest.fixture
def test_receiver():
    return UserSchema(
        user_id=f"002",
        fname="Receiver",
        lname="User",
        score=50
    )

@pytest.fixture
def test_transaction():
    return TransactionSchema(
        transaction_id=f"001",
        amount=500.0,
        status=TransactionStatus.PENDING,
        timestamp=datetime.utcnow().isoformat()
    )

@pytest.fixture
def test_device():
    return DeviceSchema(
        device_id=f"aabbddeeff",
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.100"
    )
    
    
def cleanup_user_device(user_model, device_model, user_id, device_id):
    user_model.delete(user_id)
    device_model.delete(device_id)

    
def test_connection(user_model, txn_model, device_model, neo4j_service, test_user):
    assert user_model is not None
    assert txn_model is not None
    assert device_model is not None
    assert neo4j_service is not None

    # Test connection by creating a dummy user
    node_id = user_model.create(test_user)
    assert isinstance(node_id, int)

    
def test_user_crud(user_model, test_user):
    # Create
    node_id = user_model.create(test_user)
    assert isinstance(node_id, int)

    # Read
    node = user_model.read(test_user.user_id)
    assert node["user_id"] == test_user.user_id

    # Update
    updated = user_model.update(test_user.user_id, test_user.copy(update={"score": 200}))
    assert updated is True

    # Delete
    deleted = user_model.delete(test_user.user_id)
    assert deleted is True
    
    user_model.delete(test_user.user_id)


def test_transaction_crud(txn_model, test_transaction):
    # Create
    node_id = txn_model.create(test_transaction)
    assert isinstance(node_id, int)

    # Read
    node = txn_model.read(test_transaction.transaction_id)
    assert node["transaction_id"] == test_transaction.transaction_id

    # Update
    updated = txn_model.update(test_transaction.transaction_id, test_transaction.copy(update={"amount": 999}))
    assert updated is True

    # Delete
    deleted = txn_model.delete(test_transaction.transaction_id)
    assert deleted is True
    
    # in case conftest doesn't clean up
    txn_model.delete(test_transaction.transaction_id)

def test_device_crud(device_model, test_device):
    # Create
    node_id = device_model.create(test_device)
    assert isinstance(node_id, int)

    # Read
    node = device_model.read(test_device.device_id)
    assert node["device_id"] == test_device.device_id

    # Update
    updated = device_model.update(test_device.device_id, test_device.copy(update={"ip_address": "10.0.0.2"}))
    assert updated is True

    # Delete
    deleted = device_model.delete(test_device.device_id)
    assert deleted is True

def test_user_transaction_connection(neo4j_service, user_model, txn_model, test_user, test_receiver, test_transaction):
    user_model.create(test_user)
    user_model.create(test_receiver)
    txn_model.create(test_transaction)

    result = neo4j_service.connect_user_transaction_user({
        "sender_id": test_user.user_id,
        "receiver_id": test_receiver.user_id,
        "transaction_id": test_transaction.transaction_id
    })
    assert result is not None

    connections = neo4j_service.get_user_transactions_connections({"user_id": test_user.user_id})
    assert any(tx["transaction_id"] == test_transaction.transaction_id for tx in connections)
    
def test_user_user_connection(neo4j_service, txn_model, user_model, test_user, test_receiver, test_transaction):
    user_model.create(test_user)
    user_model.create(test_receiver)
    txn_model.create(test_transaction)

    result = neo4j_service.connect_user_transaction_user({
        "sender_id": test_user.user_id,
        "receiver_id": test_receiver.user_id,
        "transaction_id": test_transaction.transaction_id
    })
    
    assert result is not None
    
    connections = neo4j_service.get_user_user_connections({"user_id": test_user.user_id})
    assert any(conn["receiver_id"] == test_receiver.user_id for conn in connections)


def test_user_device_connection(neo4j_service, device_model, user_model, test_user, test_device):
    user_model.create(test_user)
    device_model.create(test_device)

    result = neo4j_service.connect_user_device({
        "user_id": test_user.user_id,
        "device_id": test_device.device_id
    })
    assert result is not None

    result = neo4j_service.get_user_device_connections({"user_id": test_user.user_id})
    assert result[0]["total_devices"] == 1


def test_detect_circular_transaction(neo4j_service, user_model, txn_model):
    user = UserSchema(user_id="001", fname="Circular", lname="Test", score=10)
    user_model.create(user)

    now = datetime.utcnow()
    txns = []
    prev_user = user

    # ceate circular transaction: 001 -> 002 -> 003 -> 001
    for i in range(2, 5):  # 002, 003, 004
        user_id = f"{i:03d}" 
        next_user = UserSchema(user_id=user_id, fname="U", lname=str(i), score=5)
        user_model.create(next_user)

        txn = TransactionSchema(
            transaction_id=f"{i:03d}", 
            amount=100,
            timestamp=(now + timedelta(minutes=i)).isoformat()
        )
        txn_model.create(txn)

        neo4j_service.connect_user_transaction_user({
            "sender_id": prev_user.user_id,
            "receiver_id": next_user.user_id,
            "transaction_id": txn.transaction_id
        })

        prev_user = next_user
        txns.append(txn)

    # last connection in the circular 004 -> 001
    txn = TransactionSchema(
        transaction_id="005",
        amount=100,
        timestamp=(now + timedelta(minutes=5)).isoformat()
    )
    txn_model.create(txn)
    neo4j_service.connect_user_transaction_user({
        "sender_id": prev_user.user_id,
        "receiver_id": user.user_id,
        "transaction_id": txn.transaction_id
    })

    path = neo4j_service.detect_circular_transaction({
        "user_id": user.user_id,
        "max_depth": 4,
        "max_diff_minutes": 10
    })

    assert path is not None
    
    path_nodes = path.nodes
    path_ids = []
    for node in path_nodes:
        if "transaction_id" in node:
            path_ids.append(node["transaction_id"])
        else:
            path_ids.append(node["user_id"])
    assert "001" in path_ids
    assert "002" in path_ids
    assert "003" in path_ids
    assert "004" in path_ids
    assert "005" in path_ids
    
    assert path_nodes[0]["user_id"] == "001"
    assert path_nodes[-1]["user_id"] == "001"