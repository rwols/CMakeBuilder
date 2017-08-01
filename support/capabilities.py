from .check_output import check_output
import json

_capabilities = None

def capabilities(key):
    global _capabilities
    if _capabilities is None:
        try:
            _capabilities = json.loads(check_output("cmake -E capabilities"))
        except Exception as e:
            print("CMakeBuilder: Error: Could not load cmake's capabilities")
            _capabilities = {"error": None}
    return _capabilities.get(key, None)
