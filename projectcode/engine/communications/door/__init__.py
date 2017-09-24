from .... import hardware, database_ops


def action(client, userdata, message):
    "Deals with Door topics"
    payload = message.payload.decode("utf-8")
    if message.topic == 'From_WebServer/Door/Status':
        handle_status_request(client, userdata, message)
    elif message.topic == 'From_ServerEngine/Door/Status':
        handle_status_request(client, userdata, message)
    elif payload == "Open":
        handle_open_request(client, userdata, message)
    elif payload == "Close":
        handle_close_request(client, userdata, message)



def handle_status_request(client, userdata, message):
    """If a request for door status has been received,
       check gpio pins and respond to it"""
    status_request = message.payload.decode("utf-8")
    # userdata is the redis connection
    # status_request is the actual message
    if status_request == "status_request":
        hardvalue = hardware.get_boolean_output("output01")
        if hardvalue is None:
            hardvalue = database_ops.get_output("output01")
        if client is None:
            return
        if hardvalue:
            client.publish(topic="From_Pi01/Door/Status", payload='Openning')
        else:
            client.publish(topic="From_Pi01/Door/Status", payload='Closing')


def handle_open_request(client, userdata, message):
    "set output01 pin high"
    hardware.set_boolean_output("output01", True)
    # Set output value in database
    database_ops.set_output("output01", True)
    if client is not None:
        client.publish(topic="From_Pi01/Door/Status", payload='open requested')

def handle_close_request(client, userdata, message):
    "set output01 pin low"
    hardware.set_boolean_output("output01", False)
    # Set output value in database
    database_ops.set_output("output01", False)
    if client is not None:
        client.publish(topic="From_Pi01/Door/Status", payload='close requested')
