
############################################################################
#
# schedule.py - this module defines
#
# ScheduledEvents
#
# A class that sets up periodic events to occur each hour
#
#############################################################################


import sys, sched, time


from . import communications


###  scheduled actions ###



def event1(mqtt_client, userdata):
    "event1 is to publish status"
    if not userdata['comms']:
        return
    try:
        communications.status_request(mqtt_client, userdata)
    except Exception:
        # return without action if any failure occurs
        pass


def event2(mqtt_client, userdata):
    """event2 is called every ten minutes
       decrements userdata['comms_countdown'], and checks if zero or less"""
    if not userdata['comms']:
        return
    if userdata['comms_countdown'] < 1:
        userdata['comms'] = False
        return
    # comms_countdown is still positive, decrement it
    userdata['comms_countdown'] -= 1




### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, mqtt_client, userdata):
        "Stores the mqtt_clent and creates the schedule of hourly events"
        # create a list of event callbacks and minutes past the hour for each event in turn

        event_list = [
                       (event1, 9),   # event 1 at 9 minutes past the hour
                       (event1, 24),  # event 1 again at 24 minutes past the hour
                       (event1, 39),  # etc.,
                       (event1, 54),
                       (event2, 2),   # heartbeat check every ten minutes
                       (event2, 12),
                       (event2, 22),
                       (event2, 32),
                       (event2, 42),
                       (event2, 52)]

        # sort the list
        self.event_list = sorted(event_list, key=lambda x: x[1])
        self.mqtt_client = mqtt_client
        self.userdata = userdata
        self.schedule = sched.scheduler(time.time, time.sleep)


    @property
    def queue(self):
        return self.schedule.queue


    def _create_next_hour_events(self):
        "Create a new set of events for the following hour"

        # get a time tuple for now
        ttnow = time.localtime()
        # get the timestamp for the beginning of the next hour
        nexthour = 3600 + time.mktime( (ttnow.tm_year,
                                        ttnow.tm_mon,
                                        ttnow.tm_mday,
                                        ttnow.tm_hour,
                                        0,                  # zero minutes
                                        0,                  # zero seconds
                                        ttnow.tm_wday,
                                        ttnow.tm_yday,
                                        ttnow.tm_isdst)  )

        # create scheduled events which are to occur
        # at interval minutes during nexthour

        for evt_callback, mins in self.event_list:
            self.schedule.enterabs(time = nexthour + mins*60,
                                   priority = 1,
                                   action = evt_callback,
                                   kwargs= {"mqtt_client":self.mqtt_client, "userdata":self.userdata}
                                   )

        # schedule a final event to occur 5 seconds before the end of nexthour
        self.schedule.enterabs(time = nexthour + 3595,
                               priority = 1,
                               action = self._create_next_hour_events
                               )



    def __call__(self): 
        "Schedule Events, and run the scheduler, this is a blocking call, so run in a thread"
        # set the scheduled events for the current hour

        # get a time tuple for now
        ttnow = time.localtime()
        # get the timestamp of now
        rightnow = time.mktime(ttnow)

        # get the timestamp for the beginning of the current hour
        thishour = time.mktime( (ttnow.tm_year,
                                 ttnow.tm_mon,
                                 ttnow.tm_mday,
                                 ttnow.tm_hour,
                                 0,                  # zero minutes
                                 0,                  # zero seconds
                                 ttnow.tm_wday,
                                 ttnow.tm_yday,
                                 ttnow.tm_isdst)  )

        # create times at which events are to occur
        # during the remaining part of this hour
        for evt_callback, mins in self.event_list:
            event_time = thishour + mins*60
            if event_time > rightnow:
                self.schedule.enterabs(time = event_time,
                                       priority = 1,
                                       action = evt_callback,
                                       kwargs= {"mqtt_client":self.mqtt_client, "userdata":self.userdata}
                                       )

        # schedule a final event to occur 5 seconds before the end of thishour
        self.schedule.enterabs(time = thishour + 3595,
                               priority = 1,
                               action = self._create_next_hour_events
                               )


        # and run the schedule
        self.schedule.run()


# How to use

# create event callback functions
# add them to event_list  in the class __init__, as tuples of (event function, minutes after the hour)

# create a ScheduledEvents instance
# scheduled_events = ScheduledEvents(mqtt_client, userdata)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required



