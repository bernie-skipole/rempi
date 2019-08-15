
import collections

from skipole import FailPage, GoTo, ValidateError, ServerError


def sensor_table(skicall):
    """sets three lists for sensor table into page data"""
    sensors = ["LED", "TEMPERATURE"]
    skicall.page_data['sensors', 'col1'] = sensors
    skicall.page_data['sensors', 'col2'] = _get_sensor_values(sensors, skicall)
    skicall.page_data['sensors', 'col3'] = ["LED attached to pi", "Temperature from probe"]


def sensors_json_api(skicall):
    "Returns sensors dictionary"
    sensors = ["LED", "TEMPERATURE"]
    values = _get_sensor_values(sensors, skicall)
    return collections.OrderedDict(zip(sensors,values))


def _get_sensor_values(sensors, skicall):
    "Returns list of sensor values"
    redis = skicall.proj_data['redis']
    values = []
    for name in sensors:
        if name == "LED":
            # get led status from redis
            led_status = redis.get('led')
            if led_status == b"ON":
                value = 'ON'
            else:
                value = 'OFF'
            values.append(value)
        if name == "TEMPERATURE":
            value = redis.get('temperature')
            if value is None:
                values.append("0.0")
            else:
                values.append(value.decode("utf-8"))
    return values


def status(skicall):
    "Fills sensors status internet page"
    redis = skicall.proj_data['redis']
    temperature = redis.get('temperature')
    if temperature is None:
        temperature = "0.0"
    else:
        temperature = temperature.decode("utf-8")
    skicall.page_data["tmeter", "measurement"] = temperature
    skicall.page_data["tvalue", "text"] = "Temperature : %s" % (temperature,)
