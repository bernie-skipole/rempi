
############################################################################
#
# package engine, __init__.py
#
# This module contains the functions:
#
# create_mqtt_redis
#
# which returns a tuple (mqtt client, redis connection),
# with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/#
# and running a threaded loop
# and with an on_message callback that calls further functions
# within this package
#
# listen_to_inputs(mqtt_client, rconn)
#
# Which returns a Listen object that listens for input pin changes
# and publishes to topic "From_Pi01/Inputs" with payload the name
# of the pin which has changed
#
#
#############################################################################


import sys


import paho.mqtt.client as mqtt


from ..hardware import get_mqtt, get_redis, Listen


from .communications import outputs, redis_ops




def _on_message(client, userdata, message):
    "Callback when a message is received"

    # uncomment for testing
    # print(message.payload.decode("utf-8"))
    
    if message.topic.startswith('From_WebServer/Outputs'):
        outputs.action(client, userdata, message)
    elif message.topic.startswith('From_ServerEngine/Outputs'):
        outputs.action(client, userdata, message)
    elif message.topic.startswith('From_ServerEngine/Inputs'):
        outputs.read(client, userdata, message)
    elif message.topic == 'From_ServerEngine':
        # no subtopic, generally an initial full status request
        payload = message.payload.decode("utf-8")
        if payload == 'status_request':
            outputs.status_request(client, userdata, message)


def create_mqtt_redis():
    """Returns a tuple (mqtt client, redis connection),
       with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/#
       and running a threaded loop
       and with an on_message callback that calls further functions
       within this package"""

    # Get the mqtt server parameters from hardware.py
    mqtt_ip, mqtt_port, mqtt_username, mqtt_password = get_mqtt()

    try:
        # create a redis connction
        rconn = redis_ops.open_redis()
    except Exception as e:
        print(e, file=sys.stderr)
        rconn = None

    try:
        # create an mqtt client instance
        client = mqtt.Client(client_id="Pi01", userdata=rconn)

        # attach callback function to client
        client.on_message = _on_message

        # If a username/password is set on the mqtt server
        if mqtt_username and mqtt_password:
            client.username_pw_set(username = mqtt_username, password = mqtt_password)
        elif mqtt_username:
            client.username_pw_set(username = mqtt_username)

        # connect to the server
        client.connect(host=mqtt_ip, port=mqtt_port)

        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#"
        client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0)] )

        # start a threaded loop
        client.loop_start()
    except Exception as e:
        print(e, file=sys.stderr)
        client = None

    return (client, rconn)


def _inputcallback(name, userdata):
    "Callback when an input pin changes, name is the pin name"
    mqtt_client, rconn = userdata
    if mqtt_client is None:
        return
    mqtt_client.publish("From_Pi01/Inputs", payload=name)


def listen_to_inputs(mqtt_client, rconn):
    """create an input Listen object (defined in hardware.py),
       which calls inputcallback on a pin change"""
    listen = Listen(_inputcallback, (mqtt_client, rconn))
    listen.start_loop()
    return listen



