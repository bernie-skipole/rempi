#!/home/rempi/rempivenv/bin/python3


#################################################################
#
# pimqtt.py
#
# this script communicates with the remote server via MQTT
#
# it runs a redis pubsub, to communicate with picontrol which
# in turn implements the required actions
# and to rempiweb which allows local control
#
# It runs a schedular to maintain a 10 minute MQTT heartbeat,
# and sends a sensor status messages every fifteen minutes
#
#
#################################################################



import sys, time, threading

import paho.mqtt.client as mqtt

from redis import StrictRedis

from rempicomms import communications, schedule

# mqtt parameters

#mqtt_ip = '10.100.100.1'          # mqtt server
mqtt_ip = '10.34.167.1'           # development mqtt server
mqtt_port = 1883
mqtt_username = ''
mqtt_password = ''

userdata = {
            'comms':False,
            'comms_countdown':4,
            'from_topic':'From_RemPi01'
           }


### MQTT Handlers

def _on_message(client, userdata, message):
    "Callback when a message is received"

    # If no other message received, a heartbeat with topic 'From_ServerEngine/HEARTBEAT':
    # is sent by the server every six minutes to maintain userdata['comms_countdown']

    userdata['comms'] = True
    userdata['comms_countdown'] = 4

    print(message.topic)
   
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


def _on_connect(client, userdata, flags, rc):
    "The callback for when the client receives a CONNACK response from the server, renew subscriptions"

    if rc == 0:
        userdata['comms_countdown'] = 4
        userdata['comms'] = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#"
        client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0)] )
        print("MQTT client connected")
    else:
        userdata['comms'] = False


def _on_disconnect(client, userdata, rc):
    "The client has disconnected, set userdata['comms'] = False"
    # userdata is the status_data dictionary
    userdata['comms'] = False


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



if __name__ == "__main__":

    # have a pause to ensure various services are up and working
    time.sleep(3)

    # create redis connection
    rconn = StrictRedis(host='localhost', port=6379)

    # set rconn into userdata
    userdata['rconn'] = rconn

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

    print("MQTT loop started")

    ### create an event schedular to do periodic actions
    scheduled_events = schedule.ScheduledEvents(mqtt_client, userdata)
    # this is a callable which runs scheduled events, it
    # needs to be called in its own thread
    run_scheduled_events = threading.Thread(target=scheduled_events)
    # and start the scheduled thread
    run_scheduled_events.start()

    print("Scheduled events started")


    # subscribe to alert01, alert02.., etc
    pubsub = rconn.pubsub()
    pubsub.subscribe(alert01 = alert01_handler)
    pubsub.subscribe(alert02 = alert02_handler)

    print("redis pubsub started")

    # create loop which blocks and listens to redis.
    # Every two seconds, send scope position of packed structure: timestamp, alt, az

    count = 0

    while True:
        # loop to get redis pubsub messages
        message = pubsub.get_message()
        # uncomment for diagnostics
        #if message:
        #    print(message)
        time.sleep(0.1)
        count += 1
        if count > 20:
            # 2 seconds have passed
            count = 0
            telescope_topic = userdata['from_topic'] + '/Telescope/position'
            telescope_position = rconn.get('telescope_position')
            if telescope_position:
                mqtt_client.publish(topic=telescope_topic, payload=telescope_position)


