from fastapi import HTTPException
from flask import Blueprint, request
from app.services.redis_service import RedisTrustScoreService
from app.services.neo4j_service import Neo4jService
from app.models.mongo_model import MongoTransactionModel, Transaction, get_next_id, MongoUserModel
from app.services.neo4j_service import Neo4jService
from app.models.neo4j_model import Neo4jTransactionModel, TransactionSchema
from app.services.mongo_service import MongoService
from app.services.trust_service import enforce_trust_policy
from app.services.score_service import calculate_score, update_score_mongo
from pydantic import ValidationError


redis = RedisTrustScoreService()
txn_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

mongo_txn_model = MongoTransactionModel()
mongo_user_model = MongoUserModel()
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
    txn.transaction_id = transaction_id 

    # create txn node in Neo4j
    txn_node = TransactionSchema(
        transaction_id=transaction_id,
        amount=txn.amount,
        status=txn.status,
        timestamp=txn.timestamp.isoformat()
    )
    neo4j_txn_model.create(txn_node)
    print(f"Created transaction node in Neo4j: {txn_node}")

    # get user_id to create relationship in Neo4j
    sender_user = mongo_user_model.read_by_email(txn.sender.user_email)
    recipient_user = mongo_user_model.read_by_email(txn.recipient.user_email)

    if not sender_user or not recipient_user:
        return {"error": "Sender or recipient not found"}, 404
    
    txn.sender.user_id = sender_user["user_id"]
    txn.recipient.user_id = recipient_user["user_id"]

    mongo_txn_model.create(txn)
    print(f"Saved transaction in MongoDB: {txn}")

    print(f'Sender Id: {sender_user["user_id"]}, Recipient Id: {recipient_user["user_id"]}')
    
    connection_data = {
        "sender_id": sender_user["user_id"],
        "receiver_id": recipient_user["user_id"],
        "transaction_id": transaction_id,
    }
    neo4j_service.connect_user_transaction_user(connection_data)
    print(f"Created relationship in Neo4j: {connection_data}")

    # calculate trust score
    new_score, _ = calculate_score(sender_user["user_id"], str(transaction_id))
    if new_score:
        update_score_mongo(sender_user["user_id"])
    
    txn_updated = mongo_txn_model.read(str(transaction_id))
    status = txn_updated["status"]
    flag_reason = txn_updated["flag_reason"]
    
    # is txn is not marked suspicious, verify it
    if status != "suspicious":
        MongoService().verify_transaction(str(transaction_id))
        txn_verified = mongo_txn_model.read(str(transaction_id))
        status = txn_verified.get("status")
        print(f"Transaction {transaction_id} verified because status is {status}")


    return {
        "transaction_id": transaction_id,
        "sender": txn.sender.user_email,
        "recipient": txn.recipient.user_email,
        "amount": txn.amount,
        "status": status,
        "flag_reason": flag_reason,
    }


@txn_bp.route('/<user_id>', methods=['GET'])
def get_user_transactions(user_id: str):
    transactions = MongoService().get_transactions_by_sender(user_id)
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for this user")
    
    return {"transactions": transactions}
