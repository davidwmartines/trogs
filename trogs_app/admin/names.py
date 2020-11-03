import re

def safe_obj_name(val):
    return re.sub(r'\W+', '', val.lower().replace(' ', '_').replace('-', '_')).replace("_", "-")
