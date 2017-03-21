import string
import sublime

def expand_variables(the_dict, the_vars):
    if not the_dict:
        return
    if isinstance(the_dict, str):
        return
    for key, value in the_dict.items():
        if isinstance(value, dict):
            expand_variables(value, the_vars)
        elif isinstance(value, str):
            the_dict[key] = string.Template(value).substitute(the_vars)
        else:
            continue

def get_cmake_value(the_dict, key):
    if not the_dict:
        return None
    if sublime.platform() in the_dict:
        if key in the_dict[sublime.platform()]:
            return the_dict[sublime.platform()][key]
    if key in the_dict:
        return the_dict[key]
    else:
        return None
