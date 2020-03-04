################################################################
#
# Accepts alt az values to move the telescope
#
################################################################

import logging

from struct import pack, unpack

from datetime import datetime, timezone, timedelta

from time import sleep

from scipy.optimize import curve_fit

# telescope has states:

# slewing - heading fast towards a given alt, az

# tracking - following a changing altaz slowly

# stopped - at a given alt az


def _qcurve(x, a, b, c):
    "This function models the data, x is an input, and the parameters a,b,c are required to fit the data"
    return a*x*x + b*x + c



class Telescope(object):

    def __init__(self, rconn):
        "set up the Telescope state"
        # info stored to redis
        self.rconn = rconn
        self.curves = {}
        self.alt = 0.0           # initial conditions, could be changed to a 'parking' state
        self.az = 0.0

        targettime = datetime.utcnow()
        self.timestamp = int(targettime.replace(tzinfo=timezone.utc).timestamp())
        # this value is subtracted from subsequent timestamps to reduce the size of the numbers



    def goto(self, msg):
        "Handles the pubsub msg"
        # positions consists of target_name, ra, dec and 20 sets of timestamp,alt,az which is a string and 62 floats,
        positions = unpack("10s"+"d"*62, msg['data'])
        target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        ra = positions[1]
        dec = positions[2]
        # goto just received, so no tracking yet
        self.rconn.delete('track')
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp - self.timestamp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        self.curves = self.createcurves(time_altaz)
        self.alt = None
        self.az = None
 

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

        return curves



    def curve_maker(self, timeseries, time_altaz):
        "Returns quadratic coefficients for curves fitting alt and az values over the given timeseries"
        # altitudes for the timestamps in timeseries
        altseries = [ time_altaz[tm][0] for tm in timeseries ]
        popt_alt, pcov_alt = curve_fit(_qcurve, timeseries, altseries)

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
        "Handles the pubsub msg"
        self.alt, self.az = unpack("dd", msg['data'])
        # no tracking
        self.rconn.delete('track')


    def target_alt_az(self, at_time):
        "Returns the wanted target alt, az at the given timestamp at_time"
        reduced_time = at_time - self.timestamp
        if not self.curves:
            return self.alt, self.az
        curvetimes = list(self.curves.keys())
        curvetimes.sort()
        if reduced_time >= curvetimes[3]:
            # check if more positions have been given, if so load them
            if loadpositions():
                # self.curves has been updated, so call this function again
                return self.target_alt_az(at_time)
            popt_alt, popt_az = self.curves[curvetimes[3]]
        elif reduced_time >= curvetimes[2]:
            popt_alt, popt_az = self.curves[curvetimes[2]]
        elif reduced_time >= curvetimes[1]:
            popt_alt, popt_az = self.curves[curvetimes[1]]
        else:
           popt_alt, popt_az = self.curves[curvetimes[0]]

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
        return alt, az


    def tracking_speed(self, at_time):
        "Returns alt_speed, az_speed which are the angular speeds the telescope should be moving at in degrees per second at the given timestamp"
        # gets positions at at_time - 5 and at_time +5 and takes difference / 10.0 as the speeds
        if not self.curves:
            return (0.0, 0.0)
        pos1 = self.target_alt_az(at_time - 5.0)
        pos2 = self.target_alt_az(at_time + 5.0)
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


    def loadpositions():
        "Checks if new positions have been received, since lasttime, if so return True, if not, False"
        payload = self.rconn.get('track')
        if not payload:
            return False
        self.rconn.delete('track')
        positions = unpack("10s"+"d"*62, payload)
        target_name = positions[0].rstrip(b'\x00').decode("utf-8")
        ra = positions[1]
        dec = positions[2]
        # create a dictionary of {timestamp:(alt,az), timestamp:(alt,az),....}
        # note positions[3:] is used as the first three elements are the name, ra and dec
        time_altaz = { tstmp - self.timestamp : (altdeg, azdeg) for tstmp, altdeg, azdeg in zip(*[iter(positions[3:])]*3) }
        self.curves = self.createcurves(time_altaz)
        return True



def worker(state):
    "This actually runs the telescope"
    telescope = state['telescope']


    targettime = datetime.utcnow()
    timestamp = targettime.replace(tzinfo=timezone.utc).timestamp()
    wanted_position = telescope.target_alt_az(timestamp)
    wanted_speed = telescope.tracking_speed(timestamp)

    print("\nTime: {:1.3f}".format(timestamp))
    print("Initial wanted Telescope position ALT: {:1.5f}\xb0 AZ: {:1.5f}\xb0".format(*wanted_position))
    print("Initial wanted speed  ALT: {:1.5f}\xb0 per second, AZ: {:1.5f}\xb0 per second".format(*wanted_speed))
    while True:
        # wait ten seconds
        sleep(10)
        # check if scope wanted position and speed has changed

        targettime = datetime.utcnow()
        timestamp = targettime.replace(tzinfo=timezone.utc).timestamp()
        wanted_position = telescope.target_alt_az(timestamp)
        wanted_speed = telescope.tracking_speed(timestamp)

        print("\nTime: {:1.3f}".format(timestamp))
        print("Telescope wanted position ALT: {:1.5f}\xb0 AZ: {:1.5f}\xb0".format(*wanted_position))
        print("Telescope wanted speed  ALT: {:1.5f}\xb0 per second, AZ: {:1.5f}\xb0 per second".format(*wanted_speed))

        ### todo

        # get actual position/speed of telescope
        # send instructions to motors to match actual to wanted
        
        



 

