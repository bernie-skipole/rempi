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


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        # this would typically set the redis 'door_status'
        # and would send an alert such as 
        # self.redis.publish('alert01', 'door status')
        # pimqtt.py would define an alert01_handler - and would read the redis door_status
        # and send it by mqtt
        pass


    def get_door(self):
        """Provides the door status, one of;
            None - with 'UNKNOWN' set in redis 'door_status'
            'STOPPED'
            'OPEN'
            'CLOSED'
            'OPENING'
            'CLOSING'
        """
        # should check hardware, if error, return None, and set UNKNOWN
        # self.redis.set('door_status', 'UNKNOWN')
        # otherwise set the appropriate status

        # in this case however, as hardware not done yet, instead of hardware test
        # just read redis
        status = redis.get('door_status'):
        if status is None:
            return 'UNKNOWN'
        elif status == b"OPEN":
            return "OPEN"
        elif status == b"CLOSE":
            return "CLOSE"


    def set_door(self, action):
        """Called to set the door, action should be OPEN or CLOSE
           Sets the requested output into Redis"""
        if action == 'OPEN':
            # set door in hardware
            self.redis.set('door_status', 'OPEN')
            logging.info('Door set to open')
            self.redis.publish('alert01', 'door status')
            return 'OPEN'
        else:
            # set door in hardware
            self.redis.set('door_status', 'CLOSE')
            logging.info('Door set to close')
            self.redis.publish('alert01', 'door status')
            return 'CLOSE'

