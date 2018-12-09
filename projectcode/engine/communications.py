# If comunications recieved by mqtt for hardware input or output

# can set outputs and
# reply by publishing the status


from .. import hardware


def from_topic():
    "Returns a string 'From_name' where name is the hardware name of this device"
    return 'From_' + hardware.get_name()


def status_request(mqtt_client, state_values, message=''):
    "Request received for general status request"
    # call each pin status in turn
    output01_status(mqtt_client, state_values, message)
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
    if value is None:
        mqtt_client.publish(topic=topic, payload='UNKNOWN')
    elif value is True:
        mqtt_client.publish(topic=topic, payload='ON')
    elif value is False:
        mqtt_client.publish(topic=topic, payload='OFF')
    else:
        # could be string, integer or float
        mqtt_client.publish(topic=topic, payload=str(value))


###### OUTPUTS ######


def action(mqtt_client, state_values, message):
    "Deals with setting Outputs"
    payload = message.payload.decode("utf-8")
    if (message.topic == 'From_WebServer/Outputs/output01') or (message.topic == 'From_ServerEngine/Outputs/output01'):
        if payload == "ON":
            output01_ON(mqtt_client, state_values, message)
        elif payload == "OFF":
            output01_OFF(mqtt_client, state_values, message)
        else:
            output01_status(mqtt_client, state_values, message)


def output_status(output_name, mqtt_client, state_values, message=''):
    """If a request for an output status has been received, respond to it"""
    if mqtt_client is None:
        return
    if output_name == 'output01':
        output01_status(mqtt_client, state_values, message)
    # add elif's as further outputs defined



# Functions are provided for each individual output

###### output01 #####

def output01_status(mqtt_client, state_values, message=''):
    """If a request for output01 status has been received,
       check gpio pins and respond to it"""
    if mqtt_client is None:
        return
    hardvalue = hardware.get_boolean_output("output01")
    # if unable to get pin output, respond with state store value
    # primarily for test usage on a none-raspberry pi pc
    if hardvalue is None:
        hardvalue = state_values['door'].output01
    topic = from_topic() + '/Outputs/output01'
    if hardvalue:
        mqtt_client.publish(topic=topic, payload='ON')
    else:
        mqtt_client.publish(topic=topic, payload='OFF')

def output01_ON(mqtt_client, state_values, message):
    "set output01 pin high"
    hardware.set_boolean_output("output01", True)
    # Set output value in the state 'door'
    state_values['door'].output01 = True
    # respond with output01 status
    output01_status(mqtt_client, state_values)

def output01_OFF(mqtt_client, state_values, message):
    "set output01 pin low"
    hardware.set_boolean_output("output01", False)
    # Set output value in the state 'door'
    state_values['door'].output01 = False
    # respond with output01 status
    output01_status(mqtt_client, state_values)


