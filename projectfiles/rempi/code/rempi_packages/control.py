import collections

from skipole import FailPage, GoTo, ValidateError, ServerError



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
    skicall.page_data['led_description', 'para_text'] = "LED output"
    # widget led is boolean radio and expects a binary True, False value
    if _get_output('LED', skicall)  == 'ON':
        skicall.page_data['led', 'radio_checked'] = True
    else:
        skicall.page_data['led', 'radio_checked'] = False
    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(skicall)


def toggle_web_control(skicall):
    "Enable / disable the enable_web_control flag in proj_data"
    if skicall.proj_data['status']['enable_web_control']:
        skicall.proj_data['status']['enable_web_control'] = False
    else:
        skicall.proj_data['status']['enable_web_control'] = True


def refresh_results(skicall):
    """Fill in the control page results fields"""
    if _get_output('LED', skicall)  == 'ON':
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : On"
    else:
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : Off"


def controls_json_api(skicall):
    "Returns json dictionary of output names : output values, used by external api"
    if _get_output('LED', skicall)  == 'ON':
        return collections.OrderedDict([('LED', True)])
    else:
        return collections.OrderedDict([('LED', False)])



def set_output_from_browser(skicall):
    """sets given output, called from browser via web page"""
    if ('led', 'radio_checked') in skicall.call_data:
        # set LED
        _set_output('LED', skicall.call_data['led', 'radio_checked'], skicall)
    # further elif statements could set further outputs if they are present in call_data


def set_output(skicall):
    "External api call"
    if 'received_data' not in skicall.submit_dict:
        return
    received = skicall.submit_dict['received_data']
    if ('name' in received) and ('value' in received):
        name = received['name']
        value = received['value']
        # controls is a list - currently only with the single LED element
        controls = ["LED"]
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
    redis = skicall.proj_data['redis']
    if name == "LED":
        if (value is True) or (value == "ON") or (value == "true") or (value == "True"):
            redis.publish("control02", "ON")
        else:
            redis.publish("control02", "OFF")


def _get_output(name, skicall):
    """Gets an output value, given the output name, return None on failure"""
    redis = skicall.proj_data['redis']
    if name == "LED":
        # get led status from redis
        led_status = redis.get('led')
        if led_status == b"ON":
            return 'ON'
        else:
            return 'OFF'


