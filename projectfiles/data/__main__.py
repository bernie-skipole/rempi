#!/usr/bin/env python3

# sys is used for the sys.exit function and to check python version
import sys, argparse

# Check the python version
if sys.version_info[0] != 3 or sys.version_info[1] < 2:
    print("Sorry, your python version is not compatable")
    print("This program requires python 3.2 or later")
    print("Program exiting")
    sys.exit(1)

# Requires python3 version of the waitress web server, 'python3-waitress' with debian
from waitress import serve

import skipoles

project = "pi01"

# Set up command line parser

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
description='Project for Raspberry Pi',
epilog='Stop the server with ctrl-c')

parser.add_argument("-p", "--port", type=int, dest="port", default=8000,
                  help="The port the web server will listen at, default 8000.")

parser.add_argument("-o", "--option", dest="option",
                  help="An optional value passed to your functions.")

parser.add_argument('--version', action='version', version=project + ' ' + '0.0.3')

args = parser.parse_args()

port = args.port

# An 'option' value can be passed to the project, and futher options to subprojects
# with a dictionary of {project:option,..} where each key is the project or sub project name
# and each option is any value you care to add, and which will appear as an argument in
# your start_project and start_call functions. This allows you to pass a parameter from the
# command line, or from start up code set here, to your project code if required.
# If you do not wish to use this function, then pass an empty dictionary.

if args.option:
    options = {project : args.option}
else:
    options = {}

site = skipoles.load_project(project, options)

if site is None:
    print("Project not found")
    sys.exit(1)

# This 'site' object can now be used in a wsgi app function
# by calling its 'respond' method, with the environ as argument.
# The method returns status, headers and the page data

def application(environ, start_response):
    "Defines the wsgi application"
    # uses the 'site' object created previously
    status, headers, data = site.respond(environ)
    start_response(status, headers)
    return data

# serve the site, using the waitress wsgi web server
serve(application, host='0.0.0.0', port=port)

