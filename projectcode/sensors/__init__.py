
import random, collections

from ... import FailPage, GoTo, ValidateError, ServerError

_SENSORS = ["Temperature"]


def sensor_table01(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets two lists for sensor table 01 into page data"""
    page_data['table01', 'col1'] = _SENSORS
    # and set values
    sensor_table01_values(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


def sensor_table01_values(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets values list for sensor table 01 into page data"""
    page_data['table01', 'col2'] = _get_sensor_values(call_data)


def sensors_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns sensors dictionary"
    sensors = _SENSORS
    values = _get_sensor_values(call_data)
    return collections.OrderedDict(zip(sensors,values))


def _get_sensor_values(call_data):
    "Returns list of sensor values, in this case the list only has one element, the temperature"
    if 'temp_sensor' not in call_data:
        return ['x']
    temp_sensor = call_data['temp_sensor']
    try:
        with open(temp_sensor, 'r') as f:
            lines = f.readlines()
        if lines[0].strip()[-3:] != 'YES':
            return ['x']
        temp_output = lines[1].find('t=')
        if temp_output == -1:
            return ['x']
        temp_string = lines[1].strip()[temp_output+2:]
        temperature = float(temp_string) / 1000.0
    except:
        # return an 'x' to indicate invalid value
        return ['x']
    return [ str(temperature)  ]

