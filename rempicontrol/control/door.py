################################################################
#
# This module controls the door
#
################################################################

import logging

from . import hardware

class Door(object):

    def __init__(self, rconn):
        "set up the door state"
        # info stored to rconn
        self.rconn = rconn
        # Ensure the door position is found on startup
        self.get_door()


    def __call__(self, msg):
        "Handles the pubsub msg"
        message = msg['data']
        if message == b"status":
            status = self.get_door()
            if status is None:
                logging.error('Failed to read the door status')
            else:
                logging.info("Door status: " + status)
        elif message == b"OPEN":
            self.set_door("OPEN")
        elif message == b"CLOSE":
            self.set_door("CLOSE")
        elif message == b"HALT":
            self.set_door("HALT")


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # this would typically set the rconn 'door_status'
        # and would send an alert such as 
        # self.rconn.publish('alert01', 'door status')
        # pimqtt.py would define an alert01_handler - and would read the rconn door_status
        # and send it by mqtt
        pass


    def get_door(self):
        """Provides the door status, one of;
            None - with 'UNKNOWN' set in rconn 'door_status'
            'STOPPED'   set if HALT received or other hardware interrupt
            'OPEN'
            'CLOSED'
            'OPENING'
            'CLOSING'
        """
        # should check hardware, if error, return None, and set UNKNOWN
        # self.rconn.set('rempi01_door_status', 'UNKNOWN')
        # otherwise set the appropriate status

        # in this case however, as hardware not done yet, instead of hardware test
        # just read rconn
        status = self.rconn.get('rempi01_door_status')
        if status is None:
            return 'UNKNOWN'
        elif status == b"OPEN":
            return "OPEN"
        elif status == b"OPENING":
            return "OPENING"
        elif status == b"CLOSED":
            return "CLOSED"
        elif status == b"CLOSING":
            return "CLOSING"
        elif status == b"STOPPED":
            return "STOPPED"
        return "UNKNOWN"


    def set_door(self, action):
        """Called to set the door, action should be OPEN, CLOSE or HALT
           Sets the requested output into redis"""
        if action == 'OPEN':
            # set open door in hardware
            self.rconn.set('rempi01_door_status', 'OPENING')
            logging.info('Door set to open')
            self.rconn.publish('alert01', 'door status')
            return 'OPEN'
        elif action == 'CLOSE':
            # set close door in hardware
            self.rconn.set('rempi01_door_status', 'CLOSING')
            logging.info('Door set to close')
            self.rconn.publish('alert01', 'door status')
            return 'CLOSE'
        else:
            # set door stopped in hardware
            self.rconn.set('rempi01_door_status', 'STOPPED')
            logging.info('Door halted')
            self.rconn.publish('alert01', 'door status')
            return 'STOPPED'



