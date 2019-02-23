"""
This package will be called by the Skipole framework to access your data.
"""

import os, sys, threading, logging

from logging.handlers import RotatingFileHandler

from .. import FailPage, GoTo, ValidateError, ServerError, use_submit_list

from . import login, hardware, engine

from .control import state


# any page not listed here requires basic authentication
_PUBLIC_PAGES = [1,  # index
                 2,  # sensors
                 4,  # information
                 6,  # controls.json
                 7,  # sensors.json
                 9,  # sensors_refresh
                21,  # rempi.log.1
                22,  # rempi.log.2
                23,  # rempi.log.3
                24,  # rempi.log.4
                25,  # rempi.log.5
                29,  # rempi.log
               540,  # no_javascript
              1002,  # css
              1004,  # css
              1006,  # css
              5001,  # weather
              5002   # weather by JSON
               ]


def start_project(project, projectfiles, path, option):
    """On a project being loaded, and before the wsgi service is started, this is called once,
       Note: it may be called multiple times if your web server starts multiple processes.
       This function should return a dictionary (typically an empty dictionary if this value is not used).
       Can be used to set any initial parameters, and the dictionary returned will be passed as
       'skicall.proj_data' to subsequent start_call functions."""

    logfile = os.path.join(projectfiles, project, 'rempi.log')
    handler = RotatingFileHandler(logfile, maxBytes=10000, backupCount=5)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', handlers= [handler])


    logging.info('start_project called')

    # create door state
    door = state.Door()
    door.output01 = hardware.get_boolean_power_on_value('output01')

    # setup hardware
    hardware.initial_setup_outputs()

    # set state of door
    # still to be done as it depends on hardware
    # door.set_state(door_open, door_closed, door_opening, door_closing)
    # door.start()

    # comms is True if communications to the server is working, this
    # is initially assumed True and gets set to False if no comms received after
    # about twenty minutes

    # lock is a threading lock which is aquired whenever an output is to be set
    # by a local action from this rempi web service or JSON request

    # enable_web_control is True if this accepts output commands via MQTT from
    # the web server, and can be set to False via the rempi web interface,
    # to ignore such commands 


    status_data = {'door':door,
                   'enable_web_control':True,
                   'comms':True
                  }

    proj_data = {'status': status_data,
                 'lock':threading.Lock(),       # lock object enables commands from web server to seize lock
                 'mqtt_client':None}

    # Create the mqtt client connection

    proj_data['mqtt_client'] = engine.create_mqtt(status_data)

    # create an input listener, which publishes messages on an input pin change
    listen = engine.listen_to_inputs(proj_data)

    # create an event schedular to do periodic actions
    scheduled_events = engine.ScheduledEvents(proj_data)
    # this is a callable which runs scheduled events, it
    # needs to be called in its own thread
    run_scheduled_events = threading.Thread(target=scheduled_events)
    # and start the thread
    run_scheduled_events.start()

    return proj_data


def start_call(called_ident, skicall):
    "When a call is initially received this function is called."
    if not called_ident:
        return
    if skicall.environ.get('HTTP_HOST'):
        # This is used in the information page to insert the host into a displayed url
        skicall.call_data['HTTP_HOST'] = skicall.environ['HTTP_HOST']
    else:
        skicall.call_data['HTTP_HOST'] = skicall.environ['SERVER_NAME']
    # password protected pages
    if called_ident[1] not in _PUBLIC_PAGES:
        # check login
        if not login.check_login(skicall.environ):
            # login failed, ask for a login
            return skicall.project,2010
    return called_ident


@use_submit_list
def submit_data(skicall):
    """This function is called when a Responder wishes to submit data for processing in some manner
       For two or more submit_list values, the decorator ensures the matching function is called instead"""
    raise FailPage("submit_list string not recognised")


def end_call(page_ident, page_type, skicall):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""

    # in this example, status is the value on input02
    status = hardware.get_text_input('input02')
    if status:
        skicall.page_data['topnav','status', 'para_text'] = status
    else:
        skicall.page_data['topnav','status', 'para_text'] = "Status: input02 unavailable"

    if page_type != "TemplatePage":
        return

    skicall.page_data['leftnav','left_name','large_text'] = hardware.get_name()



