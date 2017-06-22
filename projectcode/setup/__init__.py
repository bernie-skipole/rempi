"The setup package"

import os

from ... import FailPage, GoTo, ValidateError, ServerError

from ....skilift import get_projectfiles_dir

from .. import login, database_ops

def setup_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Populates the setup page"""
    # First the text beneath the username, password fields
    project = ident_list[-1][0]
    username = database_ops.get_access_user()
    password = database_ops.get_default_password()
    defaults = "This will create a new setup, with defaults - username '%s' and password '%s'." % (username, password)
    setup_directory = os.path.join(get_projectfiles_dir(project), "setup")
    page_data['defaults', 'para_text'] = defaults
    page_data['setup', 'para_text'] = setup_directory
    # the power up values for each output - further functions to be added for each output
    get_pwr_output01(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang)
    # redis server settings
    redis_values = database_ops.get_redis()
    if not redis_values:
        raise FailPage(message = "Error: Failed to access database.")
    page_data['redis_ip', 'input_text'] = redis_values[0]
    page_data['redis_port', 'input_text'] = str(redis_values[1])
    page_data['redis_auth', 'input_text'] = redis_values[2]
    page_data['redis_db', 'input_text'] = str(redis_values[3])
    


# Further get_pwr_outputnn functions to be provided for each output

def get_pwr_output01(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Reads database and sets widgfields for output01"
    result = database_ops.get_power_values('output01')
    if not result:
        raise FailPage(message="Invalid database result")
    default_on_pwr, onpower = result
    page_data['output01_default','radio_checked'] = default_on_pwr
    page_data['output01_check','checked'] = onpower
    if onpower:
        if default_on_pwr:
            page_data['output01_result', 'para_text'] = "Current status: Powers up to 'On'."
        else:
            page_data['output01_result', 'para_text'] = "Current status: Powers up to 'Off'."
    else:
        page_data['output01_result', 'para_text'] = "Current status: Powers up to the last value set on output01."


def set_pwr_output01(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Sets database from data submitted via widgfields"
    # Get default value on power up
    if ('output01_default','radio_checked') in call_data:
        default_on_pwr = call_data[('output01_default','radio_checked')]
        if (default_on_pwr=='True') or (default_on_pwr=='true') or (default_on_pwr is True):
            default_on_pwr = True
        else:
            default_on_pwr = False
    else:
        raise FailPage(message = "invalid input")
    # Get the onpower enabled checkbox result
    if ('output01_check','checkbox') in call_data:
        onpower = call_data[('output01_check','checkbox')]
        if (onpower=='True') or (onpower=='true') or (onpower is True):
            onpower = True
        else:
            onpower = False
    else:
        raise FailPage(message = "invalid input")
    # set result into database
    if not database_ops.set_power_values('output01', default_on_pwr, onpower):
        raise FailPage(message = "Error: Failed to write to database.")
 


###############################
#
# Set the access password
#
###############################

def set_password(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Check password given, and set it into the database"""
    oldpassword = call_data['oldpassword', 'input_text']
    newpassword1 = call_data['newpassword1', 'input_text']
    newpassword2 = call_data['newpassword2', 'input_text']
    if (not oldpassword) or (not newpassword1) or (not newpassword2):
        raise FailPage(message="Missing data, all fields are required. Please try again.", widget='accesspassword')
    if newpassword1 != newpassword2:
        raise FailPage(message="The new password fields are not equal. Please try again.", widget='accesspassword')
    if oldpassword == newpassword1:
        raise FailPage(message="The new and current passwords must be different. Please try again.", widget='accesspassword')
    if len(newpassword1) < 4:
        raise FailPage(message="Four characters or more please. Please try again.", widget='accesspassword')
    if not login.check_password(oldpassword):
        raise FailPage(message="Invalid current password. Please try again.", widget='accesspassword')
    # password ok, now set it
    user = database_ops.get_access_user()
    if not database_ops.set_password(user, newpassword1):
        raise FailPage(message="Sorry, database access failure.", widget='accesspassword')
    page_data['passwordset', 'show_para'] = True



##########################################################
#
# Set Redis parameters, IP address, port, password and db
#
##########################################################

def set_redis(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    """Check values given, and set them into the database"""
    ip = call_data['redis_ip', 'input_text']
    port = call_data['redis_port', 'input_text']
    auth = call_data['redis_auth', 'input_text']
    db = call_data['redis_db', 'input_text']
    # the redis port, default 6379
    if not port:
        port = 6379
    else:
        try:
            port = int(port)
        except:
            raise FailPage(message="Invalid port.", widget='redissetup')
    # the redis database number, default 0
    if not db:
        db = 0
    else:
        try:
            db = int(db)
        except:
            raise FailPage(message="Invalid database number.", widget='redissetup')
    if (db < 0) or (db > 16):
        raise FailPage(message="Invalid database number.", widget='redissetup') 
    # set values
    if not database_ops.set_redis(ip, port, auth, db):
        raise FailPage(message="Sorry, database access failure.", widget='redissetup')
    if not ip:
        page_data['redisset', 'para_text'] = "No IP address, redis disabled"
    else:
        page_data['redisset', 'para_text'] = "Redis server at: %s:%s db:%s" % (ip,port,db)
    page_data['redisset', 'show_para'] = True
    # clear any previous error (needed by JSON call, web call refreshes entire page anyway)
    page_data['redissetup', 'clear_error'] = True

