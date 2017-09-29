
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


import sys, sched, time, datetime


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

    rconn = None
    mqtt_client = None

    # Get the mqtt server parameters from hardware.py
    mqtt_ip, mqtt_port, mqtt_username, mqtt_password = get_mqtt()

    try:
        # create a redis connction
        rconn = redis_ops.open_redis()
    except:
        rconn = None

    if rconn is None
        print("Open Redis connection failed", file=sys.stderr)

    try:
        # create an mqtt client instance
        mqtt_client = mqtt.Client(client_id="Pi01", userdata=rconn)

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

    if mqtt_client is None
        print("Failed to create mqtt_client", file=sys.stderr)

    return (mqtt_client, rconn)


###  input pin changes ###


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


### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, mqtt_client, rconn):
        "Stores the mqtt_clent and rconn and creates the schedule of hourly events"
        self.mqtt_client = mqtt_client
        self.rconn = rconn
        self.schedule = sched.scheduler(time.time, time.sleep)
        # create the events and add them to the schedule
        self._create_events()


    def _minutespast(self, timetuple, minutes):
        "Returns time.time compatable seconds for the minutes interval after the hour in the given timetuple"
        return time.mktime(time.struct_time((timetuple.tm_year,
                                             timetuple.tm_mon,
                                             timetuple.tm_mday,
                                             timetuple.tm_hour,
                                             minutes,
                                             0,
                                             timetuple.tm_wday,
                                             timetuple.tm_yday,
                                             timetuple.tm_isdst)))

    def _event1_callback(self):
        "event1 is to publish status"
        outputs.status_request(self.mqtt_client, self.rconn)

    def _event2_callback(self):
        "event2 is to publish status"
        outputs.status_request(self.mqtt_client, self.rconn)

    def _event3_callback(self):
        "event3 is to publish status"
        outputs.status_request(self.mqtt_client, self.rconn)

    def _event4_callback(self):
        "event4 is to publish status"
        outputs.status_request(self.mqtt_client, self.rconn)

    def _event5_callback(self):
        "event5 is to publish status, and start schedule for next hour"
        outputs.status_request(self.mqtt_client, self.rconn)
        # Once this event is done, then the schedule is finished
        # so set up a new schedule
        self._create_events()


    def _create_events(self):
        "Create a new set of events for the following hour"
        # Create a timetuple of now plus one hour
        nexthour = datetime.datetime.now() + datetime.timedelta(hours=1)
        tt = nexthour.timetuple()
        # create times at which events are to occur
        # at interval minutes after the next hour

        # event1 at two minutes past the hour
        self.event1_time = self._minutespast(tt, 2)
        # event2 at 15 minutes past the hour
        self.event2_time = self._minutespast(tt, 15)
        # event3 at 30 minutes
        self.event3_time = self._minutespast(tt, 30)
        # event4 at 45 minutes
        self.event4_time = self._minutespast(tt, 45)
        # event5 at 54 minutes
        self.event5_time = self._minutespast(tt, 54)

        # enter these events into the schedule
        self.schedule.enterabs(self.event1_time, 1, self._event1_callback)
        self.schedule.enterabs(self.event2_time, 1, self._event2_callback)
        self.schedule.enterabs(self.event3_time, 1, self._event3_callback)
        self.schedule.enterabs(self.event4_time, 1, self._event4_callback)
        self.schedule.enterabs(self.event5_time, 1, self._event5_callback)

    def __call__(self): 
        "Run the schedular, this is a blocking call, so run in a thread"
        self.schedule.run()


# How to use
# create a ScheduledEvents instance
# scheduled_events = ScheduledEvents(mqtt_client, rconn)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required, and
# further event callbacks can be set as class methods, however the last one
# in the hour should include the call to self.create_events()

# avoid minutes zero time, since a new user will take over on the hour
# so last event should be several minutes before (minutes 54)
# and first event several minutes after (minutes 2)




