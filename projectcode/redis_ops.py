

import redis


_CONFIG = { 
            'redis_ip' : 'localhost',
            'redis_port' : 6379,
            'redis_auth' : '',
            'redis_db' : 0
          }


def get_redis():
    "Returns tuple of redis ip, port, auth, db"
    return (_CONFIG['redis_ip'], _CONFIG['redis_port'], _CONFIG['redis_auth'], _CONFIG['redis_db'])


def open_redis():
    "Returns a connection to the redis database, on failure returns None"

    rconn = None

    redis_ip, redis_port, redis_auth, redis_db = get_redis()

    if not redis_ip:
        return None

    # create a connection to the server
    try:
        rconn = redis.StrictRedis(host=redis_ip, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
    except:
        return None
    return rconn


def store_output(name, value, rconn=None):
    "Store an output, given the output name return True on success, False on failure"
    if rconn is None:
        try:
            rconn = open_redis()
        except:
            return False
    if rconn is None:
        return False
    if name == "output01":
        return _store_output01(value, rconn)
    return False


def get_output(name, rconn=None):
    "Get an output value, given the output name return None on failure"
    if rconn is None:
        try:
            rconn = open_redis()
        except:
            return
    if rconn is None:
        return
    if name == "output01":
        result = _get_output01(rconn)
        if result == "UNKNOWN":
            return
        return result 
    return        


def _get_output01(rconn):
    "Return rempi01_output01 string from redis database, if unable to access redis, return 'UNKNOWN'"
    if rconn is None:
        return 'UNKNOWN'
    output01 = 'UNKNOWN'
    try:
        output01 = rconn.get('rempi01_output01')
        if output01:
            output01 = output01.decode('utf-8')
        else:
            return 'UNKNOWN'
    except:
        return 'UNKNOWN'
    return output01


def _store_output01(value, rconn):
    "Stores the rempi01_output01 value in the database, True on success, False on failure"
    if rconn is None:
        return False
    result = False
    try:
        result = rconn.set('rempi01_output01', value)
    except:
        return False
    return result


def store_input(name, value, rconn=None):
    "Store an input, given the input name return True on success, False on failure"
    if rconn is None:
        try:
            rconn = open_redis()
        except:
            return False
    if rconn is None:
        return False
    if name == "input01":
        return _store_input01(value, rconn)
    return False


def get_input(name, rconn=None):
    "Get an input value, given the input name return None on failure"
    if rconn is None:
        try:
            rconn = open_redis()
        except:
            return
    if rconn is None:
        return
    if name == "input01":
        result = _get_input01(rconn)
        if result == "UNKNOWN":
            return
        return result 
    return


def _get_input01(rconn):
    "Return rempi01_input01 string from redis database, if unable to access redis, return 'UNKNOWN'"
    if rconn is None:
        return 'UNKNOWN'
    input01 = 'UNKNOWN'
    try:
        input01 = rconn.get('rempi01_input01')
        if input01:
            input01 = input01.decode('utf-8')
        else:
            return 'UNKNOWN'
    except:
        return 'UNKNOWN'
    return input01


def _store_input01(value, rconn):
    "Stores the rempi01_input01 value in the database, True on success, False on failure"
    if rconn is None:
        return False
    result = False
    try:
        result = rconn.set('rempi01_input01', value)
    except:
        return False
    return result


######################### log temperature to redis,

def log_temperature(thistime, temperature, rconn):
    "Log the given temperature to the redis connection rconn, return True on success, False on failure"
    if temperature is None:
        return False
    if rconn is None:
        return False
    try:
        # create a datapoint to set in the redis server
        point = thistime.strftime("%Y-%m-%d %H:%M") + " " + str(temperature)
        rconn.rpush("rempi01_temperature", point)
        # and limit number of points to 200
        rconn.ltrim("rempi01_temperature", -200, -1)
    except:
        return False
    return True




