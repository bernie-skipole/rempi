


from ... import FailPage, GoTo, ValidateError, ServerError


from .. import hardware



def index_page(skicall):
    "Fills in the public index page"

    skicall.page_data['headingtext', 'large_text'] = hardware.get_name()

    skicall.page_data['intro', 'large_text'] = "You are connected to Raspberry Pi - " + hardware.get_name()


