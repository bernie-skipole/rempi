################################################################
#
# This module controls the door
#
################################################################

import logging

from . import hardware

class Door(object):

    def __init__(self, redis):
        "set up the door state"
        # info stored to redis
        self.redis = redis
        # Ensure the door position is found on startup
        self.status()


    def __call__(self, msg):
        "Handles the pubsub msg"
        message = msg['data']
        if message == b"status":
            status = self.status()
            if status is None:
                logging.error('Failed to read the door status')
            else:
                logging.info("Door status: " + status)
        # followed by elif's
        # which would handle open, close and stop requests


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # this would typically set the redis 'door_status'
        # and would send an alert such as 
        # self.redis.publish('alert01', 'door status')
        # pimqtt.py would define an alert01_handler - and would read the redis door_status
        # and send it by mqtt
        pass



    def status(self):
        """Provides the door status, one of;
            None - with 'UNKNOWN' set in redis 'door_status'
            'STOPPED'
            'OPEN'
            'CLOSED'
            'OPENING'
            'CLOSING'
        """
        # check hardware, if error, return None, and set UNKNOWN
        # currently no hardware tests done, so door is always 'UNKNOWN'
        self.redis.set('door_status', 'UNKNOWN')
        return
