TASK: перенос rate limiting в Redis

FILE: src/mko_bi/core/security.py

GOAL: persistent rate limiting для production

IMPLEMENT:

import redis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
    
    def check_rate_limit(self, key: str, max_attempts: int, ttl: int) -> bool:
        # key = f"rate_limit:{identifier}"
        attempts = self._redis.get(key)
        if attempts and int(attempts) >= max_attempts:
            return False
        
        pipeline = self._redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, ttl)
        pipeline.execute()
        return True

LOGIC:

создать Redis клиент
перенести _login_attempts в Redis
настроить TTL для записей
убрать дублирование rate limiting

CONSTRAINTS:

использование Redis для хранения
TTL для автоматической очистки
работа в multi-worker окружении

DONE:

rate limiting в Redis
нет дублирования кода
работает в production
