
from base64 import b64decode


from ... import FailPage, GoTo, ValidateError, ServerError


# This is the access username
_USERNAME = "admin"
# This is the access password
_PASSWORD = "password"


def check_login(environ):
    "Returns True if login ok, False otherwise"
    try:
        auth = environ.get('HTTP_AUTHORIZATION')
        if auth:
            scheme, data = auth.split(" ", 1)
            if scheme.lower() != 'basic':
                return False
            username, password = b64decode(data).decode('UTF-8').split(':', 1)
            if username != _USERNAME:
                return False
            if password == _PASSWORD:
                # login ok
                return True
    except:
        pass
        # Any exception causes False to be returned
    # login fail
    return False


def request_login(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Set up the basic authentication"""
    realm = 'Basic realm="' + call_data['project'] + '"'
    page_data['headers'] = [
            ('content-type', 'text/html'),
            ('WWW-Authenticate', realm)]
    page_data['status'] = '401 Unauthorized'

