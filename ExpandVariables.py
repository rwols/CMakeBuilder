import string
def expand_variables(the_dict, the_vars):
    for key, value in the_dict.items():
        if isinstance(value, dict):
            expand_variables(value, the_vars)
        elif isinstance(value, str):
            the_dict[key] = string.Template(value).substitute(the_vars)
        else:
            continue
