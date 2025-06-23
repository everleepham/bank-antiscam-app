from .suspicious_service import log_suspicious_actions
from app.services.redis_service import RedisTrustScoreService
from app.services.mongo_service import MongoService
from app.models.mongo_model import MongoUserModel
from app.utils.trust_rules import RULES
from app.utils.trust_score import SCORE
from typing import Optional

# get score
# update score on redis
# update score on mongo

redis = RedisTrustScoreService()
mongo = MongoService()
mongo_user = MongoUserModel()


def get_flag_and_warning(score: int):
    for level in SCORE:
        if level["min"] <= score <= level["max"]:
            return level["flag"], level["warning"]
    return "Unknown", None

def get_score(user_id: str) -> int:
    score = redis.get_or_load_score(user_id, mongo.get_score)
    return score if score is not None else 0

def calculate_score(user_id: str, transaction_id=None) -> tuple[int, set[str]]:
    suspicious_actions = log_suspicious_actions(user_id, transaction_id)

    score = get_score(user_id)

    user_data = mongo_user.read(user_id)
    print(f"DEBUG: user_data for user_id={user_id}: {user_data}")

    already_applied_rules = set(user_data.get("score_deductions_applied") or [])

    newly_applied_rules = set()

    for rule in RULES:
        if rule not in suspicious_actions:
            continue

        # only this rule can be applied multiple time
        if rule == "high_transaction_amount":
            score += RULES[rule]
        elif rule not in already_applied_rules and score > 0:
            score += RULES[rule]
            newly_applied_rules.add(rule)

    # update score in redis
    redis.update_score(user_id, score)

    if newly_applied_rules:
        mongo_user.append_deductions(user_id, list(newly_applied_rules))

    return score, suspicious_actions


def update_score_mongo(user_id: str, old_score: Optional[int] = None):
    if old_score is None:
        old_score = mongo.get_score(user_id)
    new_score = redis.get_score(user_id)
    if new_score is not None and old_score != new_score:
        mongo.update_score(user_id, new_score)
        return "Score updated successfully in MongoDB"
