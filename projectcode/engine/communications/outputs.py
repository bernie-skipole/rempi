from ... import hardware, database_ops



def status_request(client, userdata, message):
    "Request received for general status request"
    # call each pin status in turn
    output01_status(client, userdata, message)
    input01_status(client, userdata, message)


###### INPUTS ######


def read(client, userdata, message):
    "Deals with readin Inputs"
    payload = message.payload.decode("utf-8")
    if (message.topic == 'From_WebServer/Inputs/input01') or (message.topic == 'From_ServerEngine/Inputs/input01'):
        if payload == "status_request":
            input01_status(client, userdata, message)


def input01_status(client, userdata, message):
    """If a request for input01 status has been received,
       check gpio pins and respond to it"""
    if client is None:
        return
    # userdata is the redis connection
    # status_request is the actual message
    hardvalue = hardware.get_boolean_input("input01")
    if hardvalue is None:
        client.publish(topic="From_Pi01/Inputs/input01", payload='UNKNOWN')
        return
    if hardvalue:
        client.publish(topic="From_Pi01/Inputs/input01", payload='ON')
    else:
        client.publish(topic="From_Pi01/Inputs/input01", payload='OFF')


###### OUTPUTS ######


def action(client, userdata, message):
    "Deals with setting Outputs"
    payload = message.payload.decode("utf-8")
    if (message.topic == 'From_WebServer/Outputs/output01') or (message.topic == 'From_ServerEngine/Outputs/output01'):
        if payload == "ON":
            output01_ON(client, userdata, message)
        elif payload == "OFF":
            output01_OFF(client, userdata, message)
        else:
            output01_status(client, userdata, message)


def output01_status(client, userdata, message):
    """If a request for output01 status has been received,
       check gpio pins and respond to it"""
    if client is None:
        return
    # userdata is the redis connection
    # status_request is the actual message
    hardvalue = hardware.get_boolean_output("output01")
    if hardvalue is None:
        hardvalue = database_ops.get_output("output01")
    if hardvalue:
        client.publish(topic="From_Pi01/Outputs/output01", payload='ON')
    else:
        client.publish(topic="From_Pi01/Outputs/output01", payload='OFF')


def output01_ON(client, userdata, message):
    "set output01 pin high"
    hardware.set_boolean_output("output01", True)
    # Set output value in database
    database_ops.set_output("output01", True)
    if client is not None:
        client.publish(topic="From_Pi01/Outputs/output01", payload='ON')

def output01_OFF(client, userdata, message):
    "set output01 pin low"
    hardware.set_boolean_output("output01", False)
    # Set output value in database
    database_ops.set_output("output01", False)
    if client is not None:
        client.publish(topic="From_Pi01/Outputs/output01", payload='OFF')


