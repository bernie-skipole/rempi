#######################################################
#
# database_ops.py
# creates sqlite database to hold username and password
# and to store output values
#
#######################################################



import os, sqlite3, hashlib, random

from .. import FailPage, GoTo, ValidateError, ServerError

from . import hardware

_OUTPUTS = hardware.get_outputs()

# If it does not already exist, a database will be created in a directory
# beneath the projectfiles directory
_DATABASE_DIR_NAME =  'setup'
_DATABASE_NAME = 'setup.db'

# the following two values are set by the initial call to start_database
_DATABASE_PATH = ''
_DATABASE_EXISTS = False

# This is the access username
_USERNAME = "admin"
# This is the default access password, set when the database is first created
_PASSWORD = "password"

# If this pi logs output to a redis server, and it is useful to have server
# parameters stored in this database, and perhaps set from the pi web page
# REDIS VALUES
# _REDIS_IP = ''
# _REDIS_PORT = 6379
# _REDIS_AUTH = ''
# _REDIS_DB = 0



# If this pi accepts or sends commands to an MQTT server, and it is useful to have server
# parameters stored in this database, and perhaps set from the pi web page
# MQTT VALUES
# _MQTT_USERNAME = ''
# _MQTT_PASSWORD = ''
# _MQTT_IP = ''
# _MQTT_PORT = 1883


def get_access_user():
    return _USERNAME

def get_default_password():
    return _PASSWORD

def hash_password(password, seed=None):
    "Return (hashed_password, seed) if no seed given, create a random one"
    if not seed:
        # create seed
        seed = str(random.SystemRandom().randint(1000000, 9999999))
    seed_password = seed +  password
    hashed_password = hashlib.sha512( seed_password.encode('utf-8') ).digest()
    return hashed_password, seed


def start_database(projectfiles):
    """Must be called first, before any other database operation, to check if database
       exists, and if not, to create it, and to set globals _DATABASE_PATH and _DATABASE_EXISTS"""
    global _DATABASE_PATH, _DATABASE_EXISTS
    if _DATABASE_EXISTS:
        return
    database_dir = os.path.join(projectfiles, _DATABASE_DIR_NAME)
    # Set global variables
    _DATABASE_PATH = os.path.join(database_dir, _DATABASE_NAME)
    _DATABASE_EXISTS = True
    # make directory for database
    try:
        os.mkdir(database_dir)
    except FileExistsError:
        return
    # create the database
    con = open_database()
    try:
        # make access user password
        con.execute("create table users (username TEXT PRIMARY KEY, seed TEXT, password BLOB)")
        # make a table for each output type, text, integer and boolean
        con.execute("create table text_outputs (outputname TEXT PRIMARY KEY, value TEXT, default_on_pwr TEXT, onpower INTEGER)")
        con.execute("create table integer_outputs (outputname TEXT PRIMARY KEY, value INTEGER, default_on_pwr INTEGER, onpower INTEGER)")
        con.execute("create table boolean_outputs (outputname TEXT PRIMARY KEY, value INTEGER, default_on_pwr INTEGER, onpower INTEGER)")

        # If this pi logs output to a redis server
        # make a table for redis server items
        # con.execute("create table redis (redis_id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, port INTEGER, auth TEXT, db INTEGER)")


        # If this pi connects to a mqtt server
        # make a table for mqtt server items
        # con.execute("create table mqtt (mqtt_id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, port INTEGER, username TEXT, password TEXT)")


        # insert default values
        hashed_password, seed = hash_password(_PASSWORD)
        con.execute("insert into users (username, seed, password) values (?, ?, ?)", (_USERNAME, seed, hashed_password))
        for name in _OUTPUTS:
            outputtype, outputvalue, onpower, bcm = _OUTPUTS[name]
            if onpower:
                onpower = 1
            else:
                onpower = 0
            if outputtype == 'text':
                con.execute("insert into text_outputs (outputname, value, default_on_pwr, onpower) values (?, ?, ?, ?)", (name, outputvalue, outputvalue, onpower))
            elif outputtype == 'integer':
                con.execute("insert into integer_outputs (outputname, value, default_on_pwr, onpower) values (?, ?, ?, ?)", (name, outputvalue, outputvalue, onpower))
            elif outputtype == 'boolean':
                if outputvalue:
                    con.execute("insert into boolean_outputs (outputname, value, default_on_pwr, onpower) values (?, 1, 1, ?)", (name, onpower))
                else:
                    con.execute("insert into boolean_outputs (outputname, value, default_on_pwr, onpower) values (?, 0, 0, ?)", (name, onpower))

        # If this pi logs output to a redis server
        # con.execute("insert into redis (redis_id, ip, port, auth, db) values (?, ?, ?, ?, ?)", (None, _REDIS_IP, _REDIS_PORT, _REDIS_AUTH, _REDIS_DB))

        # If this pi connects to a mqtt server
        # con.execute("insert into mqtt (mqtt_id, ip, port, username, password) values (?, ?, ?, ?, ?)", (None, _MQTT_IP, _MQTT_PORT, _MQTT_USERNAME, _MQTT_PASSWORD))

        con.commit()
    finally:
        con.close()


def open_database():
    "Opens the database, and returns the database connection"
    if not _DATABASE_EXISTS:
        raise ServerError(message="Database does not exist.")
    if not _DATABASE_PATH:
       raise ServerError(message="Unknown database path.")
    # connect to database
    try:
        con = sqlite3.connect(_DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 1")
    except:
        raise ServerError(message="Failed database connection.")
    return con


def close_database(con):
    "Closes database connection"
    con.close()


def get_password(user, con=None):
    "Return (hashed_password, seed) for user, return None on failure"
    if (not  _DATABASE_EXISTS) or (not user):
        return
    if con is None:
        con = open_database()
        result = get_password(user, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select password, seed from users where username = ?", (user,))
        result = cur.fetchone()
    return result


def set_password(user, password, con=None):
    "Return True on success, False on failure, this updates an existing user"
    if not  _DATABASE_EXISTS:
        return False
    if con is None:
        try:
            con = open_database()
            result = set_password(user, password, con)
            con.close()
            return result
        except:
            return False
    else:
        hashed_password, seed = hash_password(password)
        try:
            con.execute("update users set password = ?, seed=? where username = ?", (hashed_password, seed, user))
            con.commit()
        except:
            return False
    return True


def get_output(name, con=None):
    "Return output value for given name, return None on failure"
    if name not in _OUTPUTS:
        return
    if not  _DATABASE_EXISTS:
        return
    if con is None:
        con = open_database()
        outputvalue = get_output(name, con)
        con.close()
    else:
        outputtype = _OUTPUTS[name][0]
        cur = con.cursor()
        if outputtype == 'text':
            cur.execute("select value from text_outputs where outputname = ?", (name,))
            result = cur.fetchone()
            if result is None:
                return
            outputvalue = result[0]
        elif outputtype == 'integer':
            cur.execute("select value from integer_outputs where outputname = ?", (name,))
            result = cur.fetchone()
            if result is None:
                return
            outputvalue = result[0]
        elif outputtype == 'boolean':
            cur.execute("select value from boolean_outputs where outputname = ?", (name,))
            result = cur.fetchone()
            if result is None:
                return
            outputvalue = bool(result[0])
        else:
            return
    return outputvalue


def set_output(name, value, con=None):
    "Return True on success, False on failure, this updates an existing output in the database"
    if name not in _OUTPUTS:
        return False
    if not  _DATABASE_EXISTS:
        return False
    if con is None:
        try:
            con = open_database()
            result = set_output(name, value, con)
            con.close()
            return result
        except:
            return False
    else:
        outputtype = _OUTPUTS[name][0]
        try:
            if outputtype == 'text':
                con.execute("update text_outputs set value = ? where outputname = ?", (value, name))
            elif outputtype == 'integer':
                con.execute("update integer_outputs set value = ? where outputname = ?", (value, name))
            elif outputtype == 'boolean':
                if value:
                    con.execute("update boolean_outputs set value = 1 where outputname = ?", (name,))
                else:
                    con.execute("update boolean_outputs set value = 0 where outputname = ?", (name,))
            else:
                return False
            con.commit()
        except:
            return False
    return True


def power_up_values():
    """Check database exists, if not, return an empty dictionary.
        If it does, return a dictionary of outputnames:values from the database
        The values being either the default_on_pwr values for each output with onpower True
        or last saved values if onpower is False"""
    if not _DATABASE_EXISTS:
        return {}
    # so database exists, for each output, get its value
    bool_tuple = (name for name in _OUTPUTS if _OUTPUTS[name][0] == 'boolean')
    int_tuple =  (name for name in _OUTPUTS if _OUTPUTS[name][0] == 'integer')
    text_tuple = (name for name in _OUTPUTS if _OUTPUTS[name][0] == 'text')
    outputdict = {}
    con = open_database()
    cur = con.cursor()
    # read values
    for name in bool_tuple:
        cur.execute("select value,  default_on_pwr, onpower from boolean_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is not None:
            if result[2]:
                outputdict[name] = bool(result[1])
            else:
                outputdict[name] = bool(result[0])
    for name in int_tuple:
        cur.execute("select value,  default_on_pwr, onpower from integer_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is not None:
            if result[2]:
                outputdict[name] = result[1]
            else:
                outputdict[name] = result[0]
    for name in text_tuple:
        cur.execute("select value,  default_on_pwr, onpower from text_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is not None:
            if result[2]:
                outputdict[name] = result[1]
            else:
                outputdict[name] = result[0]
    con.close()
    return outputdict


def get_power_values(name):
    """Check database exists, if not, return an empty tuple.
        If it does, return a tuple of (default_on_pwr, onpower) from
        the database for the given outputname
"""
    if name not in _OUTPUTS:
        return ()
    if not _DATABASE_EXISTS:
        return ()
    # so database exists
    con = open_database()
    cur = con.cursor()
    if _OUTPUTS[name][0] == 'boolean':
        cur.execute("select default_on_pwr, onpower from boolean_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is None:
            out = ()
        else:
            out = (bool(result[0]), bool(result[1]))
    elif _OUTPUTS[name][0] == 'integer':
        cur.execute("select default_on_pwr, onpower from integer_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is None:
            out = ()
        else:
            out = (result[0], bool(result[1]))
    elif _OUTPUTS[name][0] == 'text':
        cur.execute("select default_on_pwr, onpower from text_outputs where outputname = ?", (name,))
        result = cur.fetchone()
        if result is None:
            out = ()
        else:
            out = (result[0], bool(result[1]))
    else:
        out = ()
    con.close()
    return out


def set_power_values(name, default_on_pwr, onpower, con=None):
    "Return True on success, False on failure, this updates a name output power-up values"
    if name not in _OUTPUTS:
        return False
    if not  _DATABASE_EXISTS:
        return False
    if con is None:
        try:
            con = open_database()
            result = set_power_values(name, default_on_pwr, onpower, con)
            con.close()
            return result
        except:
            return False
    else:
        try:
            if onpower:
                onpower = 1
            else:
                onpower = 0
            if _OUTPUTS[name][0] == 'boolean':
                if default_on_pwr:
                    default_on_pwr = 1
                else:
                    default_on_pwr = 0
                con.execute("update boolean_outputs set default_on_pwr = ?,  onpower = ? where outputname= ?", (default_on_pwr, onpower, name))
            elif _OUTPUTS[name][0] == 'integer':
                con.execute("update integer_outputs set default_on_pwr = ?,  onpower = ? where outputname= ?", (default_on_pwr, onpower, name))
            elif _OUTPUTS[name][0] == 'text':
                con.execute("update text_outputs set default_on_pwr = ?,  onpower = ? where outputname= ?", (default_on_pwr, onpower, name))
            con.commit()
        except:
            return False
    return True


# The following two functions are only used if a redis server is used

def get_redis(redis_id=1, con=None):
    "Return redis ip, port, auth, db as a tuple on success, None on failure"
    if (not  _DATABASE_EXISTS) or (not redis_id):
        return
    if con is None:
        con = open_database()
        result = get_redis(redis_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select ip, port, auth, db from redis where redis_id = ?", (redis_id,))
        result = cur.fetchone()
        if not result:
            return
    return result


def set_redis(ip, port, auth, db, redis_id=1):
    "Return True on success, False on failure"
    if not  _DATABASE_EXISTS:
        return False
    try:
        con = open_database()
        con.execute("update redis set ip = ?, port = ?, auth = ?, db = ? where redis_id = ?", (ip, port, auth, db, redis_id))
        con.commit()
        con.close()
    except:
        return False
    return True


# The following two functions are only used if a mqtt server is used

def get_mqtt(mqtt_id=1, con=None):
    "Return mqtt ip, port, username, password as a tuple on success, None on failure"
    if (not  _DATABASE_EXISTS) or (not mqtt_id):
        return
    if con is None:
        con = open_database()
        result = get_mqtt(mqtt_id, con)
        con.close()
    else:
        cur = con.cursor()
        cur.execute("select ip, port, username, password from mqtt where mqtt_id = ?", (mqtt_id,))
        result = cur.fetchone()
        if not result:
            return
    return result


def set_mqtt(ip, port, username, password, mqtt_id=1):
    "Return True on success, False on failure"
    if not  _DATABASE_EXISTS:
        return False
    try:
        con = open_database()
        con.execute("update mqtt set ip = ?, port = ?, username = ?, password = ? where mqtt_id = ?", (ip, port, username, password, mgtt_id))
        con.commit()
        con.close()
    except:
        return False
    return True

