from typing import Optional
from app.models.redis_model import RedisTrustScoreModel
from .suspicious_service import log_suspicious_actions
import logging


logger = logging.getLogger(__name__)


class RedisTrustScoreService:
    def __init__(self, ttl: int = 3600):
        self.model = RedisTrustScoreModel()
        self.ttl = ttl

    
    def get_score(self, user_id: str) -> Optional[int]:
        raw = self.model.get(user_id)
        if raw is not None:
            try:
                return int(raw)
            except ValueError:
                logger.warning(f"Failed to convert Redis trust score for user {user_id}: {raw}")
                return None
        return None

    def set_score(self, user_id: str, score: int, expire_seconds: Optional[int] = None):
        if expire_seconds is None:
            expire_seconds = self.ttl
        return self.model.set(user_id, str(score), expire_seconds)

    def has_score(self, user_id: str) -> bool:
        return self.model.exists(user_id)
    
    def update_score(self, user_id: str, score: int) -> bool:
        if self.has_score(user_id):
            return self.set_score(user_id, score)
        else:
            logger.warning(f"Attempted to update score for user {user_id} without an existing score.")
            return False
    
    def delete_score(self, user_id: str) -> bool:
        return self.model.delete(user_id)
    
    def get_or_load_score(self, user_id: str, loader_func: callable) -> int:
        score = self.get_score(user_id)
        if score is not None:
            return score
        score = loader_func(user_id)
        if score is not None:
            self.set_score(user_id, score)
            return score
        return 0

    
        
        
