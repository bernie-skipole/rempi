
############################################################################
#
# package engine, __init__.py
#
# This module contains the function create_mqtt_redis
#
# which returns a tuple (mqtt client, redis connection),
# with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/#
# and running a threaded loop
# and with an on_message callback that calls further functions
# within this package
#
#############################################################################




import paho.mqtt.client as mqtt


from ..hardware import get_mqtt, get_redis


from .communications import door, redis_ops




def _on_message(client, userdata, message):
    "Callback when a message is received"

    # uncomment for testing
    # print(message.payload.decode("utf-8"))
    
    if message.topic.startswith('From_WebServer/Door'):
        door.action(client, userdata, message)
    elif message.topic.startswith('From_ServerEngine/Door'):
        door.action(client, userdata, message)
    elif message.topic == 'From_ServerEngine':
        # no subtopic, generally an initial full status request
        payload = message.payload.decode("utf-8")
        if payload == 'status_request':
            door.handle_status_request(client, userdata, message)



def inputcallback(name, userdata):
    "Callback when an input pin changes, name is the pin name"
    mqtt_client, rconn = userdata
    # In future, may call other functions dependent on which
    # pin is called, for example the 'door' pin
    if mqtt_client is None:
        return
    mqtt_client.publish("From_Pi01/Pin_Change", payload=name)


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
    except:
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
    except:
        client = None


    return (client, rconn)

