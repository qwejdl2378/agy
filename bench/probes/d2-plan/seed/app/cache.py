import json
import redis
from . import config

r = redis.Redis.from_url(config.REDIS_URL)


def cached_project(slug, loader):
    key = f"project:{slug}"
    v = r.get(key)
    if v:
        return json.loads(v)
    data = loader()
    r.setex(key, 300, json.dumps(data))
    return data


def invalidate_project(slug):
    r.delete(f"project:{slug}")
