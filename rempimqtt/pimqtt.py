

import sys


try:
    import paho.mqtt.client as mqtt
except Exception:
    print("Unable to import paho.mqtt.client")
    sys.exit(1)

from redis import StrictRedis

# create redis connection
redis = StrictRedis(host='localhost', port=6379)

# Device mqtt parameters

_CONFIG = { 'name' : 'RemPi01',                # This device identifying name
            'mqtt_ip' : 'localhost',           # mqtt server, change as required, currently 192.168.1.91
            'mqtt_port' : 1883,
            'mqtt_username' : '',
            'mqtt_password' : ''
           }



from rempicomms import communications, schedule


def _on_message(client, userdata, message):
    "Callback when a message is received"

    # If no other message received, a heartbeat with topic 'From_ServerEngine/HEARTBEAT':
    # is sent by the server every six minutes to maintain _COMMS_COUNTDOWN

    userdata['comms'] = True
    userdata['comms_countdown'] = 4

    # uncomment for testing
    # print(message.payload.decode("utf-8"))
    
    if message.topic.startswith('From_WebServer/Outputs') or message.topic.startswith('From_ServerEngine/Outputs') or message.topic.startswith('From_RemControl/Outputs'):
        if userdata['enable_web_control']:
            communications.action(client, userdata, message)
    elif message.topic == 'From_ServerEngine/Inputs':
        # an initial full status request
        payload = message.payload.decode("utf-8")
        if payload == 'status_request':
            communications.status_request(client, userdata)
    elif message.topic == 'From_RemControl/status':
        # a status request from the terminal remscope control program
        payload = message.payload.decode("utf-8")
        if payload == 'led':
            communications.led_status(client, userdata)


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    "Comms now available, renew subscriptions"

    if rc == 0:
        userdata['comms_countdown'] = 4
        userdata['comms'] = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#" and "From_RemControl/#"
        client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0), ("From_RemControl/#", 0)] )
    else:
        userdata['comms'] = False


def _on_disconnect(client, userdata, rc):
    "The client has disconnected, set userdata['comms'] = False"
    # userdata is the status_data dictionary
    userdata['comms'] = False


mqtt_client = None

mqtt_ip = _CONFIG['mqtt_ip']
mqtt_port = _CONFIG['mqtt_port']
mqtt_username = _CONFIG['mqtt_username']
mqtt_password = _CONFIG['mqtt_password']


try:

    userdata = {'comms':True,
                'comms_countdown':4,
                'enable_web_control':True,
                'from_topic':'From_' + _CONFIG['name'],
                'redis':redis}

    # create an mqtt client instance
    mqtt_client = mqtt.Client(userdata=userdata)

    # attach callback function to client
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_disconnect = _on_disconnect
    mqtt_client.on_message = _on_message

    # If a username/password is set on the mqtt server
    if mqtt_username and mqtt_password:
        mqtt_client.username_pw_set(username = mqtt_username, password = mqtt_password)
    elif mqtt_username:
        mqtt_client.username_pw_set(username = mqtt_username)

    # connect to the server
    mqtt_client.connect(host=mqtt_ip, port=mqtt_port)

    # start a threaded loop
    mqtt_client.loop_start()
except Exception:
    sys.exit(2)

# create an event schedular to do periodic actions
scheduled_events = schedule.ScheduledEvents(mqtt_client, userdata)
# this is a callable which runs scheduled events
# it is a blocking call, and could be run in a separate thread
# however in this case it just runs here
scheduled_events()



