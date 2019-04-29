################################################################
#
# This module measures temperature
#
################################################################

import logging

from . import hardware


class Temperature(object):

    def __init__(self, redis):
        "set up a Temperature object"
        # state is False until the first get_temperature is called
        self._state = False
        self._temperature = 0.0
        # info will be stored to redis
        self.redis = redis

        # Ensure the hardware values are read on startup
        self.get_temperature()


    def __call__(self, msg):
        "Handles the pubsub msg"
        message = msg['data']
        if message == b"status":
            tmpt = self.get_temperature()
            if tmpt is None:
                logging.error('Failed to read the temperature')


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant
        pass

    def check_state(self):
        "Checks the hardware for the state"
        return self._state


    def get_temperature(self):
        "Called to get the temperature from the hardware, saves it in redis"
        # the temperature input is called 'input03' in the hardware module
        try:
            temperature = hardware.get_input("input03")
        except Exception:
            self._state = False
            self._temperature = 0.0
            return
        # round to one digit
        self._temperature = round(float(temperature), 1)
        self.redis.set('temperature', self._temperature)
        return self._temperature


    def status(self):
        """Provides the temperature status, one of;
            'UNKNOWN' or a number
        """
        if not self._state:
            return 'UNKNOWN'
        return self._temperature
