# app/db/redis.py
import redis
from app.utils.config import Config

redis_client = redis.from_url(Config.REDIS_URI)
