import collections

from ... import FailPage, GoTo, ValidateError, ServerError

from .. import database_ops, hardware


def control_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populate the control page, by setting widget values, and then the results values"""
    # display output description
    page_data['output01_description', 'para_text'] = hardware.get_output_description('output01')
    # widget output01 is boolean radio and expects a binary True, False value
    page_data['output01', 'radio_checked'] = _get_output('output01')
    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


def refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Fill in the control page results fields"""
    if _get_output('output01'):
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : On"
    else:
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : Off"


def controls_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns json dictionary of output names : output values, used by external api"
    controls = hardware.get_output_names()
    values = [ _get_output(name) for name in controls ]
    return collections.OrderedDict(zip(controls,values))


def set_output_from_browser(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets given output, called from browser via web page"""
    if ('output01', 'radio_checked') in call_data:
        # set output01
        _set_output('output01', call_data['output01', 'radio_checked'], submit_dict['proj_data'])
    # further elif statements could set further outputs if they are present in call_data


def set_output(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "External api call"
    if 'received_data' not in submit_dict:
        return
    received = submit_dict['received_data']
    if ('name' in received) and ('value' in received):
        name = received['name']
        value = received['value']
        controls = hardware.get_output_names()
        if name not in controls:
            return
        _set_output(name, value, submit_dict['proj_data'])
        call_data['OUTPUT'] = name
           

def return_output(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """{outputname:value} returned as a result of external api call,
           outputname should have previously been set in call_data['OUTPUT']"""
    if 'OUTPUT' not in call_data:
        return {}
    outputname = call_data['OUTPUT']
    value = _get_output(outputname)
    if value is None:
        return {}
    return {outputname:value}


def set_multi_outputs(output_dict):
    """output_dict is a dictionary of name:value to set"""
    for name, value in output_dict.items():
        _set_output(name, value)
    

def _set_output(name, value, proj_data={}):
    """Sets an output, given the output name and value"""
    output_type = hardware.get_output_type(name)
    if output_type is None:
        return
    if ('mqtt_client' in proj_data):
        mqtt_client = proj_data['mqtt_client']
    else:
        mqtt_client = None
    if output_type == 'boolean':
        if (value == 'True') or (value == 'true') or (value == 'ON') or (value is True):
            value = True
        else:
            value = False
        hardware.set_boolean_output(name, value)
        if mqtt_client is not None:
            topic = "From_" + hardware.get_name() + "/Outputs/" + name
            if value:
                mqtt_client.publish(topic=topic, payload='ON')
            else:
                mqtt_client.publish(topic=topic, payload='OFF')
    if output_type == 'int':
        if not isinstance(value, int):
            try:
                value = int(value)
            except:
                # Invalid value
                return
    if output_type == 'text':
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                # Invalid value
                return
        
    # Set output value in database
    database_ops.set_output(name, value)


def _get_output(name):
    """Gets an output value, given the output name, return None on failure"""
    # instructions to get an output from hardware are placed here
    hardtype = hardware.get_output_type(name)
    if hardtype == 'boolean':
        hardvalue = hardware.get_boolean_output(name)
        if hardvalue is not None:
            return hardvalue
    # if hardvalue not available, reads the stored output from the database
    return database_ops.get_output(name)
