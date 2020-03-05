import collections

from skipole import FailPage, GoTo, ValidateError, ServerError



def control_page(skicall):
    """Populate the control page, by setting widget values, and then the results values"""
    # display web_control status
    redis = skicall.proj_data['redis']
    web_control = redis.get('rempi01_web_control')
    if web_control == b'ENABLED':
        skicall.page_data['web_control', 'para_text'] = "Control from the Internet web server is ENABLED"
        skicall.page_data['toggle_web_control', 'button_text'] = "Disable Internet Control"
    else:
        skicall.page_data['web_control', 'para_text'] = "Control from the Internet web server is DISABLED"
        skicall.page_data['toggle_web_control', 'button_text'] = "Enable Internet Control"

    # widget led is boolean radio and expects a binary True, False value
    if _get_led(redis) == 'ON':
        skicall.page_data['led', 'radio_checked'] = True
    else:
        skicall.page_data['led', 'radio_checked'] = False

    # set door widget
    door_status = _get_door(redis)
    if door_status in ["CLOSED", "CLOSING"]:
        skicall.page_data['door', 'radio_checked'] = True
    else:
        skicall.page_data['door', 'radio_checked'] = False

    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(skicall)


def toggle_web_control(skicall):
    "Enable / disable the enable_web_control flag in proj_data"
    redis = skicall.proj_data['redis']
    web_control = redis.get('rempi01_web_control')
    if web_control == b'ENABLED':
        redis.set('rempi01_web_control', 'DISABLED')
    else:
        redis.set('rempi01_web_control', 'ENABLED')


def refresh_results(skicall):
    """Fill in the control page results fields"""
    redis = skicall.proj_data['redis']

    if _get_led(redis) == 'ON':
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : On"
    else:
        skicall.page_data['led_result', 'para_text'] = "The current value of the LED is : Off"

    # get the door status
    door_status = _get_door(redis)
    skicall.page_data['door_result', 'para_text'] = "The current door status is : " + door_status


    # get the motor status
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
    redis = skicall.proj_data['redis']
    if ('led', 'radio_checked') in skicall.call_data:
        value = skicall.call_data['led', 'radio_checked']
        # set LED
        if (value is True) or (value == "ON") or (value == "true") or (value == "True"):
            redis.publish("control02", "ON")
        else:
            redis.publish("control02", "OFF")
    elif ('door', 'radio_checked') in skicall.call_data:
        value = skicall.call_data['door', 'radio_checked']
        # set Door
        if (value is True) or (value == "OPEN") or (value == "true") or (value == "True"):
            redis.publish("control01", "OPEN")
        else:
            redis.publish("control01", "CLOSE")



def _get_led(redis):
    """Gets LED status from redis"""
    led_status = redis.get('rempi01_led')
    if led_status == b"ON":
        return 'ON'
    else:
        return 'OFF'

def _get_door(redis):
    "Get door status from redis"
    door_status = redis.get('rempi01_door_status')
    if door_status is None:
        return "UNKNOWN"
    elif door_status == b"CLOSED":
        return "CLOSED"
    elif door_status == b"CLOSING":
        return "CLOSING"
    elif door_status == b"OPEN":
        return "OPEN"
    elif door_status == b"OPENING":
        return "OPENING"
    elif door_status == b"STOPPED":
        return "STOPPED"
    else:
        return "UNKNOWN"




