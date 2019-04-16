
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
            value = redis.get('temperature').decode("utf-8")
            values.append(value)
    return values


def temperature(skicall):
    "Fills weather station temperature meter"
    redis = skicall.proj_data['redis']
    temperature = redis.get('temperature').decode("utf-8")
    skicall.page_data["temperature", "measurement"] = temperature
    skicall.page_data["temperature_value", "text"] = "Temperature : %s" % (temperature,)
