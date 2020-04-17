#!/home/rempi/rempivenv/bin/python3

# Python3 program to display a terminal status and control menu
# for the Astronomy Centre REMSCOPE

import sys, curses

from redis import StrictRedis



def main(stdscr, rconn, pubsub):
    "Sets up the windows, and checks for input"

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
    showstatus(statuswin, rconn, "Terminal started")

    # start menu1 window, with colour pair 3
    # the height is full screen height less the status window height and less 2 for the border
    menu1win = curses.newwin(curses.LINES-status_window_height-2, curses.COLS-2, status_window_height+1, 1)
    menu1win.bkgd(' ', curses.color_pair(3))

    # menu1 options
    menu1win.clear()
    menu1win.box(0,0)
    menu1win.addstr(2,5,"Choose an option:")
    menu1win.addstr(4,10,"1 - To turn on the LED")
    menu1win.addstr(5,10,"2 - To turn off the LED")
    menu1win.addstr(6,10,"3 - To open the door")
    menu1win.addstr(7,10,"4 - To close the door")
    menu1win.addstr(8,10,"5 - To stop the door")
    menu1win.addstr(9,10,"Q - To quit the program")
    menu1win.noutrefresh()

    curses.doupdate()

    # wait for an input
    while True:

        c = stdscr.getch()
        # For each menu option
        if c == ord('1'):
            showstatus(statuswin, rconn, "LED ON request")
            rconn.publish("control02", "ON")
            curses.doupdate()
            continue
        elif c == ord('2'):
            showstatus(statuswin, rconn, "LED OFF request")
            rconn.publish("control02", "OFF")
            curses.doupdate()
            continue
        elif c == ord('3'):
            showstatus(statuswin, rconn, "Door OPEN request")
            rconn.publish("control01", "OPEN")
            curses.doupdate()
            continue
        elif c == ord('4'):
            showstatus(statuswin, rconn, "Door CLOSE request")
            rconn.publish("control01", "CLOSE")
            curses.doupdate()
            continue
        elif c == ord('5'):
            showstatus(statuswin, rconn, "Door STOP request")
            rconn.publish("control01", "HALT")
            curses.doupdate()
            continue


        # Final menu option q for quit
        elif c == ord('q') or c == ord('Q'):
            break  # Exit the while loop

        # has a message been received by redis pubsub?
        message = pubsub.get_message()
        if message:
            # Yes it has, so show it as a status
            status_message = "Message received: " + message['data'].decode("utf-8")
            showstatus(statuswin, rconn, status_message)
            curses.doupdate()

    # Clear screen and end the program
    stdscr.clear()
    stdscr.refresh()


def showstatus(statuswin, rconn, status_message):
    "fills in the status window"
    # get led status locally
    if rconn.get('rempi01_led') == b"ON":
        led_status = "LED: ON"
    else:
        led_status = "LED: OFF"

    door = rconn.get('rempi01_door_status')
    if door is None:
        door_status = "Door: UNKNOWN"
    else:
        door_status = "Door: " + door.decode("utf-8")
    statuswin.clear()
    statuswin.box(0,0)
    statuswin.addstr(2,5,"REMScope Status:")
    statuswin.addstr(3,10,status_message)
    statuswin.addstr(4,10,led_status)
    statuswin.addstr(5,10,door_status)
    statuswin.noutrefresh()


if __name__ == "__main__":


    # create redis connection
    rconn = StrictRedis(host='localhost', port=6379)

    pubsub = rconn.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('alert01')
    pubsub.subscribe('alert02')

    # start the curses screen
    curses.wrapper(main, rconn, pubsub)


