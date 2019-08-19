

# communications

# action is 


def action(client, userdata, message):
    """called to initiate a control action by publishing to
       a redis topic control01, control02 etc.,"""
    payload = message.payload.decode("utf-8")
    redis = userdata['redis']
    web_control = redis.get('web_control')
    if web_control == b'DISABLED':
        return
    if (message.topic == 'From_WebServer/Outputs/led') or (message.topic == 'From_ServerEngine/Outputs/led') or (message.topic == 'From_RemControl/Outputs/led'):
        # led control is on channel control02
        if payload == "ON":
            redis.publish('control02', 'ON')
        elif payload == "OFF":
            redis.publish('control02', 'OFF')
        else:
            # it must be an led status request
            led_status(client, userdata)
    elif (message.topic == 'From_WebServer/Outputs/door') or (message.topic == 'From_ServerEngine/Outputs/door') or (message.topic == 'From_RemControl/Outputs/door'):
        # door control is on channel control01
        if payload == "OPEN":
            redis.publish('control01', 'OPEN')
        elif payload == "CLOSE":
            redis.publish('control01', 'CLOSE')
        else:
            # it must be a door status request
            door_status(client, userdata)


def led_status(client, userdata):
    "Get the led status from redis and publish it via MQTT"
    if not userdata['comms']:
        return
    redis = userdata['redis']
    # get led status from redis
    led_status = redis.get('led')
    topic = userdata['from_topic'] + '/Outputs/led'
    if led_status == b"ON":
        client.publish(topic=topic, payload='ON')
    else:
        client.publish(topic=topic, payload='OFF')


def temperature_status(client, userdata):
    "Get the temperature from redis and publish it via MQTT"
    if not userdata['comms']:
        return
    redis = userdata['redis']
    # get temperature from redis
    temperature = redis.get('temperature')
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
    redis = userdata['redis']
    # get staus from redis
    status = redis.get('door_status')
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


