from .suspicious_service import log_suspicious_actions
from app.services.redis_service import RedisTrustScoreService
from app.services.mongo_service import MongoService
from app.utils.trust_rules import RULES
from typing import Optional

# get score
# update score on redis
# update score on mongo

redis = RedisTrustScoreService()
mongo = MongoService()


def get_score(user_id: str) -> int:
    score = redis.get_or_load_score(user_id, mongo.get_score)
    return score if score is not None else 0

def calculate_score(user_id: str, transaction_id=None, device_id=None) -> int:
    suspicious_actions = log_suspicious_actions(user_id, transaction_id, device_id)

    score = get_score(user_id)

    for rule in RULES:
        if rule in suspicious_actions:
            score += RULES[rule]

    redis.update_score(user_id, score)
    return score

def update_score_mongo(user_id: str, old_score: Optional[int] = None):
    if old_score is None:
        old_score = mongo.get_score(user_id)
    new_score = redis.get_score(user_id)
    if new_score is not None and old_score != new_score:
        mongo.update_score(user_id, new_score)
        return "Score updated successfully in MongoDB"
