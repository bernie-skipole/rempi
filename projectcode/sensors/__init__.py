
import collections

from ... import FailPage, GoTo, ValidateError, ServerError
from .. import hardware


def sensor_table(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets three lists for sensor table into page data"""
    sensors = hardware.get_input_names()
    page_data['sensors', 'col1'] = sensors
    page_data['sensors', 'col2'] = _get_sensor_values(sensors)
    page_data['sensors', 'col3'] = [hardware.get_input_description(name) for name in sensors]


def sensors_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns sensors dictionary"
    sensors = hardware.get_input_names()
    values = _get_sensor_values(sensors)
    return collections.OrderedDict(zip(sensors,values))


def _get_sensor_values(sensors):
    "Returns list of sensor values"
    values = []
    for name in sensors:
        input_type = hardware.get_input_type(name)
        if input_type == 'boolean':
            invalue = hardware.get_boolean_input(name)
            if invalue is None:
                value = 'UNKNOWN'
            elif invalue:
                value = 'ON'
            else:
                value = 'OFF'
        elif input_type == 'text':
            value = hardware.get_text_input(name)
        elif input_type == 'float':
            value = str(hardware.get_float_input(name))
        else:
            value = ''
        values.append(value)
    return values


def temperature(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills weather station temperature meter"
    temperature = str(hardware.get_temperature())
    page_data["temperature", "measurement"] = temperature
    page_data["temperature_value", "text"] = "Temperature : %s" % (temperature,)
