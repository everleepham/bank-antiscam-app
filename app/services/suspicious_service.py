from app.models.mongo_model import MongoUserModel, MongoTransactionModel, DeviceLogModel, User, Transaction, DeviceLog, TransactionStatus
from datetime import datetime
from app.utils.trust_rules import RULES

from .neo4j_service import Neo4jService
from .mongo_service import MongoService
import logging


logging.basicConfig(level=logging.DEBUG)  
logger = logging.getLogger(__name__)

# Mongo service
def check_high_transactions_amount(user_id, transaction_id):
    user_id = str(user_id).zfill(3)
    txn_model = MongoTransactionModel()
    user_model = MongoUserModel()

    transaction = txn_model.read(transaction_id)
    if not transaction:
        return False

    sender_info = transaction.get("sender", {})
    sender_id = sender_info.get("user_id")
    if sender_id != user_id:
        return False

    user = user_model.read(user_id)
    if not user:
        return False

    plafond = user.get("plafond", 1000.0)
    amount = transaction.get("amount", 0)

    if amount > (plafond * 2):
        txn_model.collection.update_one(
            {"transaction_id": transaction_id},
            {"$set": {
                "status": TransactionStatus.SUSPICIOUS,
                "flag_reason": f"Amount {amount} exceeds user plafond {plafond}"
            }}
        )
        return True
    logger.debug("Transaction found: %s", transaction)
    logger.debug("Sender ID in txn: %s", sender_id)
    logger.debug("User ID passed: %s", user_id)
    logger.debug("Amount: %s | Plafond: %s", amount, plafond)
    logger.debug("Comparison result: %s", amount > (plafond * 2))

    return False


def check_suspicious_monthly_spent(user_id):
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    pipeline = [
        {
            "$match": {
                "sender.user_id": user_id,
                "status": TransactionStatus.VERIFIED.value  
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"}
                },
                "total_spent": {"$sum": "$amount"}
            }
        }
    ]

    cursor = MongoTransactionModel().collection.aggregate(pipeline)

    monthly_spending = {}
    for doc in cursor:
        # separate year and month
        y = doc["_id"]["year"]
        m = doc["_id"]["month"]
        total = doc["total_spent"]
        monthly_spending[(y, m)] = total

    current_spent = monthly_spending.get((current_year, current_month), 0)
    
    past_months = [
        amount for (y, m), amount in monthly_spending.items()
        if (y, m) != (current_year, current_month)
    ]

    if not past_months:
        return False 

    average_past = sum(past_months) / len(past_months)
    
    return current_spent > 2 * average_past
    

def is_new_account(user_id):
    txn_model = MongoTransactionModel()
    user_model = MongoUserModel()
    
    user = user_model.read(user_id)
    if not user:
        return False 

    if not user.get("new_user", True):
        return False

    txn_count = txn_model.collection.count_documents({"sender.user_id": user_id})

    if txn_count >= 3: # has 3+ transactions-> new_user = False
        user_model.collection.update_one(
            {"user_id": user_id},
            {"$set": {"new_user": False}}
        )
        return False
    
    return True

def has_multiple_devices(user_id): # 1 user uses >5 devices
    user_devices = MongoService().get_devices_by_user(user_id)
    return len(user_devices) > 5

def has_shared_device_count(user_id: str) -> bool:
    user_devices = MongoService().get_devices_by_user(user_id)  # giả sử hàm này trả về list device_id

    for device_id in user_devices:
        device_users = MongoService().get_users_by_device(device_id)
        if len(device_users) > 5 and user_id in device_users:
            return True
    return False

# Neo4j serviceS
def has_suspicious_connections(user_id):
    neo4j_service = Neo4jService()
    data = {
        "user_id": user_id,
    }
    user_relations = neo4j_service.get_user_user_connections(data)
    suspicious_connections = []
    for relation in user_relations:
        if relation['score'] < 50:
            suspicious_connections.append(relation)
    if len(suspicious_connections) > 3: #has more than 3 suspicious connections
        return True
    return False

def has_circular_transactions(user_id):
    neo4j_service = Neo4jService()
    tx_data = {
        "user_id": user_id, 
        "max_depth": 4
    }
    circular_transaction = neo4j_service.detect_circular_transaction(tx_data)
    return circular_transaction is not None


def log_suspicious_actions(user_id, transaction_id=None):
    log = set()

    # check suspicious transactions amount
    if check_high_transactions_amount(user_id, transaction_id):
        log.add('high_txn_amount')

    # check suspicious monthly spending
    if check_suspicious_monthly_spent(user_id):
        log.add('high_monthly_spent')

    # check new account status
    if is_new_account(user_id):
        log.add('new_account')

    # check multiple devices
    if has_multiple_devices(user_id):
        log.add("has_multiple_devices")

    # check shared device count
    if has_shared_device_count(user_id):
        log.add("shared_device_count")

    # check suspicious connections
    if has_suspicious_connections(user_id):
        log.add("suspicious_connections")

    # check circular transactions
    if has_circular_transactions(user_id):
        log.add("circular_transaction_detected")

    return log
