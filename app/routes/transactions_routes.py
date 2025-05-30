from fastapi import APIRouter, HTTPException
from app.services.redis_service import RedisService
from app.services.neo4j_service import Neo4jService
from app.models.mongo_model import MongoTransactionModel
from app.services.neo4j_service import Neo4jService
from app.models.neo4j_model import Neo4jTransactionModel
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy

router = APIRouter()
redis = RedisService()


@router.post("/transactions")
def make_transaction(tx_data: dict):
    enforce_trust_policy(tx_data.sender_id, tx_data.amount, MongoTransactionModel())
    node_transaction_data = {
        "transaction_id": tx_data.transaction_id,
        "amount": tx_data.amount,
        "timestamp": tx_data.timestamp,
        "status": tx_data.status
    }
    connection_data = {
        "sender_id": tx_data.sender.user_id,
        "receiver_id": tx_data.receiver.user_id,
        "transaction_id": tx_data.transaction_id
    }
    Neo4jTransactionModel().create(node_transaction_data)
    MongoTransactionModel().create(tx_data)
    Neo4jService().connect_user_transaction_user(connection_data)
    return {"message": "Transaction created successfully"}


@router.get("/transactions/{user_id}")
def get_user_transactions(user_id: str):
    transactions = MongoService().get_transactions_by_sender(user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    
    return transactions
