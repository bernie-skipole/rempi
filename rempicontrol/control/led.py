################################################################
#
# This module controls the led
#
################################################################

import logging

from . import hardware


class LED(object):

    def __init__(self, redis):
        "set up an LED object"

        # info stored to redis
        self.redis = redis

        # Ensure the hardware values are read on startup
        self.get_output()


    def __call__(self, msg):
        "Handles the pubsub msg"
        message = msg['data']
        if message == b"status":
            # refresh redis from hardware
            ledout = self.get_output()
            if ledout is None:
               logging.error('Failed to read the LED status')
        elif message == b"ON":
            self.set_output("ON")
            logging.info('LED set ON')
        elif message == b"OFF":
            self.set_output("OFF")
            logging.info('LED set OFF')


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant - but could be a nice test to make a button turn on or off the led
        pass


    def get_output(self):
        "Called to get the led state from the hardware, saves it in redis"
        # the led is called 'output01' in the hardware module
        try:
            out = hardware.get_boolean_output("output01")
        except Exception:
            return
        if out:
            self.redis.set('led', 'ON')
            return 'ON'
        else:
            self.redis.set('led', 'OFF')
            return 'OFF'


    def set_output(self, output):
        """Called to set the LED, output should be True or ON to turn on, anything else to turn off
           Sets the requested output into Redis"""
        if not output:
            out = False
        elif output is True:
            out = True
        elif output == "ON":
            out = True
        else:
            out = False

        if out:
            self.redis.set('led', 'ON')
            hardware.set_boolean_output("output01", True)
            # send an alert that the led has changed
            self.redis.publish('alert02', 'led status')
            return 'ON'
        else:
            self.redis.set('led', 'OFF')
            hardware.set_boolean_output("output01", False)
            # send an alert that the led has changed
            self.redis.publish('alert02', 'led status')
            return 'OFF'

