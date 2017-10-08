
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

from .. import hardware

from .communications import outputs, redis_ops


def from_topic():
    "Returns a string 'From_name' where name is the hardware name of this device"
    return 'From_' + hardware.get_name()

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

    rconn = None
    mqtt_client = None

    # Get the mqtt server parameters from hardware.py
    mqtt_ip, mqtt_port, mqtt_username, mqtt_password = hardware.get_mqtt()

    try:
        # create a redis connction
        rconn = redis_ops.open_redis()
    except:
        rconn = None

    if rconn is None:
        print("Open Redis connection failed", file=sys.stderr)


    if not _mqtt_mod:
        print("Failed to create mqtt_client", file=sys.stderr)
        return (None, rconn)

    try:
        # create an mqtt client instance
        mqtt_client = mqtt.Client(client_id=hardware.get_name(), userdata=rconn)

        # attach callback function to client
        mqtt_client.on_message = _on_message

        # If a username/password is set on the mqtt server
        if mqtt_username and mqtt_password:
            mqtt_client.username_pw_set(username = mqtt_username, password = mqtt_password)
        elif mqtt_username:
            mqtt_client.username_pw_set(username = mqtt_username)

        # connect to the server
        mqtt_client.connect(host=mqtt_ip, port=mqtt_port)

        # subscribe to topics "From_WebServer/#" and "From_ServerEngine/#"
        mqtt_client.subscribe( [("From_WebServer/#", 0), ("From_ServerEngine/#", 0)] )

        # start a threaded loop
        mqtt_client.loop_start()
    except:
        mqtt_client = None

    if mqtt_client is None:
        print("Failed to create mqtt_client", file=sys.stderr)

    return (mqtt_client, rconn)


###  input pin changes ###


def _inputcallback(name, userdata):
    "Callback when an input pin changes, name is the pin name"
    mqtt_client, rconn = userdata
    if mqtt_client is None:
        return
    mqtt_client.publish(from_topic() + "/Inputs", payload=name)


def listen_to_inputs(mqtt_client, rconn):
    """create an input Listen object (defined in hardware.py),
       which calls inputcallback on a pin change"""
    listen = hardware.Listen(_inputcallback, (mqtt_client, rconn))
    listen.start_loop()
    return listen


###  scheduled actions ###


def event1(mqtt_client, rconn):
    "event1 is to publish status"
    outputs.input_status("input01", mqtt_client, rconn)
    outputs.output_status("output01", mqtt_client, rconn)


def event2(mqtt_client, rconn):
    "event2 is to publish status, and send temperature"
    outputs.input_status("input01", mqtt_client, rconn)
    outputs.output_status("output01", mqtt_client, rconn)
    temperature = hardware.get_temperature()
    redis_ops.log_temperature(rconn, temperature)




### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, mqtt_client, rconn):
        "Stores the mqtt_clent and rconn and creates the schedule of hourly events"
        # create a list of event callbacks and minutes past the hour for each event in turn
        self.event_list = [(event1, 2), (event2, 9), (event2, 24), (event2, 39), (event2, 54)]
        self.mqtt_client = mqtt_client
        self.rconn = rconn
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
                                   argument = (self.mqtt_client, self.rconn)
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
                                       argument = (self.mqtt_client, self.rconn)
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
# scheduled_events = ScheduledEvents(mqtt_client, rconn)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required



