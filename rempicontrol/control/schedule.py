
############################################################################
#
# schedule.py - this module defines
#
# ScheduledEvents
#
# A class that sets up periodic events to occur each hour
#
#############################################################################


import sys, sched, time, logging



###  scheduled actions ###


def event1(*args):
    "event1 is to store temperature"
    try:
        redis = args[0]
        state = args[1]
        # this logs the temperature to redis
        state['temperature'].get_temperature()
    except Exception:
        # return without action if any failure occurs
        logging.error('Exception during scheduled Event1')
        return
    logging.info("Temperature recorded to redis")




### scheduled actions to occur at set times each hour ###

class ScheduledEvents(object):

    def __init__(self, redis, state):
        "Stores the mqtt_clent and creates the schedule of hourly events"
        # create a list of event callbacks and minutes past the hour for each event in turn

        # initially start with event1 occurring every five minutes (on minutes 1,6,11,16....56)
        event_list = []
        for mins in range(1, 61,5):
            event_list.append((event1,mins))
        # add further events in format event_list.append((event2,mins)) etc.,
        # sort the list
        self.event_list = sorted(event_list, key=lambda x: x[1])
        self.state = state
        self.redis = redis
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
                                   argument = (self.redis, self.state)
                                   )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
 
        final_event_time = nexthour + last_event[1]*60 + 30
        self.schedule.enterabs(time = final_event_time,
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
                                       argument = (self.redis, self.state)
                                       )

        # schedule a final event to occur 30 seconds after last event
        last_event = self.event_list[-1]
        
        final_event_time = thishour + last_event[1]*60 + 30
        self.schedule.enterabs(time = final_event_time,
                               priority = 1,
                               action = self._create_next_hour_events
                               )


        # and run the schedule
        self.schedule.run()


# How to use

# create event callback functions
# add them to event_list  in the class __init__, as tuples of (event function, minutes after the hour)

# create a ScheduledEvents instance
# scheduled_events = ScheduledEvents(state)
# this is a callable, use it as a thread target
# run_scheduled_events = threading.Thread(target=scheduled_events)
# and start the thread
# run_scheduled_events.start()

# the event callbacks should be set with whatever action is required



