from ....skilift import FailPage, GoTo, ValidateError, ServerError


def information_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Set up the information page"""
    if ('HTTP_HOST' in call_data) and call_data['HTTP_HOST']:
        page_data['control_json', 'content'] = call_data['HTTP_HOST'] + "/controls.json"
        page_data['sensors_json', 'content'] = call_data['HTTP_HOST'] + "/sensors.json"
