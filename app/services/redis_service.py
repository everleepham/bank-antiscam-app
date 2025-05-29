from typing import Optional
from app.models.redis_model import RedisTrustScoreModel

class RedisTrustScoreService:
    def __init__(self):
        self.model = RedisTrustScoreModel()
    
    def get_score(self, user_id: str) -> Optional[float]:
        raw = self.model.get(user_id)
        if raw is not None:
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    def set_score(self, user_id: str, score: float, expire_seconds: int = 3600) -> bool:
        return self.model.set(user_id, str(score), expire_seconds)

    def has_score(self, user_id: str) -> bool:
        return self.model.exists(user_id)
