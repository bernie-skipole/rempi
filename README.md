# README #

This project is developed for specific hardware and functions required to control a robotic telescope at Todmorden Astronomy Centre.

An attempt will be made to document the build process using these wiki pages. This project may not be easily adaptable to other sites, as it will be very hardware dependent, however it may be of interest as an example.

Associated repositories:

framework - skipole web framework used to develop rempi

pi01 - base general project for running on a pi, rempi starts as a copy of pi01.

astro - which will be the main internet facing web server, and which will communicate to a pi running rempi.

rempicron - Python script to read and log sensor data, running under cron control.