

# picontrol

# this script controls the hardware of the pi
# it runs a redis pubsub, subscribed to 'control01' to 'control99' for various incoming messages
# and acts on them

# It publishes to 'event01' to 'event99' for events (to be described)

# it saves to redis keys:
#
# temperature
# etc
# etc
#


## note for debugging
# redis-cli
#> PUBLISH control01 status


import time

import os, sys, threading, logging

from logging.handlers import RotatingFileHandler


from redis import StrictRedis

from control import hardware, schedule, door, led, temperature


logfile = 'rempi.log'
handler = RotatingFileHandler(logfile, maxBytes=10000, backupCount=5)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', handlers= [handler])
logging.info('picontrol started')


# set up pins
result = hardware.initial_setup_outputs()
if not result:
    logging.error('Failed hardware initial setup')

# create redis connection
redis = StrictRedis(host='localhost', port=6379)


### create a dictionary of objects to control
state = { 'door': door.Door(redis),
          'led': led.LED(redis),
          'temperature':temperature.Temperature(redis)
        }


# Ensure the hardware values are read
state['led'].get_output()
state['temperature'].get_temperature()



# handlers to deal with incoming messages

def control01_handler(msg):
    "Handles the pubsub msg for control01 - this controls the door"
    message = msg['data']
    door = state['door']
    if message == b"status":
        print(door.status())


def control02_handler(msg):
    "Handles the pubsub msg for control02 - this controls the led"
    message = msg['data']
    led = state['led']
    if message == b"status":
        # refresh the status from hardware
        ledout = led.get_output()
        if ledout is None:
           logging.error('Failed to read the LED status')
    elif message == b"ON":
        led.set_output("ON")
        logging.info('LED set ON')
    elif message == b"OFF":
        led.set_output("OFF")
        logging.info('LED set OFF')


def control03_handler(msg):
    "Handles the pubsub msg for control03 - this requests a hardware read of the temperature"
    message = msg['data']
    temperature = state['temperature']
    if message == b"status":
        tmpt = temperature.get_temperature()
        if tmpt is None:
            logging.error('Failed to read the temperature')


# subscribe to control01, control02, control03
pubsub = redis.pubsub()  
pubsub.subscribe(**{'control01': control01_handler})
pubsub.subscribe(**{'control02': control02_handler})
pubsub.subscribe(**{'control03': control03_handler})

# run the pobsub with the above handlers in a thread
pubsubthread = pubsub.run_in_thread(sleep_time=0.01)


# create input listener callback

def inputcallback(input_name, state):
    "Callback when an input pin changes, name is the pin name as listed in hardware._INPUTS"
    logging.info('%s has changed state' % (input_name,))
    for item in state.keys():
        # tell each item a pin has changed, it is up to the
        # item whether it is interested or not
        item.pin_changed(input_name)

# create a Listen object and run its loop in its own thread
# this calls inputcallback when a pin changes state
listen = hardware.Listen(inputcallback, state)
listen.start_loop()


# create an event schedular to do periodic actions
scheduled_events = schedule.ScheduledEvents(redis, state)
# this is a callable which runs scheduled events
# it is a blocking call, and could be run in a separate thread
# however in this case it just runs here
logging.info('picontrol schedular started')
scheduled_events()



