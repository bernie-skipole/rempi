#!/usr/bin/env python3

###########################
#
# pi01 robotic telescope
#
###########################

# sys is used for the sys.exit function and to check python version
import sys, os

# Check the python version
if sys.version_info[0] != 3 or sys.version_info[1] < 2:
    print("Sorry, your python version is not compatable")
    print("This program requires python 3.2 or later")
    print("Program exiting")
    sys.exit(1)

# argparse is used to pass the port and check value
import argparse

# used to run the python wsgi server
from wsgiref.simple_server import make_server

# the skipoles package contains your own code plus
# the skipole framework code
import skipoles 

# Sets up a parser to get port and check value
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='Robotics Telescope Raspberry Pi 01 web service',
                                 epilog='Stop the server with ctrl-c')

parser.add_argument("-p", "--port", type=int, dest="port", default=8000,
                  help="The port the web server will listen at, default 8000")


parser.add_argument('--version', action='version', version='0.0.9')

args = parser.parse_args()

# set debug mode on
skipoles.set_debug(True)

print("Loading site")


options = {"pi01": {"RaspberryPi":False}}

site = skipoles.load_project("pi01", options)

if site is None:
    print("Project not found")
    sys.exit(1)


# Define the wsgi app

def the_app(environ, start_response):
    "Defines the wsgi application"
    # uses the 'site' object created previously
    status, headers, data = site.respond(environ)
    start_response(status, headers)
    return data

# serve the site, using the python wsgi web server

httpd = make_server('', args.port, the_app)
print("Serving on port " + str(args.port) + "...")
print("Press ctrl-c to stop")

# Serve until process is killed
httpd.serve_forever()
