#!/home/rempi/rempivenv/bin/python3

# The above line allows this script to be executed within the previously
# prepared virtual environment



#################################################################
#
# picontrol.py
#
# this script controls the hardware of the pi
#
# It creates and writes to a logfile
# it runs a redis pubsub, subscribing to incoming messages
# and calls sub modules (such as door) to take actions
#
# It listens to hardware input pins, again calling sub modules
#
# It runs a schedular for repetetive tasks
#
# It finally runs the telescope worker to operate it
#
#################################################################


import time

import os, sys, threading, logging

from logging.handlers import RotatingFileHandler

from redis import StrictRedis

from control import hardware, schedule, door, led, temperature, telescope

# have a pause to ensure various services are up and working
time.sleep(3)


####### SET THE LOGFILE LOCATION

#logfile = "/home/rempi/projectfiles/rempi/rempi.log"
logfile = "/home/bernard/rempi.log"
handler = RotatingFileHandler(logfile, maxBytes=10000, backupCount=5)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', handlers= [handler])
logging.info('picontrol started')


# set up pins
result = hardware.initial_setup_outputs()
if not result:
    logging.error('Failed hardware initial setup')

# create redis connection
rconn = StrictRedis(host='localhost', port=6379)


### create a dictionary of objects to control, these objects are callable handlers
state = {
          'door': door.Door(rconn),
          'led': led.LED(rconn),
          'temperature':temperature.Temperature(rconn)
        }

# Telescope is the instrument being controlled
Telescope = telescope.Telescope(rconn, state)

pubsub = rconn.pubsub(ignore_subscribe_messages=True)

# subscribe to control channels

pubsub.subscribe(control01=state['door'])
pubsub.subscribe(control02=state['led'])
pubsub.subscribe(control03=state['temperature'])
pubsub.subscribe(motor1control=Telescope.motor1)  # probably to be removed from here - as motors will be controlled by the Telescope object
pubsub.subscribe(motor2control=Telescope.motor2)  # directly, and not via redis - allowed here for testing from web server
pubsub.subscribe(goto=Telescope.goto)        # calls the goto message of the Telescope object
pubsub.subscribe(altaz=Telescope.altaz)      # calls the altaz message of the Telescope object

### create input listener callback

def inputcallback(input_name, state):
    "Callback when an input pin changes, name is the pin name as listed in hardware._INPUTS"
    logging.info('%s has changed state' % (input_name,))
    # currently, only the Door object may be interested in a pin change
    state['door'].pin_changed(input_name)
    # other objects may also use this in due course

# create a Listen object and run its loop in its own thread
# this calls inputcallback when a pin changes state
listen = hardware.Listen(inputcallback, state)
listen.start_loop()

### create an event schedular to do periodic actions

scheduled_events = schedule.ScheduledEvents(rconn, state, Telescope)
# this is a callable which runs scheduled events, it
# needs to be called in its own thread
run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the scheduled thread
run_scheduled_events.start()
logging.info('picontrol schedular started')


### and run the telescope worker. This is a blocking call, so run in thread
run_telescope = threading.Thread(target=Telescope)
# and start the telescope
run_telescope.start()
logging.info('Telescope control started')

# blocks and listens to redis
while True:
    message = pubsub.get_message()
    if message:
        print(message)
    time.sleep(0.1)


