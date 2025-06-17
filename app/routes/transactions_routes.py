from fastapi import HTTPException
from flask import Blueprint
from app.services.redis_service import RedisTrustScoreService
from app.services.neo4j_service import Neo4jService
from app.models.mongo_model import MongoTransactionModel
from app.services.neo4j_service import Neo4jService
from app.models.neo4j_model import Neo4jTransactionModel
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy
from app.services.score_service import calculate_score, update_score_mongo

redis = RedisTrustScoreService()
bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.route('/', methods=['POST'])
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
    new_score = calculate_score(tx_data.sender.user_id, tx_data.transaction_id, tx_data.device_id)
    if new_score:
        update_score_mongo(tx_data.sender.user_id)
    return {"message": "Transaction created successfully"}


@bp.route('/{user_id}', methods=['POST'])
def get_user_transactions(user_id: str):
    transactions = MongoService().get_transactions_by_sender(user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    
    return transactions
