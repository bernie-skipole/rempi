


from ... import FailPage, GoTo, ValidateError, ServerError


from .. import database_ops



def index_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in the public index page"

    message_string = database_ops.get_all_messages()
    if message_string:
        page_data['messages', 'para_text'] = message_string

