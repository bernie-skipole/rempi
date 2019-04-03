


from skipole import FailPage, GoTo, ValidateError, ServerError




def index_page(skicall):
    "Fills in the public index page"

    skicall.page_data['headingtext', 'large_text'] = "REMPI01"

    skicall.page_data['intro', 'large_text'] = "You are connected to Raspberry Pi - REMPI01"


