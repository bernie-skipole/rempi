import collections

from ....skilift import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops, factory_defaults

# Global value is True if this is running on a raspberry pi
_RASPBERRYPI = False

def set_raspberrypi(raspberrypi):
    "Sets global value"
    global _RASPBERRYPI
    _RASPBERRYPI = raspberrypi


def control_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populate the control page, by setting widget values, and then the results values"""
    # widget output01 is boolean radio and expects a binary True, False value
    page_data['output01', 'radio_checked'] = _get_output01()
    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


def refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Fill in the control page results fields"""
    if _get_output01():
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : On"
    else:
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : Off"


def controls_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns json dictionary of output names : output values, used by external api"
    controls = factory_defaults.get_output_names()
    values = [ _get_output(name) for name in controls ]
    return collections.OrderedDict(zip(controls,values))


def set_output_from_browser(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets given output, called from browser via web page"""
    if ('output01', 'radio_checked') in call_data:
        # set output01
        _set_output('output01', call_data['output01', 'radio_checked'])
    # further elif statements will set further outputs


def set_output(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "External api call"
    if 'received_data' not in submit_dict:
        return
    received = submit_dict['received_data']
    if ('name' in received) and ('value' in received):
        name = received['name']
        value = received['value']
        controls = factory_defaults.get_output_names()
        if name not in controls:
            return
        _set_output(name, value)
        call_data['OUTPUT'] = name
           

def return_output(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """{outputname:value} returned as a result of external api call,
           outputname should have previously been set in call_data['OUTPUT']"""
    if 'OUTPUT' not in call_data:
        return {}
    outputname = call_data['OUTPUT']
    value = _get_output(outputname)
    if value is None:
        return {}
    return {outputname:value}


def set_multi_outputs(output_dict):
    """output_dict is a dictionary of name:value to set, called from __main__.py on power up"""
    for name, value in output_dict.items():
        _set_output(name, value)
    

def _set_output(name, value):
    """Sets an output, given the output name and value, converts received text (such as 'True' or 'true') to database values"""
    if name == 'output01':
        if (value == 'True') or (value == 'true') or (value is True):
            _set_output01(True)
        else:
            _set_output01(False)
    # to be followed by elif for other outputs


def _get_output(name):
    """Gets an output value, given the output name, return None on failure
          Returns True or False if boolean, has to be converted to required value by calling function"""
    if name == 'output01':
        # returns True or False
        return _get_output01()
    # to be followed by elif for other outputs

#######################################
#
# Functions:
#
#  _set_outputnn(value)
#  _get_outputnn()
#
# are to be provided for every output
#
#######################################

def _set_output01(value):
    "Sets output01, value given should be True or False, if boolean"
    global _RASPBERRYPI
    if _RASPBERRYPI:
        # set output on hardware, only if RASPBERRYPI is True
        pass
    # Also sets it in database
    database_ops.set_output('output01', value)

def _get_output01():
    "Gets output01"
    global _RASPBERRYPI
    if _RASPBERRYPI:
        # get output from hardware, if RASPBERRYPI is True
        pass
    # currently only reads from database, eventually will do it on hardware
    return database_ops.get_output('output01')
