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
        # curves is a dictionary of timestamp:curve
        self.curves = {}
        # curvetimes is a sorted list of the curve timestamps
        self.curvetimes = []
        self.tracking = False
        self.alt = 0.0           # initial conditions, could be changed to a 'parking' state
        self.az = 0.0
        self.target_name = ''
        self.ra = ''
        self.dec = ''

        # the telescope motors
        self.motor1 = motors.Motor('motor1',rconn)
        self.motor2 = motors.Motor('motor2',rconn)


    @property
    def target_name(self):
        "Returns target name or empty string if name not set"
        target_name = self.rconn.get("rempi01_target_name")
        if target_name is None:
            return ''
        return target_name.decode("utf-8")

    @target_name.setter
    def target_name(self, target_name):
        self.rconn.set("rempi01_target_name", target_name)

    @target_name.deleter
    def target_name(self):
        self.rconn.delete("rempi01_target_name")

    @property
    def ra(self):
        "Returns target ra as a string or empty string if ra not set"
        target_ra = self.rconn.get("rempi01_target_ra")
        if target_ra is None:
            return ''
        return target_ra.decode("utf-8")

    @ra.setter
    def ra(self, target_ra):
        self.rconn.set("rempi01_target_ra", target_ra)

    @ra.deleter
    def ra(self):
        self.rconn.delete("rempi01_target_ra")

    @property
    def dec(self):
        "Returns target dec as a string or empty string if dec not set"
        target_dec = self.rconn.get("rempi01_target_dec")
        if target_dec is None:
            return ''
        return target_dec.decode("utf-8")

    @dec.setter
    def dec(self, target_dec):
        self.rconn.set("rempi01_target_dec", target_dec)

    @dec.deleter
    def dec(self):
        self.rconn.delete("rempi01_target_dec")


    def goto(self, msg):
        "Handles the pubsub msg - receives a target set of alt,az values and creates the curves"
        # Set tracking False, to stop previous tracking
        self.tracking = False
        # positions consists of target_name, ra, dec and 20 sets of timestamp,alt,az which is a string and 62 floats,
        # these alt and az values are for nineteen 30 second intervals (9.5 minutes), these are updated from the server every 4 minutes
        positions = unpack("10s"+"d"*62, msg['data'])
        self.target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        self.ra = positions[1]
        self.dec = positions[2]
        logging.info('Goto received RA %s DEC %s' % (positions[1], positions[2]))
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        # create a dictionary of curves for interpolation
        self.curves = self.createcurves(time_altaz)
        self.curvetimes = list(self.curves.keys())
        self.curvetimes.sort()
        # set the received positions into the redis tracking key
        self.rconn.set('rempi01_track', msg['data'])
        # set tracking True to let telescope know to use these curves
        self.tracking = True
 

    def createcurves(self, time_altaz):
        """create four sets of curves, each with a timestamp covering the 20 sets of timestamps
           time_altaz is a dictionary of timestamps against alt,az positions
           {timestamp:(alt,az), timestamp:(alt,az),....}
           """
        timelist = list(time_altaz.keys())
        timelist.sort()

        curves = {}
      
        # timestamp[0]                   0 seconds   -------
        #                  30 seconds
        # timestamp[1]                  30 seconds
        #                  30 seconds
        # timestamp[2]                  60 seconds    1st curve
        #                  30 seconds
        # timestamp[3]                  90 seconds
        #                  30 seconds
        # timestamp[4]                  120 seconds          ======
        #                  30 seconds
        # timestamp[5]                  150 seconds   ------
        #                  30 seconds
        # timestamp[6]                  180 seconds 
        #                  30 seconds                        2nd curve
        # timestamp[7]                  210 seconds
        #                  30 seconds
        # timestamp[8]                  240 seconds                 #########
        #                  30 seconds
        # timestamp[9]                  370 seconds          =======
        #                  30 seconds
        # timestamp[10]                 300 seconds 
        #                  30 seconds
        # timestamp[11]                 330 seconds                  3rd curve
        #                  30 seconds
        # timestamp[12]                 360 seconds 
        #                  30 seconds
        # timestamp[13]                 390 seconds                            ++++++++ 
        #                  30 seconds
        # timestamp[14]                 420 seconds                   ########
        #                  30 seconds
        # timestamp[15]                 450 seconds 
        #                  30 seconds
        # timestamp[16]                 480 seconds                             4th curve
        #                  30 seconds
        # timestamp[17]                 510 seconds
        #                  30 seconds
        # timestamp[18]                 540 seconds
        #                  30 seconds
        # timestamp[19]                 570 seconds                              +++++++




        # first set of six timestamps  (5 intervals = 2.5 minutes)
        # dictionary records the curve coefficients against the first timestamp
        curves[timelist[0]] = self.curve_maker(timelist[:6], time_altaz)

        # next curve also covers six timestamps  (5 intervals = 2.5 minutes)
        # dictionary records the curve coefficients from timelist[4] - an overlap of 30 sec with the previous curve
        curves[timelist[4]] = self.curve_maker(timelist[4:10], time_altaz)

        # third curve covers seven timestamps  (6 intervals = 3 minutes)
        # dictionary records the curve coefficients from timelist[8] - an overlap of 30 sec with the previous curve
        curves[timelist[8]] = self.curve_maker(timelist[8:15], time_altaz)

        # last curve covers seven timestamps  (6 intervals = 3 minutes)
        # dictionary records the curve coefficients from timelist 13 to the end, an overlap of 30 sec with the previous curve
        curves[timelist[13]] = self.curve_maker(timelist[13:], time_altaz)

        # note the curve time coverage is less than total curve time, as the curves overlap each other

        # so the curves expire at 570 seconds, 9.5 minutes, or 3 minutes after the start of the last curve

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
        # disable tracking
        self.tracking = False
        self.alt, self.az = unpack("dd", msg['data'])
        logging.info('AltAz received ALT %s AZ %s' % (self.alt, self.az))
        self.target_name = ''
        self.ra = ''
        self.dec = ''


    def target_alt_az(self, timestamp, secondcall=False):
        """Returns the wanted target alt, az at the given timestamp
           secondcall is to stop a loop occuring with the self.loadpositions function"""
        if not self.tracking:
            # no tracking, return the static alt, az set by the altaz method (or by curve expirey)
            return self.alt, self.az
        # get the right interpolation curve for the given timestamp
        if timestamp > self.curvetimes[3]+180:
            # assume after three minutes, the curves has expired, another goto is required to create new curves
            self.target_name = ''
            self.ra = ''
            self.dec = ''
            # no tracking data has been received, so assume final position measured from curve is the final altaz point.
            popt_alt, popt_az = self.curves[self.curvetimes[3]]
            logging.error('Tracking stopped - no tracking data being received')
            self.tracking = False
            # timestamp is set to be end of last curve
            self.alt, self.az = self.alt_az_from_curve(self.curvetimes[3]+180, popt_alt, popt_az)
            return self.alt, self.az
        elif timestamp >= self.curvetimes[3]:
            # three minutes before curves expire, check if more positions have been given, if so load them
            if (not secondcall) and self.loadpositions():
                # self.curves has been updated, so call this function again
                # but this time with secondcall True, so multiple calls to loadpositions do not occur
                return self.target_alt_az(timestamp, True)
            # curves have not been updates, so continue with the existing curves
            popt_alt, popt_az = self.curves[self.curvetimes[3]]
        elif timestamp >= self.curvetimes[2]:
            popt_alt, popt_az = self.curves[self.curvetimes[2]]
        elif timestamp >= self.curvetimes[1]:
            popt_alt, popt_az = self.curves[self.curvetimes[1]]
        else:
           popt_alt, popt_az = self.curves[self.curvetimes[0]]
        # now get alt, az from the curve
        return self.alt_az_from_curve(timestamp, popt_alt, popt_az)
  

    def alt_az_from_curve(self, timestamp, popt_alt, popt_az):
        """Return alt, az from the _qcurve given timestamp and popt_alt, popt_az"""
        alt = _qcurve(timestamp, *popt_alt)
        if alt > 90.0:
            alt = 90.0
        if alt < -90.0:
            alt = -90.0
        az =  _qcurve(timestamp, *popt_az)
        if az > 360.0:
            az = az - 360.0
        if az < 0:
            az = 360.0 + az
        return alt, az


    def tracking_speed(self, timestamp):
        "Returns alt_speed, az_speed which are the angular speeds the telescope should be moving at in degrees per second at the given timestamp"
        # gets positions at timestamp - 5 and timestamp +5 and takes difference / 10.0 as the speeds
        if not self.tracking:
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
        if not self.tracking:
            # only bother with tracking data if self.tracking is True
            # that is, if a goto has been received
            return False
        payload = self.rconn.get('rempi01_track')
        if not payload:
            return False
        positions = unpack("10s"+"d"*62, payload)
        self.target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        self.ra = positions[1]
        self.dec = positions[2]
        # delete the payload to avoid multiple reads of it
        self.rconn.delete('rempi01_track')
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        self.curves = self.createcurves(time_altaz)
        self.curvetimes = list(self.curves.keys())
        self.curvetimes.sort()
        logging.info('Reading tracking data for RA %s DEC %s' % (positions[1], positions[2]))
        return True


    def record_target(self, timestamp=None):
        "Records the target information into redis for the current time, returns wanted target (alt, az, alt_speed, az_speed)"
        if timestamp is None:
            targettime = datetime.utcnow()
            timestamp = targettime.replace(tzinfo=timezone.utc).timestamp()
        elif isinstance(timestamp, datetime):
            timestamp = timestamp.replace(tzinfo=timezone.utc).timestamp()
        
        wanted_position = self.target_alt_az(timestamp)
        wanted_speed = self.tracking_speed(timestamp)

        # these values are recorded for status, and web displays
        self.rconn.set("rempi01_target_alt", "{:1.5f}".format(wanted_position[0]))
        self.rconn.set("rempi01_target_az", "{:1.5f}".format(wanted_position[1]))
        self.rconn.set("rempi01_target_alt_speed", "{:1.5f}".format(wanted_speed[0]))
        self.rconn.set("rempi01_target_az_speed", "{:1.5f}".format(wanted_speed[1]))
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

        # assume initial speed is zero
        speed_alt = 0
        speed_az = 0

        # self.alt, self.az are values for a stopped scope, set by altaz method, or when tracking information
        # has stopped. Assume they can be used as the initial value, should eventually be taken by hardware measurement

        alt = self.alt
        az = self.az

        # alt, az is the current position at the start of the time interval
    
        # target_alt, target_az is the expected target position at the end of the time interval

        # target_speed_* is the target speed at the end
        # speed_* is speed over the previous time interval

        # hopefully, alt and az will become equal to target_alt, target_az at the end of the time interval


        while True:

            # record alt and az prior to movement over the time interval
            last_alt = alt
            last_az = az


            # self.record_target returns target position and speed at TIME_INTERVAL in the future
            # and also records these target positions to redis

            future_time = datetime.utcnow()+timedelta(seconds=self.TIME_INTERVAL)
            target_alt, target_az, target_speed_alt, target_speed_az = self.record_target(future_time)

            # get speed for the next time interval, where targets are taken for TIME_INTERVAL time in the future
            speed_alt = self.get_speed(alt, speed_alt, target_alt, target_speed_alt)
            speed_az = self.get_speed(az, speed_az, target_az, target_speed_az)

            ######## call motor control with speed_alt, speed_az  ##########

            sleep(self.TIME_INTERVAL)

            # get new position after the time interval,
            # this will, in due course, be measured from scope sensors
            alt = alt + speed_alt * self.TIME_INTERVAL
            az = az + speed_az * self.TIME_INTERVAL

            while az >= 360.0:
                az = az - 360.0
            while az < 0.0:
                az = az + 360.0

            if alt > 90.0:
                alt = 90.0
            if alt < -90.0:
                alt = -90.0

            # set values into redis for reading by the web service, and also
            # pack timestamp,alt,az into a structure of three floats, for sending
            # to remote server 
            self.rconn.set("rempi01_current_time", future_time.strftime("%H:%M:%S.%f"))
            self.rconn.set("rempi01_current_alt", "{:1.5f}".format(alt))
            self.rconn.set("rempi01_current_az", "{:1.5f}".format(az))
            timestamp = future_time.replace(tzinfo=timezone.utc).timestamp()
            self.rconn.set("telescope_position", pack("ddd", timestamp, alt, az))

            # current positions should now be equal to the previous target positions for the end of the time interval
            error_alt = target_alt - alt
            error_az = target_az - az
            # print(error_alt, error_az)


    




        



 

