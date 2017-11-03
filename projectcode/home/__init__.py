


from ... import FailPage, GoTo, ValidateError, ServerError


from .. import database_ops, hardware



def index_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in the public index page"

    page_data['headingtext', 'large_text'] = hardware.get_name()

    page_data['intro', 'large_text'] = "You are connected to Raspberry Pi - " + hardware.get_name()

    message_string = database_ops.get_all_messages()
    if message_string:
        page_data['messages', 'para_text'] = message_string

