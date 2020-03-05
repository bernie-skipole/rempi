
#################################################################
#
# picontrol
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

from control import hardware, schedule, door, led, temperature, motors, telescope

####### SET THE LOGFILE LOCATION

#logfile = "/opt/projectfiles/rempi/rempi.log"
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
          'temperature':temperature.Temperature(rconn),
          'motor1': motors.Motor('motor1',rconn),
          'motor2': motors.Motor('motor2',rconn),
          'telescope': telescope.Telescope(rconn)
        }


pubsub = rconn.pubsub(ignore_subscribe_messages=True)

# subscribe to control channels

pubsub.subscribe(control01=state['door'])
pubsub.subscribe(control02=state['led'])
pubsub.subscribe(control03=state['temperature'])
pubsub.subscribe(motor1control=state['motor1'])
pubsub.subscribe(motor2control=state['motor2'])
pubsub.subscribe(goto=state['telescope'].goto)        # calls the goto message of the telescope.Telescope object
pubsub.subscribe(altaz=state['telescope'].altaz)      # calls the altaz message of the telescope.Telescope object

# run the pubsub with the above handlers in a thread
pubsubthread = pubsub.run_in_thread(sleep_time=0.01)


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

scheduled_events = schedule.ScheduledEvents(rconn, state)
# this is a callable which runs scheduled events, it
# needs to be called in its own thread
run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the scheduled thread
run_scheduled_events.start()
logging.info('picontrol schedular started')

### and run the telescope worker. This is a blocking call, and runs indefinitly

telescope.worker(state)



