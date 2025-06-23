from datetime import datetime, timedelta
from fastapi import HTTPException
from app.utils.trust_policies import TRUST_POLICY
from app.utils.trust_score import SCORE
from app.models.mongo_model import MongoTransactionModel
from app.services.mongo_service import MongoService
from app.services.redis_service import RedisTrustScoreService
from app.services.score_service import get_score
from app.models.mongo_model import TransactionStatus
from typing import Optional
from flask import abort, jsonify


redis = RedisTrustScoreService()
mongo = MongoService()

def get_policy_by_score(score: int): # find the limitation by score
    for policy in TRUST_POLICY:
        if policy["min"] <= score <= policy["max"]:
            return policy
    return None


def enforce_trust_policy(
    user_id: str,
    mongo_model: MongoTransactionModel = None,
    amount: float = None,
    action: str = "transaction", # or login,
    score: Optional[int] = None
):   
    # get score
    if score is None:
        score = get_score(user_id)
        
    # get policy matched  
    
    policy = get_policy_by_score(score)
    if not policy:
        raise HTTPException(500, "Unable to determine trust policy")
    
    restrictions = policy["restrictions"] or {}
    now = datetime.now()
    
    if restrictions.get("locked"):
        abort(403, description="Account is locked. Identity verification required")

    # check action, if not transaction, end 
    if action != "transaction" or not restrictions:
        return
    
    transactions = list(mongo_model.collection.find({
        "sender.user_id": user_id,
        "timestamp": {"$gte": now - timedelta(days=90)},
        "status": TransactionStatus.VERIFIED.value
    }))
    
    if "total_amount_limit" in restrictions:
        print(f"txn list: {transactions}")
        total = sum(t["amount"] for t in transactions)
        if total + amount > restrictions["total_amount_limit"]:
            abort(403, description=f"Limit exceeded: Max €{restrictions['total_amount_limit']} in 3 months")

    if "max_high_value_txns" in restrictions:
        start_of_month = now.replace(day=1)
        monthly_txns = [t for t in transactions if t["timestamp"] >= start_of_month and t["amount"] >= restrictions["threshold"]]
        if len(monthly_txns) >= restrictions["max_high_value_txns"]:
            abort(403, description=f"Limit exceeded: Max {restrictions['max_high_value_txns']} transactions > €{restrictions['threshold']} in 1 month")

    if "max_txns_per_month" in restrictions:
        start_of_month = now.replace(day=1)
        monthly_txns = [t for t in transactions if t["timestamp"] >= start_of_month]

        if len(monthly_txns) >= restrictions["max_txns_per_month"]:
            abort(403, description=f"Limit exceeded: Max {restrictions['max_txns_per_month']} transactions per month")

        if amount > restrictions["max_txn_amount"]:
            abort(403, description=f"Transaction too high: Max €{restrictions['max_txn_amount']} per transaction for this trust level")

    return
            

    
    
        