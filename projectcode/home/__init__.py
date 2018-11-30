


from ... import FailPage, GoTo, ValidateError, ServerError


from .. import hardware



def index_page(caller_ident, ident_list, submit_list, submit_dict, call_data, page_data, lang):
    "Fills in the public index page"

    page_data['headingtext', 'large_text'] = hardware.get_name()

    page_data['intro', 'large_text'] = "You are connected to Raspberry Pi - " + hardware.get_name()


