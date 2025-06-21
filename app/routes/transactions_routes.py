from fastapi import HTTPException
from flask import Blueprint, request
from app.services.redis_service import RedisTrustScoreService
from app.services.neo4j_service import Neo4jService
from app.models.mongo_model import MongoTransactionModel, Transaction, get_next_id
from app.services.neo4j_service import Neo4jService
from app.models.neo4j_model import Neo4jTransactionModel, TransactionSchema
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy
from app.services.score_service import calculate_score, update_score_mongo
from pydantic import ValidationError


redis = RedisTrustScoreService()
txn_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

mongo_txn_model = MongoTransactionModel()
neo4j_txn_model = Neo4jTransactionModel()
neo4j_service = Neo4jService()


@txn_bp.route("/", methods=["POST"])
def make_transaction():
    tx_data = request.json
    print(f"Received transaction data: {tx_data}")

    try:
        txn = Transaction(**tx_data)
    except ValidationError as e:
        return {"error": "Invalid transaction format", "details": e.errors()}, 400
    
    transaction_id = get_next_id("transaction_id")

    # create txn node in neo4j
    txn_node = TransactionSchema(
        transaction_id=transaction_id,
        amount=txn.amount,
        status=txn.status,
        timestamp=txn.timestamp.isoformat()
    )
    neo4j_txn_model.create(txn_node)
    
    print(f"Created transaction node in Neo4j: {txn_node}")

    # save in mongo
    mongo_txn_model.create(txn)
    print(f"Saved transaction in MongoDB: {txn}")

    # create relationship in neo4j
    connection_data = {
        "sender_id": txn.sender.user_id,
        "receiver_id": txn.recipient.user_id,
        "transaction_id": txn.transaction_id,
    }
    neo4j_service.connect_user_transaction_user(connection_data)
    print(f"Created relationship in Neo4j: {connection_data}")

    # calculate new score after every transaction
    new_score = calculate_score(txn.sender.user_id, txn.transaction_id, txn.sender_device_id)
    if new_score:
        update_score_mongo(txn.sender.user_id)
    print(f"Score updated: {new_score}")

    return {
        "message": "Transaction created successfully",
        "transaction_id": txn.transaction_id,
        "sender": txn.sender.user_id,
        "recipient": txn.recipient.user_id,
        "amount": txn.amount,
    }

@txn_bp.route('/<user_id>', methods=['GET'])
def get_user_transactions(user_id: str):
    transactions = MongoService().get_transactions_by_sender(user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    
    return {"transactions": transactions}
