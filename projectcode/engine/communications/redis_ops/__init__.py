

import redis

from ....hardware import get_redis


def open_redis():
    "Returns a connection to the redis database, on failure returns None"

    rconn = None

    # redis server settings from hardware.py
    redis_ip, redis_port, redis_auth, redis_db = get_redis()

    if not redis_ip:
        return None

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




