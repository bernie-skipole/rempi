################################################################
#
# This module contains classes to hold the state
#
################################################################


from ... import FailPage, GoTo, ValidateError, ServerError


class Door(object):

    def __init__(self):
        "set up the door state"
        # state is False if unknown, True if Known
        self._state = False
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


    def set_state(self, door_open, door_closed, door_opening, door_closing):
        "Sets the door state, should be followed by a call to start"
        self._opening = door_opening
        self._open = door_open
        self._closed = door_closed
        self._closing = door_closing
        self._stop = True
        self._state = True


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
