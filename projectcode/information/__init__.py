from ... import FailPage, GoTo, ValidateError, ServerError


def information_page(skicall):
    """Set up the information page"""
    if ('HTTP_HOST' in skicall.call_data) and skicall.call_data['HTTP_HOST']:
        skicall.page_data['control_json', 'content'] = skicall.call_data['HTTP_HOST'] + "/controls.json"
        skicall.page_data['sensors_json', 'content'] = skicall.call_data['HTTP_HOST'] + "/sensors.json"
