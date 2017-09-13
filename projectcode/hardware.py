
# _OUTPUTS

# This dictionary has keys output names, and values being a tuple of (type, value, onpower, BCM number)
# where type is one of 'text', 'boolean', 'integer'
# value is the default value to put in the database when first created
# onpower is True if the 'default value' is to be set on power up, or False if last recorded value is to be used
# BCM number is the appropriate BCM pin number, or None if not relevant

# Currently only one output 'output01' on BCM 24 is defined

_OUTPUTS = {"output01" : ('boolean', False, True, 24)}


# _INPUTS

# This dictionary has keys inpuput names, and values being a tuple of (type, pud, BCM number)
# where type is one of 'text', 'boolean', 'integer', 'float'
# pud, pull up down is True for pull up, False for pull down, None if not relevant
# BCM number is the appropriate BCM pin number, or None if not relevant

# Currently two inputs are defined
# 'input01' is the server time
# 'input02' is the input on BCM 23

_INPUTS = {"input01" : ('boolean', True, 23),
           "input02" : ('text', None, None)           
          }



import time

# import RPi.GPIO
_gpio_control = True
try:
    import RPi.GPIO as GPIO            # import RPi.GPIO module  
except:
    _gpio_control = False


def initial_setup_outputs():
    "Returns True if successfull, False if not"
    if not _gpio_control:
        return False
    GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD
    for bcm in _OUTPUTS.values():
        # set outputs
        if bcm[3] is not None: 
            GPIO.setup(bcm[3], GPIO.OUT)
    for bcm in _INPUTS.values():
        # set inputs
        if bcm[2] is not None:
            if bcm[1]:
                GPIO.setup(bcm[2], GPIO.IN, pull_up_down = GPIO.PUD_UP)
            else:
                GPIO.setup(bcm[2], GPIO.IN, pull_up_down = GPIO.PUD_DOWN)


def get_output_names():
    "Returns list of output names, the list is sorted by boolean, integer and text items, and in name order within these categories"
    bool_list = sorted(name for name in _OUTPUTS if _OUTPUTS[name][0] == 'boolean')
    int_list =  sorted(name for name in _OUTPUTS if _OUTPUTS[name][0] == 'integer')
    text_list = sorted(name for name in _OUTPUTS if _OUTPUTS[name][0] == 'text')
    controls_list = []
    if bool_list:
        controls_list.extend(bool_list)
    if int_list:
        controls_list.extend(int_list)
    if text_list:
        controls_list.extend(text_list)
    return controls_list


def get_outputs():
    return _OUTPUTS.copy()


def get_output_type(name):
    "Given an output name, returns the output type, or None if the name is not found"
    if name in _OUTPUTS:
        return _OUTPUTS[name][0]


def get_boolean_output(name):
    "Given an output name, return True or False for the state of the output, or None if name not found, or not boolean, or _gpio_control is False"
    if not _gpio_control:
        return
    if name not in _OUTPUTS:
        return
    if _OUTPUTS[name][0] != 'boolean':
        return
    return bool(GPIO.input(_OUTPUTS[name][3]))


def set_boolean_output(name, value):
    "Given an output name, sets the output pin"
    if not _gpio_control:
        return
    if name not in _OUTPUTS:
        return
    if _OUTPUTS[name][0] != 'boolean':
        return
    if value:
        GPIO.output(_OUTPUTS[name][3], 1)
    else:
        GPIO.output(_OUTPUTS[name][3], 0)



def get_input_names():
    "Returns list of input names, the list is sorted by boolean, integer, float and text items, and in name order within these categories"
    bool_list = sorted(name for name in _INPUTS if _INPUTS[name][0] == 'boolean')
    int_list =  sorted(name for name in _INPUTS if _INPUTS[name][0] == 'integer')
    float_list =  sorted(name for name in _INPUTS if _INPUTS[name][0] == 'float')
    text_list = sorted(name for name in _INPUTS if _INPUTS[name][0] == 'text')
    sensors_list = []
    if bool_list:
        sensors_list.extend(bool_list)
    if int_list:
        sensors_list.extend(int_list)
    if float_list:
        sensors_list.extend(float_list)
    if text_list:
        sensors_list.extend(text_list)
    return sensors_list

def get_inputs():
    return _INPUTS.copy()


def get_input_type(name):
    "Given an input name, returns the input type, or None if the name is not found"
    if name in _INPUTS:
        return _INPUTS[name][0]


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
