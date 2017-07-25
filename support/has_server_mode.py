from .check_output import check_output
import json

_server_mode = None


def has_server_mode():
    global _server_mode
    if _server_mode is None:
        try:
            output = check_output("cmake -E capabilities")
        except Exception as e:
            print("CMakeBuilder: Error: Could not load cmake's capabilities")
            _server_mode = False
        else:
            output = json.loads(output)
            _server_mode = output.get("serverMode", False)
    return _server_mode
