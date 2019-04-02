

# communications

# action is 


def action(client, userdata, message):
    """called to initiate a control action by publishing to
       a redis topic control01, control02 etc.,"""
    payload = message.payload.decode("utf-8")
    redis = userdata['redis']
    if (message.topic == 'From_WebServer/Outputs/led') or (message.topic == 'From_ServerEngine/Outputs/led') or (message.topic == 'From_RemControl/Outputs/led'):
        # led control is on channel control02
        if payload == "ON":
            redis.publish('control02', 'ON')
        elif payload == "OFF":
            redis.publish('control02', 'OFF')
        else:
            # it must be an led status request
            led_status(client, userdata)


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
    temperature = redis.get('temperature').decode("utf-8")
    topic = userdata['from_topic'] + '/Outputs/temperature'
    client.publish(topic=topic, payload=temperature)


def status_request(client, userdata):
    "a full status request of all values"
    led_status(client, userdata, message)
    temperature_status(client, userdata)



