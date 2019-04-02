# Python3 program to display a terminal status and control menu
# for the Astronomy Centre REMSCOPE

import sys, curses
from control import status, cfg



def main(stdscr, MQTT_CLIENT):
    "Sets up the windows, and checks for input"

    # gets the initial system status
    sys_status = status.get_system_status()

    # no blinking cursor
    curses.curs_set(False)

    # getch will block for just half a second, allowing status to be checked
    curses.halfdelay(5)

    # set color pairs
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

    # standard screen shows as a green border around the status and menu windows
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()
    stdscr.refresh()

    status_window_height = 9

    # start status window, with colour pair 2
    statuswin = curses.newwin(status_window_height, curses.COLS-2, 1, 1)
    statuswin.bkgd(' ', curses.color_pair(2))
    showstatus(statuswin, sys_status)

    # start menu1 window, with colour pair 3
    # the height is full screen height less the status window height and less 2 for the border
    menu1win = curses.newwin(curses.LINES-status_window_height-2, curses.COLS-2, status_window_height+1, 1)
    menu1win.bkgd(' ', curses.color_pair(3))
    menu1(menu1win)

    curses.doupdate()

    rempi_status_count = 1

    # wait for an input
    while True:
        # reset count to zero every fourth pass (every two seconds)
        if rempi_status_count > 3:
            rempi_status_count = 0

        c = stdscr.getch()
        # For each menu option
        if c == ord('1'):
            status.send_led_on(MQTT_CLIENT)
            rempi_status_count = 1 # so status request is delayed
        elif c == ord('2'):
            status.send_led_off(MQTT_CLIENT)
            rempi_status_count = 1 # so status request is delayed
        # Final menu option q for quit
        elif c == ord('q') or c == ord('Q'):
            break  # Exit the while loop

        if rempi_status_count == 0:
            # every fourth pass, send an MQTT message requesting status
            status.request_status(MQTT_CLIENT)
        else:
            # every 1st, 2nd, 3rd pass and after any key pressed
            # check system status flags
            new_status = status.get_system_status()
            if new_status != sys_status:
                showstatus(statuswin, new_status)
                curses.doupdate()
                sys_status = new_status
        # increment count
        rempi_status_count += 1

    # Clear screen and end the program
    stdscr.clear()
    stdscr.refresh()


def showstatus(statuswin, sys_status):
    "sys_status is the status tuple, fills in the status window"
    network_status = "Network: %s" % sys_status.network
    led_status = "LED: %s" % sys_status.led
    statuswin.clear()
    statuswin.box(0,0)
    statuswin.addstr(2,5,"REMScope Status:")
    statuswin.addstr(3,10,network_status)
    statuswin.addstr(4,10,led_status)
    statuswin.noutrefresh()


def menu1(menu1win):
    "Display the initial menu 1"
    # menu options
    menu1win.clear()
    menu1win.box(0,0)
    menu1win.addstr(2,5,"Choose an option:")
    menu1win.addstr(4,10,"1 - To turn on the LED")
    menu1win.addstr(5,10,"2 - To turn off the LED")
    menu1win.addstr(6,10,"3 - Future option")
    menu1win.addstr(7,10,"4 - Future option")
    menu1win.addstr(9,10,"Q - To quit the program")
    menu1win.noutrefresh()


if __name__ == "__main__":

    mqtt_parameters = cfg.get_mqtt()

    # create an MQTT client and run in another thread
    MQTT_CLIENT = status.create_mqtt(*mqtt_parameters)

    if MQTT_CLIENT is None:
        print("Failed to start MQTT client", file=sys.stderr)
        sys.exit(1)

    status.set_network_status("MQTT client started")
    # start the curses screen
    curses.wrapper(main, MQTT_CLIENT)


