
################################################################
#
# This module controls motors
#
################################################################

import time, threading, logging

from . import hardware



class Motor(object):

    @staticmethod
    def curve(t, duration):
        """Returns a value between 0 and 1.0 for a given t between 0 and duration
           with an eight second acceleration and deceleration
           For t from 0 to 8 increases from 0 up to 1.0
           For t from duration-8 to duration decreases to 0"""
        if t >= duration:
            return 0.0
        half = duration/2.0
        if t<=half:
            # for the first half of duration, increasing speed to a maximum of 1.0 after 8 seconds
            if t>8.0:
                return 1.0
        else:
            # for the second half of duration, decreasing speed to zero when there are 8 seconds left
            if duration-t>8.0:
                return 1.0
            t = 20 - (duration-t)

        # This curve is a fit increasing to 1 (or at least near to 1) with t from 0 to 8,
        # and decreasing with t from 12 to 20
        a = -0.0540937
        b = 0.330319
        c = -0.0383795
        d = 0.00218635
        e = -5.46589e-05
        y = a + b*t + c*t*t + d*t*t*t + e*t*t*t*t
        if y < 0.0:
            return 0.0
        if y > 1.0:
            return 1.0
        return round(y, 3)


    def __init__(self, name, rconn):
        self.name = name
        self.pwm = hardware.makepwm(name+'pwm') # for example 'motor1pwm'
        self.running = time.time()
        self.statuskey = name + 'status'  # for example 'motor1status'
        # info stored to redis
        self.rconn = rconn
        # Initial start with motors stopped
        rconn.set(self.statuskey, 'STOPPED')


    def __call__(self, msg):
        "Handles the pubsub msg"
        motorstatus = self.rconn.get(self.statuskey)
        if motorstatus != b"STOPPED":
            # can only move if the motor is stopped
            return
        try:
            direction = msg['data'].decode("utf-8")
            duration = self.rconn.get(self.name+"duration")
            duration = float(duration)
            speed = self.rconn.get(self.name+"speed")
            speed = int(speed)
        except:
            # input values malformed
            return
        if duration <= 0:
            return
        if speed <= 0:
            return
        if speed > 100.0:
            speed = 100.0
        # record time at which this method was called
        self.running = time.time()
        if direction == "CLOCKWISE":
            self.rconn.set(self.statuskey, 'CLOCKWISE')
            logging.info(self.name + " started, clockwise, duration: %s, speed: %s" % (duration,speed))
            if self.pwm is not None:
                hardware.set_boolean_output(self.name+'direction', True) # for example 'motor1direction'
            run_clockwise = threading.Thread(target=self.runmotor, args=(duration,speed))
            run_clockwise.start()
        if direction == "ANTICLOCKWISE":
            self.rconn.set(self.statuskey, 'ANTICLOCKWISE')
            logging.info(self.name + " started, anticlockwise, duration: %s, speed: %s" % (duration,speed))
            if self.pwm is not None:
                hardware.set_boolean_output(self.name+'direction', False) # for example 'motor1direction'
            run_anticlockwise = threading.Thread(target=self.runmotor, args=(duration,speed))
            run_anticlockwise.start()


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        pass


    def runmotor(self, duration, speed):
        """Runs motor for duration seconds with the given max speed, with 8 seconds acceleration/deceleration"""
        if duration <= 0:
            return
        if speed <= 0:
            return
        if speed > 100.0:
            speed = 100.0
        # start
        now = time.time()
        t = 0
        if self.pwm is not None:
            self.pwm.start(0.0)
        duty_cycle = 0
        # obtain dc which is a value between 0 and speed for the duration
        while t <= duration:
            t = time.time() - now
            dc = self.curve(t, duration) * speed
            # for initial development, print the calculated duty cycle
            print(dc)
            if dc != duty_cycle:
                # only do a change if the duty cycle has changed
                duty_cycle = dc
                if self.pwm is not None:
                    # Note: the particular H bridge used does not accept a
                    # duty cycle of 100, therefore this line reduces speed by 0.95
                    out = round(duty_cycle * 0.95,2) 
                    self.pwm.ChangeDutyCycle(out)
            time.sleep(0.2)
        if self.pwm is not None:
            self.pwm.stop()
        self.rconn.set(self.statuskey, 'STOPPED')

