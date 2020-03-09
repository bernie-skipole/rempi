

import sys

import paho.mqtt.client as mqtt

from redis import StrictRedis

from rempicomms import communications, schedule

# create redis connection
rconn = StrictRedis(host='localhost', port=6379)

# mqtt parameters

mqtt_ip = 'localhost'          # mqtt server, change as required, currently 'bernard-HP-Compaq-dc7900-Small-Form-Factor'
mqtt_port = 1883
mqtt_username = ''
mqtt_password = ''

userdata = {
            'comms':True,
            'comms_countdown':4,
            'from_topic':'From_RemPi01',
            'rconn':rconn
           }


### MQTT Handlers

def _on_message(client, userdata, message):
    "Callback when a message is received"

    # If no other message received, a heartbeat with topic 'From_ServerEngine/HEARTBEAT':
    # is sent by the server every six minutes to maintain userdata['comms_countdown']

    userdata['comms'] = True
    userdata['comms_countdown'] = 4
   
    if message.topic.startswith('From_WebServer/Outputs') or message.topic.startswith('From_ServerEngine/Outputs'):
        communications.action(client, userdata, message)
    elif message.topic == 'From_ServerEngine/Telescope/track':
        communications.telescope_track(client, userdata, message)
    elif message.topic == 'From_WebServer/Telescope/goto':
        communications.telescope_goto(client, userdata, message)
    elif message.topic == 'From_WebServer/Telescope/altaz':
        communications.telescope_altaz(client, userdata, message)
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
        elif payload == 'door':
            communications.door_status(client, userdata)


def _on_connect(client, userdata, flags, rc):
    "The callback for when the client receives a CONNACK response from the server, renew subscriptions"

    if rc == 0:
        userdata['comms_countdown'] = 4
        userdata['comms'] = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#"
        client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0)] )
    else:
        userdata['comms'] = False


def _on_disconnect(client, userdata, rc):
    "The client has disconnected, set userdata['comms'] = False"
    # userdata is the status_data dictionary
    userdata['comms'] = False



try:

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
    sys.exit(1)


### redis pubsub handlers, these are 'alerts' received from rempicontrol
### and requesting that info be published via mqtt

def alert01_handler(msg):
    "Handles the pubsub msg for alert01 - this sends info about the door"
    message = msg['data']
    if message == b"door status":
        # send the door status
        communications.door_status(mqtt_client, userdata)


def alert02_handler(msg):
    "Handles the pubsub msg for alert02 - this sends info about led"
    message = msg['data']
    if message == b"led status":
        # send the led status
        communications.led_status(mqtt_client, userdata)


# subscribe to alert01, alert02.., etc
pubsub = rconn.pubsub()  
pubsub.subscribe(alert01 = alert01_handler)
pubsub.subscribe(alert02 = alert02_handler)

# run the pubsub with the above handlers in a thread
pubsubthread = pubsub.run_in_thread(sleep_time=0.01)


### create an event schedular to do periodic actions

scheduled_events = schedule.ScheduledEvents(mqtt_client, userdata)
# this is a callable which runs scheduled events
# it is a blocking call, and runs here indefinitly
scheduled_events()



