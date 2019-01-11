# If comunications recieved by mqtt for hardware input or output

# can set outputs and
# reply by publishing the status

import logging

from .. import hardware


def from_topic():
    "Returns a string 'From_name' where name is the hardware name of this device"
    return 'From_' + hardware.get_name()


def status_request(mqtt_client, proj_data, message=''):
    "Request received for general status request"
    # call each pin status in turn
    output01_status(mqtt_client, proj_data, message)
    input_names = hardware.get_input_names()
    for name in input_names:
        input_status(name, mqtt_client, message)


###### INPUTS ######


def read(mqtt_client, message):
    "Deals with a request to read a specific Input"
    payload = message.payload.decode("utf-8")
    if message.topic == 'From_WebServer/Inputs/input01':
        if payload == "status_request":
            input_status('input01', mqtt_client, message)
    if message.topic == 'From_WebServer/Inputs/input02':
        if payload == "status_request":
            input_status('input02', mqtt_client, message)
    if message.topic == 'From_WebServer/Inputs/input03':
        if payload == "status_request":
            input_status('input03', mqtt_client, message)


def input_status(input_name, mqtt_client, message=''):
    """If a request for an input status has been received, respond to it"""
    if mqtt_client is None:
        return
    value = hardware.get_input(input_name)
    topic = from_topic() + '/Inputs/' + input_name
    try:
        if value is None:
            logging.info("Status %s : UNKNOWN", input_name)
            mqtt_client.publish(topic=topic, payload='UNKNOWN')
        elif value is True:
            logging.info("Status %s : ON", input_name)
            mqtt_client.publish(topic=topic, payload='ON')
        elif value is False:
            logging.info("Status %s : OFF", input_name)
            mqtt_client.publish(topic=topic, payload='OFF')
        else:
            # could be string, integer or float
            logging.info("Status %s : %s", input_name, str(value))
            mqtt_client.publish(topic=topic, payload=str(value))
    except Exception:
        logging.error("Failed to publish input status via MQTT")


###### OUTPUTS ######


def action(mqtt_client, proj_data, message):
    "Sets outputs when message received via MQTT"
    payload = message.payload.decode("utf-8")
    # wait until a lock is aquired, then set output while blocking anyone else
    with proj_data['lock']:
        if (message.topic == 'From_WebServer/Outputs/output01') or (message.topic == 'From_ServerEngine/Outputs/output01'):
            if payload == "ON":
                output01_ON(proj_data, mqtt_client)
            elif payload == "OFF":
                output01_OFF(proj_data, mqtt_client)
            else:
                output01_status(mqtt_client, proj_data, message)


def output_status(output_name, mqtt_client, proj_data, message=''):
    """If a request for an output status has been received, respond to it"""
    if mqtt_client is None:
        return
    if output_name == 'output01':
        output01_status(mqtt_client, proj_data, message)
    # add elif's as further outputs defined



# Functions are provided for each individual output

###### output01 #####

def output01_status(mqtt_client, proj_data, message=''):
    """If a request for output01 status has been received,
       check gpio pins and respond to it"""
    try:
        if mqtt_client is None:
            return
        hardvalue = hardware.get_boolean_output("output01")
        # if unable to get pin output, respond with state store value
        # primarily for test usage on a none-raspberry pi pc
        if hardvalue is None:
            hardvalue = proj_data['door'].output01
        topic = from_topic() + '/Outputs/output01'
        if hardvalue:
            logging.info("Status output01 : ON")
            mqtt_client.publish(topic=topic, payload='ON')
        else:
            logging.info("Status output01 : OFF")
            mqtt_client.publish(topic=topic, payload='OFF')
    except Exception:
        # return without action if any failure occurs
        logging.error("Failed to publish output01 status via MQTT")


def output01_ON(proj_data, mqtt_client=None):
    "set output01 pin high"
    try:
        hardware.set_boolean_output("output01", True)
        # Set output value in the state 'door'
        proj_data['door'].output01 = True
        # respond with output01 status
        if mqtt_client is not None:
            output01_status(mqtt_client, proj_data)
    except Exception:
        # return without action if any failure occurs
        return


def output01_OFF(proj_data, mqtt_client=None):
    "set output01 pin low"
    try:
        hardware.set_boolean_output("output01", False)
        # Set output value in the state 'door'
        proj_data['door'].output01 = False
        # respond with output01 status
        if mqtt_client is not None:
            output01_status(mqtt_client, proj_data)
    except Exception:
        # return without action if any failure occurs
        return



