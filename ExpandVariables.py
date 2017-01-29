import sublime, string, platform

def expand_variables(the_dict, the_vars):
    # Not gonna work in combination with build_system => working_dir
    # So this is commented out for now.
    # the_vars['machine'] = platform.machine()
    # the_vars['processor'] = platform.processor()
    return _expand_variables_recursive(the_dict, the_vars)

def _expand_variables_recursive(the_dict, the_vars):
    for key, value in the_dict.items():
        if isinstance(value, dict):
            value = expand_variables(value, the_vars)
        elif isinstance(value, str):
            the_dict[key] = string.Template(value).substitute(the_vars)
        else:
            continue
    return the_dict

