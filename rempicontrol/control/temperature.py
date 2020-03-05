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
        self.get_temperature()


    def __call__(self, msg):
        "Handles the pubsub msg"
        message = msg['data']
        if message == b"status":
            # sets hardware temperature into redis
            temperature = self.get_temperature()
            if temperature is None:
                logging.error('Failed to read the temperature')


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant
        pass


    def get_temperature(self):
        "Called to get the temperature from the hardware, saves it in redis"
        # the temperature input is called 'input03' in the hardware module
        try:
            temperature = hardware.get_input("input03")
        except RuntimeError as e:
            self.rconn.set('rempi01_temperature', 0.0)
            logging.error(str(e))
            return
        except Exception:
            self.rconn.set('rempi01_temperature', 0.0)
            return
        if temperature is None:
            self.rconn.set('rempi01_temperature', 0.0)
            return
        # round to one digit
        temperature = round(float(temperature), 1)
        self.rconn.set('rempi01_temperature', temperature)
        return temperature



