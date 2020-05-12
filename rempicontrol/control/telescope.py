################################################################
#
# Defines a Telescope object to accept instructions to move
# the telescope, and also worker function, which is a blocking function
# which does the actual work
#
################################################################

import logging

from struct import pack, unpack

from datetime import datetime, timezone, timedelta

from time import sleep

from scipy.optimize import curve_fit

from . import motors

# telescope has states:

# slewing - heading fast towards a given alt, az

# tracking - following a changing altaz slowly

# stopped - at a given alt az


# function _qcurve and its parameters are used to 'fit' between a set of alt az points provided
# by the main web server, this is then used to interpolate at times between the points

def _qcurve(x, a, b, c):
    "This function models the data, x is an input, and the parameters a,b,c are required to fit the data"
    return a*x*x + b*x + c



class Telescope(object):

    MAX_SPEED = 4  # degrees per second

    MAX_ACCELERATION = 1.5 # degrees per second squared

    TIME_INTERVAL = 0.5 # seconds

    DECELERATION_DISTANCE = 10.0 # degrees


    def __init__(self, rconn, state):
        "The Telescope instrument"
        self.state = state
        # info stored to redis
        self.rconn = rconn
        self.curves = {}
        self.alt = 0.0           # initial conditions, could be changed to a 'parking' state
        self.az = 0.0
        self.target_name = ''
        self.ra = None
        self.dec = None
        self.rconn.delete('rempi01_track')
        self.rconn.delete("rempi01_target_name")
        self.rconn.delete("rempi01_target_ra")
        self.rconn.delete("rempi01_target_dec")

        targettime = datetime.utcnow()
        self.timestamp = int(targettime.replace(tzinfo=timezone.utc).timestamp())
        # this value is subtracted from subsequent timestamps to reduce the size of the numbers

        # the telescope motors
        self.motor1 = motors.Motor('motor1',rconn)
        self.motor2 = motors.Motor('motor2',rconn)


    def goto(self, msg):
        "Handles the pubsub msg - receives a target set of alt,az values"
        # positions consists of target_name, ra, dec and 20 sets of timestamp,alt,az which is a string and 62 floats,
        # these alt and az values are for ten minutes (twenty half minutes), every 30 seconds
        positions = unpack("10s"+"d"*62, msg['data'])
        self.target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        self.ra = positions[1]
        self.dec = positions[2]
        logging.info('Goto received RA %s DEC %s' % (self.ra, self.dec))
        # goto just received, so no tracking yet
        self.rconn.delete('rempi01_track')
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # timestamp has self.timestamp subtracted to reduce number size
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp - self.timestamp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        # create a dictionary of curves for interpolation
        self.curves = self.createcurves(time_altaz)
        self.alt = None
        self.az = None
        self.last_alt = None
        self.last_az = None
 

    def createcurves(self, time_altaz):
        "create four sets of curves, each with a timestamp covering the 20 sets of timestamps"
        timelist = list(time_altaz.keys())
        timelist.sort()

        curves = {}
      
        # first five timestamps
        # dictionary records the curve coefficients against the first timestamp
        curves[timelist[0]] = self.curve_maker(timelist[:5], time_altaz)

        # next five timestamps
        # dictionary records the curve coefficients
        curves[timelist[5]] = self.curve_maker(timelist[5:10], time_altaz)

        # next five timestamps
        # dictionary records the curve coefficients
        curves[timelist[10]] = self.curve_maker(timelist[10:15], time_altaz)

        # last five timestamps
        # dictionary records the curve coefficients
        curves[timelist[15]] = self.curve_maker(timelist[15:], time_altaz)

        # so this last covers from timelist[15] to a further five timesamples (to timelist 20)
        # each sample is 30 seconds, so this curve expires after a further 5*30 seconds - one minute

        return curves



    def curve_maker(self, timeseries, time_altaz):
        "Returns quadratic coefficients for curves fitting alt and az values over the given timeseries"
        # altitudes for the timestamps in timeseries
        altseries = [ time_altaz[tm][0] for tm in timeseries ]
        popt_alt, pcov_alt = curve_fit(_qcurve, timeseries, altseries)  # curve_fit from scipy.optimize

        # popt_alt is a, b, c parameters for quadratic curve which fits altseries

        # azimuths for the timestamps in timeseries
        azseries = [ time_altaz[tm][1] for tm in timeseries ]

        # it is possible for azimuths to start at say 356 and then go past 360 to just above zero, causing a discontinuity
        # for the short series of points here, the continuity may occur if any point is close to 360, ie greater than 270
        discontinuity = False
        for az in azseries:
            if az > 270.0:
                discontinuity = True
                break
        if discontinuity:
            # add 360 for points which are less than 90
            new_azseries = [ az if az > 90 else az+360 for az in azseries ]
            azseries = new_azseries
       
        popt_az, pcov_az = curve_fit(_qcurve, timeseries, azseries)
        # popt_az is a, b, c parameters for quadratic curve which fits azseries

        return popt_alt, popt_az
      

    def altaz(self, msg):
        "Handles the pubsub msg to move to a particular alt, az point, but then does not track"
        self.alt, self.az = unpack("dd", msg['data'])
        logging.info('AltAz received ALT %s AZ %s' % (self.alt, self.az))
        # no tracking
        self.curves = {}
        self.rconn.delete('rempi01_track')
        self.target_name = ''
        self.ra = None
        self.dec = None
        self.rconn.delete("rempi01_target_name")
        self.rconn.delete("rempi01_target_ra")
        self.rconn.delete("rempi01_target_dec")
        self.last_alt = self.alt
        self.last_az = self.az


    def target_alt_az(self, timestamp):
        "Returns the wanted target alt, az at the given timestamp"
        reduced_time = timestamp - self.timestamp
        if not self.curves:
            # no tracking
            return self.alt, self.az
        # get the right interpolation curve for the given timestamp
        curvetimes = list(self.curves.keys())
        curvetimes.sort()
        if reduced_time > curvetimes[3]+60:
            # curves have expired, another goto is required to create new curves
            self.curves = {}
            self.rconn.delete('rempi01_track')
            self.target_name = ''
            self.ra = None
            self.dec = None
            self.rconn.delete("rempi01_target_name")
            self.rconn.delete("rempi01_target_ra")
            self.rconn.delete("rempi01_target_dec")
            self.alt = self.last_alt
            self.az = self.last_az
            logging.error('Tracking stopped - no tracking data being received')
            return self.alt, self.az
        elif reduced_time >= curvetimes[3]:
            # one minute before curves expire, check if more positions have been given, if so load them
            if self.loadpositions():
                # self.curves has been updated, so call this function again
                return self.target_alt_az(timestamp)
            popt_alt, popt_az = self.curves[curvetimes[3]]
        elif reduced_time >= curvetimes[2]:
            popt_alt, popt_az = self.curves[curvetimes[2]]
        elif reduced_time >= curvetimes[1]:
            popt_alt, popt_az = self.curves[curvetimes[1]]
        else:
           popt_alt, popt_az = self.curves[curvetimes[0]]
        # now get alt, az from the curve
        alt = _qcurve(reduced_time, *popt_alt)
        if alt > 90.0:
            alt = 90.0
        if alt < -90.0:
            alt = -90.0
        az =  _qcurve(reduced_time, *popt_az)
        if az > 360.0:
            az = az - 360.0
        if az < 0:
            az = 360.0 + az
        self.last_alt = alt
        self.last_az = az
        return alt, az


    def tracking_speed(self, timestamp):
        "Returns alt_speed, az_speed which are the angular speeds the telescope should be moving at in degrees per second at the given timestamp"
        # gets positions at timestamp - 5 and timestamp +5 and takes difference / 10.0 as the speeds
        if not self.curves:
            return (0.0, 0.0)
        pos1 = self.target_alt_az(timestamp - 5.0)
        pos2 = self.target_alt_az(timestamp + 5.0)
        alt_speed = (pos2[0] - pos1[0])/10.0
        az1 = pos1[1]
        az2 = pos2[1]
        if az1>270 and az2<90:
            az_speed = (360 + az2 - az1)/10.0
        elif az2>270 and az1<90:
            az_speed = (az2-360-az1)/10.0
        else:
            az_speed = (az2-az1)/10.0
        return alt_speed, az_speed


    def loadpositions(self):
        "Checks if new positions have been received, since lasttime, if so return True, if not, False"
        payload = self.rconn.get('rempi01_track')
        if not payload:
            return False
        self.rconn.delete('rempi01_track')
        positions = unpack("10s"+"d"*62, payload)
        self.target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        self.ra = positions[1]
        self.dec = positions[2]
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # timestamp has self.timestamp subtracted to reduce number size
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp - self.timestamp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        self.curves = self.createcurves(time_altaz)
        logging.info('Tracking data received for RA %s DEC %s' % (self.ra, self.dec))
        return True


    def record_target(self, timestamp=None):
        "Records the target information into redis for the current time, returns wanted target (alt, az, alt_speed, az_speed)"
        if timestamp is None:
            targettime = datetime.utcnow()
            timestamp = targettime.replace(tzinfo=timezone.utc).timestamp()

        if isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=timezone.utc).timestamp()
        
        wanted_position = self.target_alt_az(timestamp)
        wanted_speed = self.tracking_speed(timestamp)

        # these values are recorded for status, and web displays
        self.rconn.set("rempi01_target_alt", "{:1.5f}".format(wanted_position[0]))
        self.rconn.set("rempi01_target_az", "{:1.5f}".format(wanted_position[1]))
        self.rconn.set("rempi01_target_alt_speed", "{:1.5f}".format(wanted_speed[0]))
        self.rconn.set("rempi01_target_az_speed", "{:1.5f}".format(wanted_speed[1]))

        if self.target_name:
            self.rconn.set("rempi01_target_name", self.target_name)
        else:
            self.rconn.delete("rempi01_target_name")

        if self.ra is None:
            self.rconn.delete("rempi01_target_ra")
        else:
            self.rconn.set("rempi01_target_ra", self.ra)

        if self.dec is None:
            self.rconn.delete("rempi01_target_dec")
        else:
            self.rconn.set("rempi01_target_dec", self.dec)

        return wanted_position + wanted_speed


    def pin_changed(self,input_name):
        "Check if input_name is relevant, and if so, do appropriate actions"
        pass


    def get_speed(self, current_pos, speed, target_pos, target_speed):
        """Return speed for the next time interval - used to slew and track

        target_pos is the expected target position at the end of the time interval
        current_pos is position at the start
        target_speed is the target speed at the end
        speed is speed over the previous time interval"""

        if target_pos<60.0 and current_pos>300.0:
            target_pos = target_pos + 360

        if current_pos<60.0 and target_pos>300.0:
            current_pos = current_pos + 360

        # delta_distance is the distance to move in this time interval
        # the returned speed will be delta_distance/TIME_INTERVAL

        # get max delta distance
        max_delta_distance = self.MAX_SPEED * self.TIME_INTERVAL

        # previous interval distance
        previous_distance = speed * self.TIME_INTERVAL

        # distance to the target, from the beginning of the interval.
        # as target_pos is at the end of the interval, we need
        # target_pos - target_speed*TIME_INTERVAL
        # to be target position at the start of the interval
        # the required distance is the difference between this and current_pos

        distance = target_pos - target_speed*self.TIME_INTERVAL - current_pos

        # the value 'DECELERATION_DISTANCE' is the distance over which deceleration occurs
        # it may have to be 'tuned'

        # if distance to move is greater than this deceleration distance,
        # make distance to move the max_delta_distance
        # otherwise make distance to move proportional to 'distance'

        if distance > self.DECELERATION_DISTANCE:
             delta_distance = max_delta_distance
        elif distance < -1*self.DECELERATION_DISTANCE:
            delta_distance =  -1 * max_delta_distance
        else:
            # as distance goes to zero, so does delta_distance
            delta_distance = max_delta_distance * distance / self.DECELERATION_DISTANCE
            # as the target is moving, add the target movement to delta_distance
            delta_distance +=  target_speed*self.TIME_INTERVAL
            if abs(delta_distance) > max_delta_distance:
                if delta_distance > 0:
                    delta_distance = max_delta_distance
                else:
                    delta_distance = -1 * max_delta_distance

        # so delta_distance worked out, but does the speed change
        # break the maximum acceleration

        while True:
            newspeed = delta_distance/self.TIME_INTERVAL
            acceleration = (newspeed - speed)/self.TIME_INTERVAL
            if abs(acceleration) < self.MAX_ACCELERATION:
                # all ok
                break
            # acceleration is too great, make delta_distance closer to previous_distance
            # which reduces acceleration, and test again
            delta_distance = (5*delta_distance + previous_distance)/6.0

        return newspeed


    def __call__(self): 
        "This actually runs the telescope, this is a blocking call, so run in a thread"
        current_alt = 0
        speed_alt = 0
        current_az = 0
        speed_az = 0

        # target_* is the expected target position at the end of the time interval
        # current_* is position at the start
        # target_speed_* is the target speed at the end
        # speed_* is speed over the previous time interval


        while True:

            # returns wanted target (alt, az, alt_speed, az_speed) at TIME_INTERVAL in the future
            # and also records these target positions to redis

            future_time = datetime.utcnow()+timedelta(seconds=self.TIME_INTERVAL)

            target_alt, target_az, target_speed_alt, target_speed_az = self.record_target(future_time)

            # get speed for the next time interval, where target_*, target_speed_* are taken for TIME_INTERVAL time in the future
            speed_alt = self.get_speed(current_alt, speed_alt, target_alt, target_speed_alt)
            speed_az = self.get_speed(current_az, speed_az, target_az, target_speed_az)

            sleep(self.TIME_INTERVAL)

            # get new position after the time interval,
            # this will, in due course, be measured from scope sensors
            current_alt = current_alt + speed_alt * self.TIME_INTERVAL
            current_az = current_az + speed_az * self.TIME_INTERVAL

            while current_az >= 360.0:
                current_az = current_az - 360.0
            while current_az < 0.0:
                current_az = current_az + 360.0

            if current_alt > 90.0:
                current_alt = 90.0
            if current_alt < -90.0:
                current_alt = -90.0

            # set values into redis for reading by the web service, and also
            # pack timestamp,alt,az into a structure of three floats, for sending
            # to remote server 
            self.rconn.set("rempi01_current_time", future_time.strftime("%H:%M:%S.%f"))
            self.rconn.set("rempi01_current_alt", "{:1.5f}".format(current_alt))
            self.rconn.set("rempi01_current_az", "{:1.5f}".format(current_az))
            timestamp = future_time.replace(tzinfo=timezone.utc).timestamp()
            self.rconn.set("telescope_position", pack("ddd", timestamp, current_alt, current_az))

            # current positions should now be equal to the previous target positions for the end of the time interval
            error_alt = target_alt - current_alt
            error_az = target_az - current_az

            # print(error_alt, error_az)


    




        



 

