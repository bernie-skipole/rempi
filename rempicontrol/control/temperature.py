################################################################
#
# This module measures temperature
#
################################################################

import logging

from . import hardware


class Temperature(object):

    def __init__(self, rconn):
        "set up a Temperature object"
        # info will be stored to redis
        self.rconn = rconn
        # Ensure the hardware values are read on startup
        temperature = self.get_temperature()
        self.set_temperature(temperature)


    def __call__(self, msg):
        """get and store the temperature, returns the temperature
           generally called at intervals by event1 of the schedule module"""
        # sets hardware temperature into redis
        temperature = self.get_temperature()
        self.set_temperature(temperature)
        return temperature


    def handle(self, msg):
        """Handles the control03 pubsub msg
           If payload requests status, get and store the temperature"""
        message = msg['data']
        if message == b"status":
            # sets hardware temperature into redis
            temperature = self.get_temperature()
            self.set_temperature(temperature)


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant
        pass


    def get_temperature(self):
        "Called to get the temperature from the hardware"
        # the temperature input is called 'input03' in the hardware module
        try:
            temperature = hardware.get_input("input03")
        except Exception as e:
            logging.error('Failed to read the temperature')
            return 0.0
        if temperature is None:
            return 0.0
        # round to one digit
        return round(temperature, 1)


    def set_temperature(self, temperature):
        "Called to set the temperature into redis"
        self.rconn.set('rempi01_temperature', temperature)




