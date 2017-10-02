
import datetime

_redis_mod = True
try:
    import redis
except:
    _redis_mod = False




from ....hardware import get_redis


def open_redis():
    "Returns a connection to the redis database, on failure returns None"

    if not _redis_mod:
        return

    rconn = None

    # redis server settings from hardware.py
    redis_ip, redis_port, redis_auth, redis_db = get_redis()

    if not redis_ip:
        return

    # create a connection to the server
    try:
        rconn = redis.StrictRedis(host=redis_ip, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
    except:
        return None
    return rconn



def store_output01(status, rconn):
    "Stores the output01 in the database, True on success, False on failure"
    if rconn is None:
        return False
    result = False
    try:
        result = rconn.set('output01', status)
    except:
        return False
    return result



######################### log temperature to redis,

def log_temperature(rconn, temperature=None):
    "Log the given temperature to the redis connection rconn, return True on success, False on failure"
    if temperature is None:
        return False
    if rconn is None:
        return False
    try:
        # create a datapoint to set in the redis server
        point = datetime.utcnow().strftime("%Y-%m-%d %H:%M") + " " + str(temperature)
        rconn.rpush("temperature", point)
        # and limit number of points to 200
        rconn.ltrim("temperature", 0,200)
    except:
        return False
    return True


