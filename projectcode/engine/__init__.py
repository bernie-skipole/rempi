
############################################################################
#
# package engine, __init__.py
#
# This module contains the functions:
#
# create_mqtt
#
# which creates an mqtt client
# with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/#
# and running a threaded loop
# and with an on_message callback that calls further functions
# within this package
#
# listen_to_inputs()
#
# Which returns a Listen object that listens for input pin changes
# and publishes to topic "From_Pi01/Inputs" with payload the name
# of the pin which has changed
#
# ScheduledEvents
#
# A class that sets up periodic events to occur each hour
#
#############################################################################


import sys, sched, time, logging

_mqtt_mod = True
try:
    import paho.mqtt.client as mqtt
except Exception:
    _mqtt_mod = False


# _COMMS_COUNTDOWN starts with a value of 4 and decremented every 10 minutes
# set to 4 every time a command is received
# via mqtt from the server

# if COMMS_COUNTDOWN reaches zero the program assumes the server or communications is down

_COMMS_COUNTDOWN = 4

from .. import hardware

from . import communications


def from_topic():
    "Returns a string 'From_name' where name is the hardware name of this device"
    return 'From_' + hardware.get_name()

def _on_message(client, userdata, message):
    "Callback when a message is received"

    # userdata is the status_data dictionary
    status_data = userdata

    global _COMMS_COUNTDOWN

    # If no other message received, a heartbeat with topic 'From_ServerEngine/HEARTBEAT':
    # is sent by the server every six minutes to maintain _COMMS_COUNTDOWN

    status_data['comms'] = True
    _COMMS_COUNTDOWN = 4

    # uncomment for testing
    # print(message.payload.decode("utf-8"))
    
    if message.topic.startswith('From_WebServer/Outputs') or message.topic.startswith('From_ServerEngine/Outputs') or message.topic.startswith('From_RemControl/Outputs'):
        if status_data['enable_web_control']:
            communications.action(client, status_data, message)
    elif message.topic == 'From_ServerEngine/Inputs':
        # an initial full status request
        payload = message.payload.decode("utf-8")
        if payload == 'status_request':
            communications.status_request(client, status_data, message)
    elif message.topic == 'From_RemControl/status':
        # a status request from the terminal remscope control program
        payload = message.payload.decode("utf-8")
        if payload == 'door':
            communications.output01_status(client, status_data, message)


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    "Comms now available, renew subscriptions"

    global _COMMS_COUNTDOWN

    # userdata is the status_data dictionary
    status_data = userdata

    if rc == 0:
        _COMMS_COUNTDOWN = 4
        status_data['comms'] = True
        logging.info("MQTT client connected")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#" and "From_RemControl/#"
        client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0), ("From_RemControl/#", 0)] )

    else:
        status_data['comms'] = False
        logging.critical('MQTT client not connected, code %s' % rc)


def _on_disconnect(client, userdata, rc):
    "The client has disconnected, set status_data['comms'] = False"
    # userdata is the status_data dictionary
    status_data = userdata
    status_data['comms'] = False
    logging.info("MQTT client disconnected")


def create_mqtt(status_data):
    """Creates an mqtt client,
       with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/# and From_RemControl/#
       and running a threaded loop
       and with an on_message callback that calls further functions
       within this package"""

    mqtt_client = None

    # Get the mqtt server parameters from hardware.py
    mqtt_ip, mqtt_port, mqtt_username, mqtt_password = hardware.get_mqtt()

    if not _mqtt_mod:
        print("paho.mqtt.client not loaded", file=sys.stderr)
        status_data['comms'] = False
        logging.critical('paho.mqtt.client not loaded')
        return

    print("Starting MQTT client...")
    logging.info("Starting MQTT client")

    try:
        # create an mqtt client instance
        mqtt_client = mqtt.Client(userdata=status_data)

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
    except Exception as e:
        mqtt_client = None
        print("Failed to create mqtt_client", file=sys.stderr)
        logging.critical('Failed to create mqtt_client')
    else:
        logging.info("MQTT client started")

    return mqtt_client



### set outputs ###

def set_output(output_name, value, proj_data):
    """Sets an output, given the output name and value"""
    mqtt_client = proj_data['mqtt_client']
    if output_name == 'output01':
        if (value is True) or (value == 'True') or (value == 'ON'):
            communications.output01_ON(proj_data['status'], mqtt_client)
        else:
            communications.output01_OFF(proj_data['status'], mqtt_client)
    # other output names to be checked here



### status request ###

def output_status(output_name, proj_data):
    """If a request for an output status has been received, respond to it"""
    mqtt_client = proj_data['mqtt_client']
    if mqtt_client is None:
        return
    communications.output_status(output_name, mqtt_client, proj_data['status'])


def input_status(input_name, proj_data):
    """If a request for an input status has been received, respond to it"""
    mqtt_client = proj_data['mqtt_client']
    if mqtt_client is None:
        return
    communications.input_status(input_name, mqtt_client, proj_data['status'])


###  input pin changes ###


def _inputcallback(input_name, proj_data):
    "Callback when an input pin changes, name is the pin name"
    mqtt_client = proj_data['mqtt_client']
    if mqtt_client is None:
        return
    input_status(input_name, proj_data)


def listen_to_inputs(proj_data):
    """create an input Listen object (defined in hardware.py),
       which calls _inputcallback on a pin change"""
    listen = hardware.Listen(_inputcallback, proj_data)
    listen.start_loop()
    return listen


###  scheduled actions ###


def event1(*args):
    "event1 is to publish status"
    try:
        if _mqtt_mod is None:
            return
        proj_data = args[0]
        if not proj_data['status']['comms']:
            return
        input_status("input01", proj_data)
        output_status("output01", proj_data)
    except Exception:
        # return without action if any failure occurs
        logging.error('Exception during scheduled Event1')
        return
    logging.info("Scheduled Event1 status sent.")


def event2(*args):
    "event2 is to publish status, and send temperature"
    try:
        if _mqtt_mod is None:
            return
        proj_data = args[0]
        if not proj_data['status']['comms']:
            return
        input_status("input01", proj_data)
        input_status("input03", proj_data)     # temperature
        output_status("output01", proj_data)
    except Exception:
        # return without action if any failure occurs
        logging.error('Exception during scheduled Event2')
        return
    logging.info("Scheduled Event2 status sent.")


def event3(*args):
    """event3 is called every ten minutes
       decrements _COMMS_COUNTDOWN, and checks if zero or less"""
    global _COMMS_COUNTDOWN
    proj_data = args[0]
    if _COMMS_COUNTDOWN < 1:
        logging.critical('Communications with main server has been lost.')
        proj_data['status']['comms'] = False
        return
    # _COMMS_COUNTDOWN is still positive, decrement it
    _COMMS_COUNTDOWN -= 1
    logging.info("Scheduled Event3 _COMMS_COUNTDOWN is %s.", _COMMS_COUNTDOWN)


### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, proj_data):
        "Stores the mqtt_clent and creates the schedule of hourly events"
        # create a list of event callbacks and minutes past the hour for each event in turn
        event_list = [ (event1, 1),   # event1 at one minute past the hour
                       (event2, 9),   # event 2 at 9 minutes past the hour
                       (event2, 24),  # event 2 again at 24 minutes past the hour
                       (event2, 39),  # etc.,
                       (event2, 54),
                       (event3, 2),   # heartbeat check every ten minutes
                       (event3, 12),
                       (event3, 22),
                       (event3, 32),
                       (event3, 42),
                       (event3, 52)]
        # sort the list
        self.event_list = sorted(event_list, key=lambda x: x[1])

        self.proj_data = proj_data
        self.schedule = sched.scheduler(time.time, time.sleep)


    @property
    def queue(self):
        return self.schedule.queue


    def _create_next_hour_events(self):
        "Create a new set of events for the following hour"

        # get a time tuple for now
        ttnow = time.localtime()
        # get the timestamp for the beginning of the next hour
        nexthour = 3600 + time.mktime( (ttnow.tm_year,
                                        ttnow.tm_mon,
                                        ttnow.tm_mday,
                                        ttnow.tm_hour,
                                        0,                  # zero minutes
                                        0,                  # zero seconds
                                        ttnow.tm_wday,
                                        ttnow.tm_yday,
                                        ttnow.tm_isdst)  )

        # create scheduled events which are to occur
        # at interval minutes during nexthour

        for evt_callback, mins in self.event_list:
            self.schedule.enterabs(time = nexthour + mins*60,
                                   priority = 1,
                                   action = evt_callback,
                                   argument = (self.proj_data,)
                                   )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
 
        final_event_time = nexthour + last_event[1]*60 + 30
        self.schedule.enterabs(time = final_event_time,
                               priority = 1,
                               action = self._create_next_hour_events
                               )


    def __call__(self): 
        "Schedule Events, and run the scheduler, this is a blocking call, so run in a thread"
        # set the scheduled events for the current hour

        # get a time tuple for now
        ttnow = time.localtime()
        # get the timestamp of now
        rightnow = time.mktime(ttnow)

        # get the timestamp for the beginning of the current hour
        thishour = time.mktime( (ttnow.tm_year,
                                 ttnow.tm_mon,
                                 ttnow.tm_mday,
                                 ttnow.tm_hour,
                                 0,                  # zero minutes
                                 0,                  # zero seconds
                                 ttnow.tm_wday,
                                 ttnow.tm_yday,
                                 ttnow.tm_isdst)  )

        # create times at which events are to occur
        # during the remaining part of this hour
        for evt_callback, mins in self.event_list:
            event_time = thishour + mins*60
            if event_time > rightnow:
                self.schedule.enterabs(time = event_time,
                                       priority = 1,
                                       action = evt_callback,
                                       argument = (self.proj_data,)
                                       )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
        
        final_event_time = thishour + last_event[1]*60 + 30
        self.schedule.enterabs(time = final_event_time,
                               priority = 1,
                               action = self._create_next_hour_events
                               )


        # and run the schedule
        self.schedule.run()


# How to use

# create event callback functions
# add them in time order to the self.event_list attribute, as tuples of (event function, minutes after the hour)

# create a ScheduledEvents instance
# scheduled_events = ScheduledEvents(proj_data)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required



