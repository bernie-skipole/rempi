"""
This package will be called by the Skipole framework to access your data.
"""

import os, sys

from datetime import datetime

from skipole import WSGIApplication, FailPage, GoTo, ValidateError, ServerError, set_debug, use_submit_list


# the framework needs to know the location of the projectfiles directory holding this and
# other projects - specifically the skis and skiadmin projects
# The following line assumes, as default, that this file is located beneath
# ...projectfiles/newproj/code/

PROJECTFILES = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PROJECT = 'rempi'


from rempi_packages import login


# any page not listed here requires basic authentication
_PUBLIC_PAGES = [1,  # index
                 2,  # sensors
                 4,  # information
                 7,  # sensors.json
                 9,  # sensors_refresh
                11,  # status called from information page
                21,  # rempi.log.1
                22,  # rempi.log.2
                23,  # rempi.log.3
                24,  # rempi.log.4
                25,  # rempi.log.5
                29,  # rempi.log
               540,  # no_javascript
              1002,  # css
              1004,  # css
              1006,  # css
              5001,  # internet
              5002   # internet by JSON
               ]



from redis import StrictRedis

# create redis connection
redis = StrictRedis(host='localhost', port=6379)

proj_data = {'redis':redis}

redis.set('web_control', 'ENABLED')


def start_call(called_ident, skicall):
    "When a call is initially received this function is called."
    if not called_ident:
        return
    if skicall.environ.get('HTTP_HOST'):
        # This is used in the information page to insert the host into a displayed url
        skicall.call_data['HTTP_HOST'] = skicall.environ['HTTP_HOST']
    else:
        skicall.call_data['HTTP_HOST'] = skicall.environ['SERVER_NAME']
    # password protected pages
    if called_ident[1] not in _PUBLIC_PAGES:
        # check login
        if not login.check_login(skicall.environ):
            # login failed, ask for a login
            return skicall.project,2010
    return called_ident


@use_submit_list
def submit_data(skicall):
    """This function is called when a Responder wishes to submit data for processing in some manner
       For two or more submit_list values, the decorator ensures the matching function is called instead"""
    raise FailPage("submit_list string not recognised")


def end_call(page_ident, page_type, skicall):
    """This function is called at the end of a call prior to filling the returned page with page_data,
       it can also return an optional ident_data string to embed into forms."""
    if (page_type == "TemplatePage") or (page_type == "JSON"):
        if 'status' in skicall.call_data:
            skicall.page_data['topnav','status', 'para_text'] = skicall.call_data['status']
        else:
            now = datetime.utcnow().strftime("%c")
            skicall.page_data['topnav','status', 'para_text'] = "UTC: " + now
    if page_type != "TemplatePage":
        return
    skicall.page_data['leftnav','left_name','large_text'] = "REMPI01"



# create the wsgi application
application = WSGIApplication(project=PROJECT,
                              projectfiles=PROJECTFILES,
                              proj_data=proj_data,
                              start_call=start_call,
                              submit_data=submit_data,
                              end_call=end_call,
                              url="/")



skis_code = os.path.join(PROJECTFILES, 'skis', 'code')
if skis_code not in sys.path:
    sys.path.append(skis_code)
import skis
skis_application = skis.makeapp(PROJECTFILES)
application.add_project(skis_application, url='/rempi01/lib')



if __name__ == "__main__":


    ####### THESE LINES ADD SKIADMIN ### REMOVE WHEN DEPLOYED #####################
    #                                                                             #
    set_debug(True)                                                               #
    skiadmin_code = os.path.join(PROJECTFILES, 'skiadmin', 'code')                #
    if skiadmin_code not in sys.path:                                             #
        sys.path.append(skiadmin_code)                                            #
    import skiadmin                                                               #
    skiadmin_application = skiadmin.makeapp(PROJECTFILES, editedprojname=PROJECT) #
    application.add_project(skiadmin_application, url='/skiadmin')                #
    #                                                                             #
    ###############################################################################

    from wsgiref.simple_server import make_server

    # serve the application
    host = ""
    port = 8000

    httpd = make_server(host, port, application)
    httpd.serve_forever()




