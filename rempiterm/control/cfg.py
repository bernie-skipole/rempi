# Sets configuration items


# Edit this dictionary to store service parameters

_CONFIG = { 'name' : 'RemControl',                # This device identifying name
            'mqtt_ip' : 'localhost',           # mqtt server, change as required: '192.168.1.64' or '10.76.78.52'
            'mqtt_port' : 1883,
            'mqtt_username' : '',
            'mqtt_password' : ''
          }



def get_name():
    "Return identifying name"
    return _CONFIG['name']


def get_mqtt():
    "Returns tuple of mqtt server ip, port, username, password"
    return (_CONFIG['mqtt_ip'], _CONFIG['mqtt_port'], _CONFIG['mqtt_username'], _CONFIG['mqtt_password'])

