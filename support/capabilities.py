from .check_output import check_output
import json
import sublime

_capabilities = None


def plugin_loaded():
    settings = sublime.load_settings("CMakeBuilder.sublime-settings")
    settings.add_on_change("CMakeBuilder", _reload_capabilities)
    _reload_capabilities()


def _reload_capabilities():
    global _capabilities
    try:
        print("loading settings")
        settings = sublime.load_settings("CMakeBuilder.sublime-settings")
        print("fetching cmake binary")
        cmake = settings.get("cmake_binary", "cmake")
        command = "{} -E capabilities".format(cmake)
        print("running", command)
        output = check_output(command)
        _capabilities = json.loads(output)
    except Exception as e:
        sublime.error_message("There was an error loading cmake's "
                              "capabilities. Your \"cmake_binary\" setting is "
                              "set to \"{}\". Please make sure that this "
                              "points to a valid cmake executable."
                              .format(cmake))
        print(str(e))
        _capabilities = {"error": None}


def capabilities(key):
    global _capabilities
    if _capabilities is None:
        raise KeyError("Capabilities called too early!")
    elif "error" in _capabilities:
        raise ValueError("Error loading capabilities")
    else:
        return _capabilities.get(key, None)
