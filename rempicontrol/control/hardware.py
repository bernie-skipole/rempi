


_CONFIG = { 
            'DS18B20': '28-000007e4291f'     # Edit for the correct temperature sensor chip DS18B20
          }


# _OUTPUTS

# This dictionary has keys output names, and values being a tuple of (type, value, BCM number, description)
# where type is one of 'text', 'boolean', 'integer'
# value is the power on value
# BCM number is the appropriate BCM pin number, or None if not relevant

# Currently only one output 'output01' on BCM 24 is defined

_OUTPUTS = {"output01" : ('boolean', False, 24, "BCM 24 - When ON lights an LED")}


# _INPUTS

# This dictionary has keys input names, and values being a tuple of (type, pud, BCM number, description)
# where type is one of 'text', 'boolean', 'integer', 'float'
# pud, pull up down is True for pull up, False for pull down, None if not relevant
# BCM number is the appropriate BCM pin number, or None if not relevant


_INPUTS = {"input01" : ('boolean', True, 23, "BCM 23 - Limit switch, when ON the door is open"),
           "input02" : ('text', None, None, "Server UTC time"),
           "input03" : ('float', None, None, "Temperature")         
          }



import time, random, logging

_gpio_control = True
try:
    import RPi.GPIO as GPIO            # import RPi.GPIO module  
except Exception:
    _gpio_control = False



def initial_setup_outputs():
    "Returns True if successfull, False if not"
    if not _gpio_control:
        return False
    GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD
    for bcm in _OUTPUTS.values():
        # set outputs
        if bcm[2] is not None: 
            GPIO.setup(bcm[2], GPIO.OUT)
    for bcm in _INPUTS.values():
        # set inputs
        if bcm[2] is not None:
            if bcm[1]:
                GPIO.setup(bcm[2], GPIO.IN, pull_up_down = GPIO.PUD_UP)
            else:
                GPIO.setup(bcm[2], GPIO.IN, pull_up_down = GPIO.PUD_DOWN)




def get_boolean_output(name):
    "Given an output name, return True or False for the state of the output, or None if name not found, or not boolean, or _gpio_control is False"
    if not _gpio_control:
        return
    if name not in _OUTPUTS:
        return
    if _OUTPUTS[name][0] != 'boolean':
        return
    return bool(GPIO.input(_OUTPUTS[name][2]))


def get_boolean_power_on_value(name):
    "Given an output name, return True or False for the power on value of the output, or None if name not found, or not boolean"
    if name not in _OUTPUTS:
        return
    if _OUTPUTS[name][0] != 'boolean':
        return
    return _OUTPUTS[name][1]


def set_boolean_output(name, value):
    "Given an output name, sets the output pin"
    if not _gpio_control:
        return
    if name not in _OUTPUTS:
        return
    if _OUTPUTS[name][0] != 'boolean':
        return
    try:
        if (value is True) or (value == 'True') or (value == 'ON'):
            GPIO.output(_OUTPUTS[name][2], 1)
            logging.info("Output %s set ON : %s", name, _OUTPUTS[name][3])
        else:
            GPIO.output(_OUTPUTS[name][2], 0)
            logging.info("Output %s set OFF : %s", name, _OUTPUTS[name][3])
    except Exception:
        logging.error("Unable to set output %s, BCM %s", name, _OUTPUTS[name][2])
        # re raise the exception to indicate to caller that this has failed
        raise


def get_input(name):
    "Given an input name, returns the value, or None if the name is not found"
    if name not in _INPUTS:
        return
    input_type = _INPUTS[name][0]
    if input_type == 'boolean':
        return get_boolean_input(name)
    if input_type == 'text':
        return get_text_input(name)
    if input_type == 'float':
        return get_float_input(name)



def get_boolean_input(name):
    "Given an input name, return True or False for the state of the input, or None if name not found, or not boolean, or _gpio_control is False"
    if not _gpio_control:
        return
    if name not in _INPUTS:
        return
    if _INPUTS[name][0] != 'boolean':
        return
    return bool(GPIO.input(_INPUTS[name][2]))


def get_text_input(name):
    "Returns text input for the appropriate input, or empty string if no text found"
    if name not in _INPUTS:
        return ''
    if _INPUTS[name][0] != 'text':
        return ''
    if name == "input02":
        # This input returns a time string
        return time.strftime("%c", time.gmtime())
    return ''


def get_float_input(name):
    "Returns float input for the appropriate input, or None if no input found"
    if name not in _INPUTS:
        return
    if _INPUTS[name][0] != 'float':
        return
    if name == "input03":
        # This input returns a temperature value
        return get_temperature()
    return


def get_input_name(bcm):
    "Given a bcm number, returns the name"
    if bcm is None:
        return
    for name, values in _INPUTS.items():
        if values[2] == bcm:
            return name


class Listen(object):
    """Listens for input pin changes. You should define a callback function
       mycallback(name, userdata)

       where name will be the input name triggered,
       and userdata will be the variable you pass to this Listen object. 

       useage
       listen = Listen(mycallback, userdata)
       listen.start_loop()

       This will then use the threaded interrupt facilities of RPi.GPIO
       to call the callback when one of the inputs falls (if pud True)
       or rises (if pud False), each with a 300ms bounce time
      
    """ 

    def __init__(self, callbackfunction, userdata):
        self.set_callback = callbackfunction
        self.userdata = userdata


    def _pincallback(self, channel):
        """This is the callback added to each pin, in turn it calls
           callbackfunction(name, proj_data)"""
        name = get_input_name(channel)
        self.set_callback(name, self.userdata)

    def start_loop(self):
        "Sets up listenning threads"
        if not _gpio_control:
            return
        for name, values in _INPUTS.items():
            if (values[0] == 'boolean') and isinstance(values[2], int):
                if values[1]:
                    # True for pull up pin, therefore detect falling edge
                    GPIO.add_event_detect(values[2], GPIO.FALLING, callback=self._pincallback, bouncetime=300)
                else:
                    GPIO.add_event_detect(values[2], GPIO.RISING, callback=self._pincallback, bouncetime=300)


####### temperature controller #######

def get_temperature():
    "Returns temperature from probe as floating point number, Returns RuntimeError on failure"

    if not _gpio_control:
        # presumably not running on a raspbery pi
        # for testing purposes, return a fake value
        # a random number with mean 6, std dev 2.0
        return random.normalvariate(6,2.0)

    temp_sensor = "/sys/bus/w1/devices/" + _CONFIG['DS18B20'] + "/w1_slave"
    try:
        with open(temp_sensor, 'r') as f:
            lines = f.readlines()
    except Exception:
        raise RuntimeError("Unable to open %s" % (temp_sensor,))
    if lines[0].strip()[-3:] != 'YES':
        raise RuntimeError("Unable to parse %s" % (temp_sensor,))
    temp_output = lines[1].find('t=')
    if temp_output == -1:
        raise RuntimeError("Unable to parse %s" % (temp_sensor,))
    temp_string = lines[1].strip()[temp_output+2:]
    return float(temp_string) / 1000.0


