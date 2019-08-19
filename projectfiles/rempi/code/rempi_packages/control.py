import collections

from skipole import FailPage, GoTo, ValidateError, ServerError



def control_page(skicall):
    """Populate the control page, by setting widget values, and then the results values"""
    # display web_control status
    redis = skicall.proj_data['redis']
    web_control = redis.get('web_control')
    if web_control == b'ENABLED':
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
    redis = skicall.proj_data['redis']
    web_control = redis.get('web_control')
    if web_control == b'ENABLED':
        redis.set('web_control', 'DISABLED')
    else:
        redis.set('web_control', 'ENABLED')


def refresh_results(skicall):
    """Fill in the control page results fields"""
    if _get_output('LED', skicall)  == 'ON':
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : On"
    else:
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : Off"

    # get the motor status
    redis = skicall.proj_data['redis']
    motor1status = redis.get('motor1status')
    if motor1status == b"CLOCKWISE":
        motor1status = "Motor 1 running clockwise"
    elif motor1status == b"ANTICLOCKWISE":
        motor1status = "Motor 1 running anti clockwise"
    elif motor1status == b"STOPPED":
        motor1status = "Motor 1 stopped"
    else:
        motor1status = "Motor 1 status : unknown"
    motor2status = redis.get('motor2status')
    if motor2status == b"CLOCKWISE":
        motor2status = "Motor 2 running clockwise"
    elif motor2status == b"ANTICLOCKWISE":
        motor2status = "Motor 2 running anti clockwise"
    elif motor2status == b"STOPPED":
        motor2status = "Motor 2 stopped"
    else:
        motor2status = "Motor 2 status : unknown"
    # Set the status in the paragraph widgets
    skicall.page_data['motor1status','para_text'] = motor1status
    skicall.page_data['motor2status','para_text'] = motor2status



def set_output_from_browser(skicall):
    """sets given output, called from browser via web page"""
    if ('led', 'radio_checked') in skicall.call_data:
        # set LED
        _set_output('LED', skicall.call_data['led', 'radio_checked'], skicall)
    # further elif statements could set further outputs if they are present in call_data



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



