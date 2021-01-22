
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


# 保存验证码
def redis_set(key, value):
    return r.set(name=key, value=value, ex=900)


# 查询验证码
def redis_get(key):
    return r.get(name=key)


# 删除验证码
def redis_del(key):
    return r.delete(key)

