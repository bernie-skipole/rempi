"""
This package will be called by the Skipole framework to access your data.
"""

import os

from ...skilift import FailPage, GoTo, ValidateError, ServerError

from . import sensors, control, information, login, setup, database_ops

_PROTECTED_PAGES = [         8,      # external api call to set an output in named get field
                          3001,      # set output 01 returns web page, for none-jscript browsers
                          3002,      # set output 01 returns json page, for jscript browsers
                          4003,      # set output 01 power-up option, returns web page, for none-jscript browsers
                          4004,      # set output 01 power-up option, returns json page, for jscript browsers
                          4400,      # set redis options
                          4401       # set redis option via json
                   ]


def start_project(project, projectfiles, path, option):
    """On a project being loaded, and before the wsgi service is started, this is called once,
       Note: it may be called multiple times if your web server starts multiple processes.
       This function should return a dictionary (typically an empty dictionary if this value is not used).
       Can be used to set any initial parameters, and the dictionary returned will be passed as
       'proj_data' to subsequent start_call functions."""
    proj_data = {}

    # checks database exists, if not create it
    database_ops.start_database(project, projectfiles)

    # get dictionary of initial start-up output values from database
    output_dict = database_ops.power_up_values()
    if not output_dict:
        print("Invalid read of database, delete setup directory to revert to defaults")
        sys.exit(1)

    # set the initial start-up values
    control.set_multi_outputs(output_dict)

    # See
    # www.modmypi.com/blog/ds18b20-one-wire-digital-temperature-sensor-and-the-raspberry-pi

    # Using a DS18B20, and with one-wire enabled.
    # my unit has address 28-000007e4291f -alter this in the temp_sensor line below to match your
    # own sensor address

    # If this system is running on a development PC, leave the following lines commented out
    # and only un-comment them on the target raspberry pi

    # os.system('modprobe w1-gpio')
    # os.system('modprobe w1-therm')
    # proj_data['temp_sensor'] = "/sys/bus/w1/devices/28-000007e4291f/w1_slave"

    return proj_data


def start_call(environ, path, project, called_ident, caller_ident, received_cookies, ident_data, lang, option, proj_data):
    "When a call is initially received this function is called."
    call_data = {}
    page_data = {}
    if not called_ident:
        return None, call_data, page_data, lang

    # set temp_sensor into call_data
    if 'temp_sensor' in proj_data:
        call_data['temp_sensor'] = proj_data['temp_sensor']

    if 'HTTP_HOST' in environ:
        # This is used in the information page to insert the host into a displayed url
        call_data['HTTP_HOST'] = environ['HTTP_HOST']

    # password protected pages
    if called_ident[1] in _PROTECTED_PAGES:
        # check login
        if not login.check_login(environ):
            # login failed, ask for a login
            return (project,2010), call_data, page_data, lang
    return called_ident, call_data, page_data, lang


def submit_data(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "This function is called when a Responder wishes to submit data for processing in some manner"

    # calls to sensors package
    if submit_list and (submit_list[0] == 'sensors'):
        try:
            submitfunc = getattr(sensors, submit_list[1])
        except:
            raise FailPage("submit_list contains 'sensors', but function not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    # calls to control package
    if submit_list and (submit_list[0] == 'control'):
        try:
            submitfunc = getattr(control, submit_list[1])
        except:
            raise FailPage("submit_list contains 'control', but function not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    # calls to information package
    if submit_list and (submit_list[0] == 'information'):
        try:
            submitfunc = getattr(information, submit_list[1])
        except:
            raise FailPage("submit_list contains 'information', but function not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    # calls to login package
    if submit_list and (submit_list[0] == 'login'):
        try:
            submitfunc = getattr(login, submit_list[1])
        except:
            raise FailPage("submit_list contains 'login', but function not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)

    # calls to setup package
    if submit_list and (submit_list[0] == 'setup'):
        try:
            submitfunc = getattr(setup, submit_list[1])
        except:
            raise FailPage("submit_list contains 'setup', but function not recognised")
        return submitfunc(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


    raise FailPage("submit_list string not recognised")


def end_call(page_ident, page_type, call_data, page_data, proj_data, lang):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""
    return
