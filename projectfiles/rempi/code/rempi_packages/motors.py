

# These functions are called by responders to control the motors



from skipole import FailPage, GoTo, ValidateError, ServerError


def m1clockwise(skicall):
    "set m1 clockwise"
    redis = skicall.proj_data['redis']
    motor1status = redis.get('motor1status')
    if motor1status == b"STOPPED":
        _speed_duration('motor1', skicall)
        skicall.page_data['motor1status','para_text'] = "Requesting Motor 1 clockwise start"
        redis.publish("motor1control", "CLOCKWISE")
    else:
        skicall.page_data['motor1status','para_text'] = "Action unavailable"


def m1anticlockwise(skicall):
    "set m1 anti clockwise"
    redis = skicall.proj_data['redis']
    motor1status = redis.get('motor1status')
    if motor1status == b"STOPPED":
        _speed_duration('motor1', skicall)
        skicall.page_data['motor1status','para_text'] = "Requesting Motor 1 anti clockwise start"
        redis.publish("motor1control", "ANTICLOCKWISE")
    else:
        skicall.page_data['motor1status','para_text'] = "Action unavailable"


def m2clockwise(skicall):
    "set m2 clockwise"
    redis = skicall.proj_data['redis']
    motor2status = redis.get('motor2status')
    if motor2status == b"STOPPED":
        _speed_duration('motor2', skicall)
        skicall.page_data['motor2status','para_text'] = "Requesting Motor 2 clockwise start"
        redis.publish("motor2control", "CLOCKWISE")
    else:
        skicall.page_data['motor2status','para_text'] = "Action unavailable"


def m2anticlockwise(skicall):
    "set m2 anticlockwise"
    redis = skicall.proj_data['redis']
    motor2status = redis.get('motor2status')
    if motor2status == b"STOPPED":
        _speed_duration('motor2', skicall)
        skicall.page_data['motor2status','para_text'] = "Requesting Motor 2 anti clockwise start"
        redis.publish("motor2control", "ANTICLOCKWISE")
    else:
        skicall.page_data['motor2status','para_text'] = "Action unavailable"


def _speed_duration(motor, skicall):
    "Sets the given speed and duration into redis values"
    skicall.page_data['top_error', 'clear_error'] = True
    call_data = skicall.call_data
    if ('speed' not in call_data) or ('duration' not in call_data):
        raise FailPage("Invalid data submitted")
    try:
        speed = int(call_data['speed'])
    except:
        raise FailPage("Invalid speed submitted")
    if (speed < 1) or (speed > 100):
        raise FailPage("Invalid speed submitted")
    try:
        duration = float(call_data['duration'])
    except:
        raise FailPage("Invalid duration submitted")
    if (duration < 1) or (duration > 90):
        raise FailPage("Duration must be between 1 and 90 seconds")
    redis.set(motor+'speed', str(speed))
    redis.set(motor+'duration',str(duration)) 


