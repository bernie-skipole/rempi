################################################################
#
# This module controls the door
#
################################################################


class Door(object):

    def __init__(self, redis):
        "set up the door state"
        # state is False if unknown, True if Known
        self._state = True
        # routine should be provided here to set self._state to True

        # stopped is True if stopped, False if in operation
        self._stopped = False
        # if opening is True, the door is being opened
        self._opening = False
        # if open is True, the door is open
        self._open = False
        # if closed is True, the door is closed
        self._closed = False
        # if closing is True, the door is being closed
        self._closing = False
        # stores actual outputs
        self.output01 = None
        # info stored to redis
        self.redis = redis

    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        pass


    def check_state(self):
        "Checks the hardware for the state of the door"
        return self._state


    def stop(self):
        "Called to stop (disable) the door"
        self._stopped = True


    def start(self):
        "Called to start (enable) the door"
        self._stopped = False


    def start_open(self):
        "Called to start the door opening action"
        self._opening = True
        self._closed = False


    def opened(self):
        "Called to indicate the door is fully opened"
        self._open = True
        self._opening = False


    def start_close(self):
        "Called to start the door closing action"
        self._closing = True
        self._closed = False


    def closed(self):
        "Called to indicate the door is fully closed"
        self._closed = True
        self._closing = False


    def status(self):
        """Provides the door status, one of;
            'UNKNOWN'
            'STOPPED'
            'OPEN'
            'CLOSED'
            'OPENING'
            'CLOSING'
        """
        if not self._state:
            return 'UNKNOWN'
        if self._stopped:
            return 'STOPPED'
        if self._open:
            return 'OPEN'
        if self._opening:
            return 'OPENING'
        if self._closed:
            return 'CLOSED'
        if self._closing:
            return 'CLOSING'
        return 'UNKNOWN'
