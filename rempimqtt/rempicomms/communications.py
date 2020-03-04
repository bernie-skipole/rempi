

from struct import pack, unpack


def action(client, userdata, message):
    """called to initiate a control action by publishing to
       a redis topic control01, control02 etc.,"""
    payload = message.payload.decode("utf-8")
    rconn = userdata['rconn']
    web_control = rconn.get('web_control')
    if web_control == b'DISABLED':
        return
    if (message.topic == 'From_WebServer/Outputs/led') or (message.topic == 'From_ServerEngine/Outputs/led') or (message.topic == 'From_RemControl/Outputs/led'):
        # led control is on channel control02
        if payload == "ON":
            rconn.publish('control02', 'ON')
        elif payload == "OFF":
            rconn.publish('control02', 'OFF')
        else:
            # it must be an led status request
            led_status(client, userdata)
    elif (message.topic == 'From_WebServer/Outputs/door') or (message.topic == 'From_ServerEngine/Outputs/door') or (message.topic == 'From_RemControl/Outputs/door'):
        # door control is on channel control01
        if payload == "OPEN":
            rconn.publish('control01', 'OPEN')
        elif payload == "CLOSE":
            rconn.publish('control01', 'CLOSE')
        elif payload == "HALT":
            rconn.publish('control01', 'HALT')
        else:
            # it must be a door status request
            door_status(client, userdata)


def telescope_goto(client, userdata, message):
    """Called to accept From_WebServer/Telescope/goto topic and publish payload to redis"""
    rconn = userdata['rconn']
    web_control = rconn.get('web_control')
    if web_control == b'DISABLED':
        return
    rconn.publish('goto', message.payload)


def telescope_track(client, userdata, message):
    """Called to accept From_ServerEngine/Telescope/goto topic and set values in redis"""
    rconn = userdata['rconn']
    web_control = rconn.get('web_control')
    if web_control == b'DISABLED':
        return
    rconn.set('track', message.payload)
    # the track data is set (not published) as the rempicontrol service does not have to act
    # on this immediately, it can read the tracking data as it wants it


def telescope_altaz(client, userdata, message):
    """Called to accept From_WebServer/Telescope/altaz topic and publish to redis"""
    rconn = userdata['rconn']
    web_control = rconn.get('web_control')
    if web_control == b'DISABLED':
        return
    rconn.publish('altaz', message.payload)


def led_status(client, userdata):
    "Get the led status from redis and publish it via MQTT"
    if not userdata['comms']:
        return
    rconn = userdata['rconn']
    # get led status from rconn
    led_status = rconn.get('led')
    topic = userdata['from_topic'] + '/Outputs/led'
    if led_status == b"ON":
        client.publish(topic=topic, payload='ON')
    else:
        client.publish(topic=topic, payload='OFF')


def temperature_status(client, userdata):
    "Get the temperature from redis and publish it via MQTT"
    if not userdata['comms']:
        return
    rconn = userdata['rconn']
    # get temperature from rconn
    temperature = rconn.get('temperature')
    if temperature is None:
        temperature = "0.0"
    else:
        temperature = temperature.decode("utf-8")
    topic = userdata['from_topic'] + '/Inputs/temperature'
    client.publish(topic=topic, payload=temperature)


def door_status(client, userdata):
    "Get the door from redis and publish it via MQTT"
    if not userdata['comms']:
        return
    rconn = userdata['rconn']
    # get staus from rconn
    status = rconn.get('door_status')
    if status is None:
        status = "UNKNOWN"
    else:
        status = status.decode("utf-8")
    topic = userdata['from_topic'] + '/Inputs/door'
    client.publish(topic=topic, payload=status)


def status_request(client, userdata):
    "a full status request of all values"
    led_status(client, userdata)
    temperature_status(client, userdata)
    door_status(client, userdata)


