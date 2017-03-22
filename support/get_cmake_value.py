import sublime

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
