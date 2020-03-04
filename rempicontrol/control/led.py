################################################################
#
# This module controls the led
#
################################################################

import logging

from . import hardware


class LED(object):

    def __init__(self, rconn):
        "set up an LED object"

        # info stored to rconn
        self.rconn = rconn

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
        elif message == b"OFF":
            self.set_output("OFF")

    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant - but could be a nice test to make a button turn on or off the led
        pass


    def get_output(self):
        "Called to get the led state from the hardware, saves it in rconn"
        # the led is called 'output01' in the hardware module
        try:
            out = hardware.get_boolean_output("output01")
        except Exception:
            return
        if out:
            self.rconn.set('led', 'ON')
            return 'ON'
        else:
            self.rconn.set('led', 'OFF')
            return 'OFF'


    def set_output(self, output):
        """Called to set the LED, output should be True or ON to turn on, anything else to turn off
           Sets the requested output into rconn"""
        if not output:
            out = False
        elif output is True:
            out = True
        elif output == "ON":
            out = True
        else:
            out = False

        if out:
            hardware.set_boolean_output("output01", True)
            self.rconn.set('led', 'ON')
            logging.info('LED set ON')
            # send an alert that the led has changed
            self.rconn.publish('alert02', 'led status')
            return 'ON'
        else:
            hardware.set_boolean_output("output01", False)
            self.rconn.set('led', 'OFF')
            logging.info('LED set OFF')
            # send an alert that the led has changed
            self.rconn.publish('alert02', 'led status')
            return 'OFF'

