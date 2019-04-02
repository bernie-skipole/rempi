# Get the system status

import sys

from collections import namedtuple

_mqtt_mod = True
try:
    import paho.mqtt.client as mqtt
except Exception:
    _mqtt_mod = False

from . import cfg

# initially assume no mqtt connection
_mqtt_connected = False


SysStatus = namedtuple('SysStatus', ['network', 'led'])

NETWORK_STATUS = 'Lost communications'
LED_STATUS = 'Unknown'
NETWORK_KEEPALIVE = 0

def get_system_status():
    "Returns a SysStatus named tuple of the system status"
    sys_status = SysStatus(NETWORK_STATUS, LED_STATUS)
    return sys_status


def set_network_status(network_status):
    "Sets the network status"
    global NETWORK_STATUS, NETWORK_KEEPALIVE
    NETWORK_STATUS = network_status
    NETWORK_KEEPALIVE = 0


def set_led_status(led_status):
    "Sets the LED status"
    global LED_STATUS
    LED_STATUS = led_status




################# set up MQTT client #############################

def _on_message(client, userdata, message):
    "Callback when a message is received"
    if message.topic == 'From_RemPi01/Outputs/led':
        led_status = message.payload.decode("utf-8")
        set_led_status(led_status)
        set_network_status('OK')


# The callback for when the client receives a CONNACK response from the server.
def _on_connect(client, userdata, flags, rc):
    global _mqtt_connected
    if rc != 0:
        # client not connected
        _mqtt_connected = False
        set_network_status("Unable to connect to Server")
        return
    _mqtt_connected = True
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # subscribe to topics "From_RemPi01/" and all subtopics
    client.subscribe( "From_RemPi01/#" )
    set_network_status("Connected to main Server")


def _on_disconnect(client, userdata, rc):
    global _mqtt_connected
    _mqtt_connected = False
    set_network_status("Disconnected from Server")


def create_mqtt(mqtt_ip, mqtt_port=1883, mqtt_username='', mqtt_password=''):
    """Creates an mqtt client,
       with the mqtt client subscribed to From_RemPi01/#
       and running a threaded loop
       and with an on_message callback that calls further functions
       within this package, returns the client, or None on failure"""

    if not _mqtt_mod:
        print("Module paho.mqtt.client not found", file=sys.stderr)
        return

    try:
        # create an mqtt client instance
        mqtt_client = mqtt.Client()

        # attach callback function to client
        mqtt_client.on_connect = _on_connect
        mqtt_client.on_disconnect = _on_disconnect
        mqtt_client.on_message = _on_message

        # If a username/password is set on the mqtt server
        if mqtt_username and mqtt_password:
            mqtt_client.username_pw_set(username = mqtt_username, password = mqtt_password)
        elif mqtt_username:
            mqtt_client.username_pw_set(username = mqtt_username)

        # connect to the server
        mqtt_client.connect(host=mqtt_ip, port=mqtt_port)

        # start a threaded loop
        mqtt_client.loop_start()
    except Exception as e:
        return

    return mqtt_client

   
def increment_network_keepalive():
    """Increments NETWORK_KEEPALIVE, if not reset by a call to set_network_status, then after eight increments
       this will cause a 'No Reply from REMPI' to be set."""
    global NETWORK_KEEPALIVE
    if NETWORK_KEEPALIVE > 8:
        set_network_status("No Reply from REMPI")
        set_led_status("Unknown")
    else:
        NETWORK_KEEPALIVE += 1


def request_status(MQTT_CLIENT):
    "send an MQTT message requesting status"
    topic = "From_" + cfg.get_name() + "/status"
    result = MQTT_CLIENT.publish(topic=topic, payload='led')
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        set_network_status("Server communications failed")
    else:
        # the sending succeeded, but possibly no reply from REMPI
        # This increments a keepalive, which if not reset by getting an answer
        # will set an error status
        increment_network_keepalive()


def send_led_on(MQTT_CLIENT):
    "Sends led on signal"
    topic = "From_" + cfg.get_name() + "/Outputs/led"
    result = MQTT_CLIENT.publish(topic=topic, payload="ON")
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        set_network_status("Server communications failed")
    else:
        set_network_status("LED ON command transmitted")


def send_led_off(MQTT_CLIENT):
    "Sends led off signal"
    topic = "From_" + cfg.get_name() + "/Outputs/led"
    result = MQTT_CLIENT.publish(topic=topic, payload="OFF")
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        set_network_status("Server communications failed")
    else:
        set_network_status("LED OFF command transmitted")



