
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


import sys, sched, time

_mqtt_mod = True
try:
    import paho.mqtt.client as mqtt
except:
    _mqtt_mod = False

# initially assume no mqtt connection
_mqtt_connected = False

# The mqtt_client
MQTT_CLIENT = None

from .. import hardware

from . import communications


def from_topic():
    "Returns a string 'From_name' where name is the hardware name of this device"
    return 'From_' + hardware.get_name()

def _on_message(client, userdata, message):
    "Callback when a message is received, userdata is state_values"

    # uncomment for testing
    # print(message.payload.decode("utf-8"))
    
    if message.topic.startswith('From_WebServer/Outputs'):
        communications.action(client, userdata, message)
    elif message.topic == 'From_ServerEngine/Inputs':
        # an initial full status request
        payload = message.payload.decode("utf-8")
        if payload == 'status_request':
            communications.status_request(client, userdata, message)


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    global _mqtt_connected
    if rc != 0:
        # client not connected
        _mqtt_connected = False
        return
    _mqtt_connected = True
    print("MQTT client connected")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#"
    client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0)] )


def _on_disconnect(client, userdata, rc):
    global _mqtt_connected
    _mqtt_connected = False


def create_mqtt(state_values):
    """Creates an mqtt client,
       with the mqtt client subscribed to From_WebServer/# and From_ServerEngine/#
       and running a threaded loop
       and with an on_message callback that calls further functions
       within this package"""

    global MQTT_CLIENT

    # Get the mqtt server parameters from hardware.py
    mqtt_ip, mqtt_port, mqtt_username, mqtt_password = hardware.get_mqtt()

    if not _mqtt_mod:
        print("Failed to create mqtt_client", file=sys.stderr)
        return

    print("Waiting for MQTT connection...")

    try:
        # create an mqtt client instance
        MQTT_CLIENT = mqtt.Client(client_id=hardware.get_name(), userdata=state_values)

        # attach callback function to client
        MQTT_CLIENT.on_connect = _on_connect
        MQTT_CLIENT.on_disconnect = _on_disconnect
        MQTT_CLIENT.on_message = _on_message

        # If a username/password is set on the mqtt server
        if mqtt_username and mqtt_password:
            MQTT_CLIENT.username_pw_set(username = mqtt_username, password = mqtt_password)
        elif mqtt_username:
            MQTT_CLIENT.username_pw_set(username = mqtt_username)

        # connect to the server
        MQTT_CLIENT.connect(host=mqtt_ip, port=mqtt_port)

        # start a threaded loop
        MQTT_CLIENT.loop_start()
    except Exception as e:
        MQTT_CLIENT = None

    if MQTT_CLIENT is None:
        print("Failed to create mqtt_client", file=sys.stderr)


### status request ###

def output_status(output_name, state_values):
    """If a request for an output status has been received, respond to it"""
    global MQTT_CLIENT
    communications.output_status(output_name, MQTT_CLIENT, state_values)


def input_status(input_name):
    """If a request for an input status has been received, respond to it"""
    global MQTT_CLIENT
    communications.input_status(input_name, MQTT_CLIENT)


###  input pin changes ###


def _inputcallback(input_name, state_values):
    "Callback when an input pin changes, name is the pin name"
    global MQTT_CLIENT
    if MQTT_CLIENT is None:
        return
    if _mqtt_connected:
        input_status(input_name)


def listen_to_inputs(state_values):
    """create an input Listen object (defined in hardware.py),
       which calls _inputcallback on a pin change"""
    listen = hardware.Listen(_inputcallback, state_values)
    listen.start_loop()
    return listen


###  scheduled actions ###


def event1(*args):
    "event1 is to publish status"
    if _mqtt_mod is None:
        return
    state_values = args[0]
    if _mqtt_connected:
        communications.input_status("input01", MQTT_CLIENT)
        communications.output_status("output01", MQTT_CLIENT, state_values)


def event2(*args):
    "event2 is to publish status, and send temperature"
    if _mqtt_mod is None:
        return
    state_values = args[0]
    if _mqtt_connected:
        communications.input_status("input01", MQTT_CLIENT)
        communications.input_status("input03", MQTT_CLIENT)     # temperature
        communications.output_status("output01", MQTT_CLIENT, state_values)



### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, state_values):
        "Stores the mqtt_clent and creates the schedule of hourly events"
        # create a list of event callbacks and minutes past the hour for each event in turn
        self.event_list = [(event1, 1),   # event1 at one minute past the hour
                           (event2, 9),   # event 2 at 9 minutes past the hour
                           (event2, 24),  # event 2 again at 24 minutes past the hour
                           (event2, 39),  # etc.,
                           (event2, 54)]
        self.state_values = state_values
        self.schedule = sched.scheduler(time.time, time.sleep)


    @property
    def queue(self):
        return self.schedule.queue


    def _create_next_hour_events(self):
        "Create a new set of events for the following hour"

        # On moving into the next hour, thishour timestamp is moved
        # forward by an hour 
        self.thishour = self.thishour + 3600

        # create scheduled events which are to occur
        # at interval minutes during thishour

        for evt_callback, mins in self.event_list:
            self.schedule.enterabs(time = self.thishour + mins*60,
                                   priority = 1,
                                   action = evt_callback,
                                   argument = (self.state_values,)
                                   )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
 
        final_event_time = self.thishour + last_event[1]*60 + 30
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
        self.thishour = time.mktime((ttnow.tm_year,
                                     ttnow.tm_mon,
                                     ttnow.tm_mday,
                                     ttnow.tm_hour,
                                     0,                  # zero minutes
                                     0,                  # zero seconds
                                     ttnow.tm_wday,
                                     ttnow.tm_yday,
                                     ttnow.tm_isdst))

        # create times at which events are to occur
        # during the remaining part of this hour
        for evt_callback, mins in self.event_list:
            event_time = self.thishour + mins*60
            if event_time > rightnow:
                self.schedule.enterabs(time = event_time,
                                       priority = 1,
                                       action = evt_callback,
                                       argument = (self.state_values,)
                                       )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
        
        final_event_time = self.thishour + last_event[1]*60 + 30
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
# scheduled_events = ScheduledEvents(state_values)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required



