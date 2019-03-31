import collections, logging

from skipole import FailPage, GoTo, ValidateError, ServerError

from .. import hardware, engine



def control_page(skicall):
    """Populate the control page, by setting widget values, and then the results values"""
    # display web_control status
    if skicall.proj_data['status']['enable_web_control']:
        skicall.page_data['web_control', 'para_text'] = "Control from the Internet web server is ENABLED"
        skicall.page_data['toggle_web_control', 'button_text'] = "Disable Internet Control"
    else:
        skicall.page_data['web_control', 'para_text'] = "Control from the Internet web server is DISABLED"
        skicall.page_data['toggle_web_control', 'button_text'] = "Enable Internet Control"
    # display output description
    skicall.page_data['output01_description', 'para_text'] = hardware.get_output_description('output01')
    # widget output01 is boolean radio and expects a binary True, False value
    if _get_output('output01', skicall)  == 'ON':
        skicall.page_data['output01', 'radio_checked'] = True
    else:
        skicall.page_data['output01', 'radio_checked'] = False
    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(skicall)


def toggle_web_control(skicall):
    "Enable / disable the enable_web_control flag in proj_data"
    if skicall.proj_data['status']['enable_web_control']:
        skicall.proj_data['status']['enable_web_control'] = False
        logging.warning("Internet control has been disabled")
    else:
        skicall.proj_data['status']['enable_web_control'] = True
        logging.warning("Internet control has been enabled")

def refresh_results(skicall):
    """Fill in the control page results fields"""
    if _get_output('output01', skicall)  == 'ON':
        skicall.page_data['output01_result', 'para_text'] = "The current value of output 01 is : On"
    else:
        skicall.page_data['output01_result', 'para_text'] = "The current value of output 01 is : Off"


def controls_json_api(skicall):
    "Returns json dictionary of output names : output values, used by external api"
    if _get_output('output01', skicall)  == 'ON':
        return collections.OrderedDict([('output01', True)])
    else:
        return collections.OrderedDict([('output01', False)])



def set_output_from_browser(skicall):
    """sets given output, called from browser via web page"""
    if ('output01', 'radio_checked') in skicall.call_data:
        # set output01
        _set_output('output01', skicall.call_data['output01', 'radio_checked'], skicall)
    # further elif statements could set further outputs if they are present in call_data


def set_output(skicall):
    "External api call"
    if 'received_data' not in skicall.submit_dict:
        return
    received = skicall.submit_dict['received_data']
    if ('name' in received) and ('value' in received):
        name = received['name']
        value = received['value']
        controls = hardware.get_output_names()
        if name not in controls:
            return
        _set_output(name, value, skicall)
        skicall.call_data['OUTPUT'] = name
           

def return_output(skicall):
    """{outputname:value} returned as a result of external api call,
           outputname should have previously been set in call_data['OUTPUT']"""
    if 'OUTPUT' not in skicall.call_data:
        return {}
    outputname = skicall.call_data['OUTPUT']
    value = _get_output(outputname, skicall)
    if value is None:
        return {}
    return {outputname:value}


def _set_output(name, value, skicall):
    """Sets an output, given the output name and value"""

    # wait until a lock is aquired and block anyone else from changing an output

    lock = skicall.proj_data['status']['lock']
    with lock:
        engine.set_output(name, value, skicall.proj_data)
        # publish output status by mqtt
        engine.output_status(name, skicall.proj_data)




def _get_output(name, skicall):
    """Gets an output value, given the output name, return None on failure"""
    # instructions to get an output from hardware are placed here
    hardtype = hardware.get_output_type(name)
    if hardtype == 'boolean':
        hardvalue = hardware.get_boolean_output(name)
        if hardvalue is not None:
            return hardvalue
    # if hardvalue not available, reads the stored output from the door state
    if skicall.proj_data['status']['door'].output01:
        return 'ON'
    else:
        return 'OFF' 

