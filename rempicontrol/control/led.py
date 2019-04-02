################################################################
#
# This module controls the led
#
################################################################


class LED(object):

    def __init__(self, redis):
        "set up an LED object"

        # routine should be provided here to set self._state to True
        self._state = True
        # the actual led output
        self._output = False
        # info stored to redis
        self.redis = redis


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # currently not relevant - but could be a nice test to make a button turn on or off the led
        pass


    def check_state(self):
        "Checks the hardware for the state of the led"
        return self._state


    def get_output(self):
        "Called to get the led state from the hardware, saves it in redis"
        # the led is called 'output01' in the hardware module
        try:
            self._output = hardware.get_boolean_output("output01")
        except Exception:
            self._state = False
            return
        if self._output:
            self.redis.set('led', 'ON')
            return 'ON'
        else:
            self.redis.set('led', 'OFF')
            return 'OFF'


    def set_output(self, output):
        """Called to set the LED, output should be True or ON to turn on, anything else to turn off
           Sets the requested output into Redis"""
        if not output:
            self._output = False
        elif output is True:
            self._output = True
        elif output == "ON":
            self._output = True
        else:
            self._output = False

        if self._output:
            self.redis.set('led', 'ON')
            return 'ON'
        else:
            self.redis.set('led', 'OFF')
            return 'OFF'


    def status(self):
        """Provides the LED status, one of;
            'UNKNOWN'
            'ON'
            'OFF'
        """
        if not self._state:
            return 'UNKNOWN'
        if self._output:
            return 'ON'
        return 'OFF'
