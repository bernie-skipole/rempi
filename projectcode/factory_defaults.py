# default output values
# This dictionary has keys output names, and values being a tuple of (type, value, onpower)
# where type is one of 'text', 'boolean', 'integer'
# value is the default value to put in the database when first created
# onpower is True if the 'default value' is to be set on power up, or False if last recorded value is to be used

_OUTPUTS = {"output01" : ('boolean', False, True)}



def get_output_names():
    "Returns list of output names, the list is sorted by boolean, integer and text items, and in name order within these categories"
    global _OUTPUTS
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
    global _OUTPUTS
    return _OUTPUTS.copy()


def get_output_type(name):
    "Given an output name, returns the output type, or None if the name is not found"
    if name in _OUTPUTS:
        return _OUTPUTS[name][0] 
