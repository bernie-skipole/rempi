"""
This package will be called by the Skipole framework to access your data.
"""

import sys, threading

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
       'proj_data' to subsequent start_call functions."""

    # create door state
    door = state.Door()
    door.output01 = hardware.get_boolean_power_on_value('output01')

    # setup hardware
    hardware.initial_setup_outputs()

    # set state of door
    # still to be done as it depends on hardware
    # door.set_state(door_open, door_closed, door_opening, door_closing)


    # Create the mqtt client connection, with state values (currently only door)
    state_values = {'door':door}

    engine.create_mqtt(state_values)

    # create an input listener, which publishes messages on an input pin change
    listen = engine.listen_to_inputs()

    # create an event schedular to do periodic actions
    scheduled_events = engine.ScheduledEvents()
    # this is a callable which runs scheduled events, it
    # needs to be called in its own thread
    run_scheduled_events = threading.Thread(target=scheduled_events)
    # and start the thread
    run_scheduled_events.start()

    return {'scheduled_events':scheduled_events, 'listen':listen, 'door':door}


def start_call(environ, path, project, called_ident, caller_ident, received_cookies, ident_data, lang, option, proj_data):
    "When a call is initially received this function is called."
    # set the door state into call_data
    call_data = {'door':proj_data['door']}
    page_data = {}
    if not called_ident:
        return None, call_data, page_data, lang
    if environ.get('HTTP_HOST'):
        # This is used in the information page to insert the host into a displayed url
        call_data['HTTP_HOST'] = environ['HTTP_HOST']
    else:
        call_data['HTTP_HOST'] = environ['SERVER_NAME']
    # ensure project is in call_data
    call_data['project'] = project
    # password protected pages
    if called_ident[1] not in _PUBLIC_PAGES:
        # check login
        if not login.check_login(environ):
            # login failed, ask for a login
            return (project,2010), call_data, page_data, lang
    return called_ident, call_data, page_data, lang


@use_submit_list
def submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """This function is called when a Responder wishes to submit data for processing in some manner
       For two or more submit_list values, the decorator ensures the matching function is called instead"""

    raise FailPage("submit_list string not recognised")


def end_call(page_ident, page_type, call_data, page_data, proj_data, lang):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""

    # in this example, status is the value on input02
    status = hardware.get_text_input('input02')
    if status:
        page_data['topnav','status', 'para_text'] = status
    else:
        page_data['topnav','status', 'para_text'] = "Status: input02 unavailable"


    if page_type != "TemplatePage":
        return

    page_data['leftnav','left_name','large_text'] = hardware.get_name()



