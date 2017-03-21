
import random, collections

from ....skilift import FailPage, GoTo, ValidateError, ServerError

_SENSORS = ["one", "two", "three"]


def sensor_table01(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets two lists for sensor table 01 into page data"""
    page_data['table01', 'col0'] = _SENSORS
    # and set values
    sensor_table01_values(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


def sensor_table01_values(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets values list for sensor table 01 into page data"""
    page_data['table01', 'col1'] = _get_sensor_values()


def sensors_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns sensors dictionary"
    sensors = _SENSORS
    values = _get_sensor_values()
    return collections.OrderedDict(zip(sensors,values))


def _get_sensor_values():
    "Returns list of sensor values"
    # currently just sets three random floating point numbers
    n1 = str(round(random.random(),4))
    n2 = str(round(random.random(),4))
    n3 = str(round(random.random(),4))
    return [ n1, n2, n3  ]
