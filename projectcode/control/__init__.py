import collections

from ... import FailPage, GoTo, ValidateError, ServerError

from .. import hardware, engine



def control_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populate the control page, by setting widget values, and then the results values"""
    # display output description
    page_data['output01_description', 'para_text'] = hardware.get_output_description('output01')
    # widget output01 is boolean radio and expects a binary True, False value
    if _get_output('output01', call_data)  == 'ON':
        page_data['output01', 'radio_checked'] = True
    else:
        page_data['output01', 'radio_checked'] = False
    # further widgets for further outputs to be set here
    # finally fill in all results fields
    refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)


def refresh_results(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Fill in the control page results fields"""
    if _get_output('output01', call_data)  == 'ON':
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : On"
    else:
        page_data['output01_result', 'para_text'] = "The current value of output 01 is : Off"


def controls_json_api(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Returns json dictionary of output names : output values, used by external api"
    if _get_output('output01', call_data)  == 'ON':
        return collections.OrderedDict([('output01', True)])
    else:
        return collections.OrderedDict([('output01', False)])



def set_output_from_browser(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """sets given output, called from browser via web page"""
    if ('output01', 'radio_checked') in call_data:
        # set output01
        _set_output('output01', call_data['output01', 'radio_checked'], call_data)
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
        _set_output(name, value, call_data)
        call_data['OUTPUT'] = name
           

def return_output(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """{outputname:value} returned as a result of external api call,
           outputname should have previously been set in call_data['OUTPUT']"""
    if 'OUTPUT' not in call_data:
        return {}
    outputname = call_data['OUTPUT']
    value = _get_output(outputname, call_data)
    if value is None:
        return {}
    return {outputname:value}


def _set_output(name, value, call_data):
    """Sets an output, given the output name and value"""
    if name == 'output01':
        if (value is True) or (value == 'True') or (value == 'ON'):
            call_data['door'].output01 = True
        else:
            call_data['door'].output01 = False
    # publish output status by mqtt
    engine.output_status(name)


def _get_output(name, call_data):
    """Gets an output value, given the output name, return None on failure"""
    # instructions to get an output from hardware are placed here
    hardtype = hardware.get_output_type(name)
    if hardtype == 'boolean':
        hardvalue = hardware.get_boolean_output(name)
        if hardvalue is not None:
            return hardvalue
    # if hardvalue not available, reads the stored output from the door state
    if call_data['door'].output01:
        return 'ON'
    else:
        return 'OFF' 

