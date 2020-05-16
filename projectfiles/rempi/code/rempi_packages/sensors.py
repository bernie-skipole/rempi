
import collections

from skipole import FailPage, GoTo, ValidateError, ServerError


def sensor_table(skicall):
    """sets three lists for sensor table into page data"""
    skicall.page_data['sensors', 'col1'] = ["LED", "DOOR", "TEMPERATURE", "ALT", "AZ", "RA", "DEC"]
    skicall.page_data['sensors', 'col2'] = _get_sensor_values(skicall.proj_data['redis'])
    skicall.page_data['sensors', 'col3'] = [ "LED attached to pi",
                                             "Observatory door",
                                             "Temperature from probe",
                                             "Telescope Altitude",
                                             "Telescope Azimuth",
                                             "Target Right Ascension",
                                             "Target Declination"]


def sensors_json_api(skicall):
    "Returns sensors dictionary"
    sensors = ["LED", "DOOR", "TEMPERATURE", "ALT", "AZ", "RA", "DEC"]
    values = _get_sensor_values(skicall.proj_data['redis'])
    return collections.OrderedDict(zip(sensors,values))


def _get_sensor_values(redis):
    "Returns list of sensor values read from redis"

    values = []

    # get led status from redis
    led_status = redis.get('rempi01_led')
    if led_status == b"ON":
        value = 'ON'
    else:
        value = 'OFF'
    values.append(value)

    # get door
    door_status = redis.get('rempi01_door_status')
    if door_status is None:
        values.append("UNKNOWN")
    elif door_status == b"CLOSED":
        values.append("CLOSED")
    elif door_status == b"CLOSING":
        values.append("CLOSING")
    elif door_status == b"OPEN":
        values.append("OPEN")
    elif door_status == b"OPENING":
        values.append("OPENING")
    elif door_status == b"STOPPED":
        values.append("STOPPED")
    else:
        values.append("UNKNOWN")

    # get temperature
    value = redis.get('rempi01_temperature')
    if value is None:
        values.append("0.0")
    else:
        values.append(value.decode("utf-8"))

    # get altitude
    alt = redis.get('rempi01_current_alt')
    if alt is None:
        values.append("UNKNOWN")
    else:
        try:
            values.append("{:1.3f}".format(float(alt.decode("utf-8"))))
        except:
            values.append("UNKNOWN")


    # get azimuth
    az = redis.get('rempi01_current_az')
    if az is None:
        values.append("UNKNOWN")
    else:
        try:
            values.append("{:1.3f}".format(float(az.decode("utf-8"))))
        except:
            values.append("UNKNOWN")


    # get ra
    ra = redis.get('rempi01_target_ra')
    if ra is None:
        values.append("UNKNOWN")
    elif ra == b'':
        values.append("--")
    else:
        try:
            values.append("{:1.3f}".format(float(ra.decode("utf-8"))))
        except:
            values.append("UNKNOWN")


    # get dec
    dec = redis.get('rempi01_target_dec')
    if dec is None:
        values.append("UNKNOWN")
    elif dec == b'':
        values.append("--")
    else:
        try:
            values.append("{:1.3f}".format(float(dec.decode("utf-8"))))
        except:
            values.append("UNKNOWN")


    return values


def status(skicall):
    "Fills sensors status internet page"
    redis = skicall.proj_data['redis']
    temperature = redis.get('rempi01_temperature')
    if temperature is None:
        temperature = "0.0"
    else:
        temperature = temperature.decode("utf-8")
    skicall.page_data["tmeter", "measurement"] = temperature
    skicall.page_data["tvalue", "text"] = "Temperature : %s" % (temperature,)

