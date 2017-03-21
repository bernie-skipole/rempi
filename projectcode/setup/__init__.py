"The setup package"

import os

from ....skilift import FailPage, GoTo, ValidateError, ServerError, get_projectfiles_dir

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
        raise FailPage(message="Missing data, all fields are required. Please try again.", displaywidgetname='accesspassword')
    if newpassword1 != newpassword2:
        raise FailPage(message="The new password fields are not equal. Please try again.", displaywidgetname='accesspassword')
    if oldpassword == newpassword1:
        raise FailPage(message="The new and current passwords must be different. Please try again.", displaywidgetname='accesspassword')
    if len(newpassword1) < 4:
        raise FailPage(message="Four characters or more please. Please try again.", displaywidgetname='accesspassword')
    if not login.check_password(oldpassword):
        raise FailPage(message="Invalid current password. Please try again.", displaywidgetname='accesspassword')
    # password ok, now set it
    user = database_ops.get_access_user()
    if not database_ops.set_password(user, newpassword1):
        raise FailPage(message="Sorry, database access failure.", displaywidgetname='accesspassword')
    page_data['passwordset', 'show_para'] = True




