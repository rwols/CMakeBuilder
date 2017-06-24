__version__ = "1.0.0"
__version_info__ = (1,0,0)

import sublime
import sublime_plugin
import subprocess
import os
import json
from CMakeBuilder.commands import *
from CMakeBuilder.event_listeners import *
