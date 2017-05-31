__version__ = "0.11.0"
__version_info__ = (0,11,0)

import sublime
import sublime_plugin
import subprocess
import os
import json
from CMakeBuilder.commands import *
from CMakeBuilder.event_listeners import *

#--- REMOVE THIS LATER -------------------------------------------------------

class DictionaryMigrator(sublime_plugin.EventListener):
    """Migrates the cmake dict from the top-level to the settings."""
    
    def on_activated(self, view):
        if view.settings().get("_cmake_dont_ask_about_migration", False): return
        project_data = view.window().project_data()
        if not project_data: return
        cmake = project_data.pop("cmake", None)
        if not cmake: return
        sublime.set_timeout(lambda: view.run_command("cmake_dict_migrate"), 1000)

class CmakeDictMigrateCommand(sublime_plugin.TextCommand):
    """Does the actual migration."""
    def run(self, edit):
        self.view.settings().set("_cmake_dont_ask_about_migration", True)
        if sublime.ok_cancel_dialog("Since version 0.11.0 of CMakeBuilder the cmake dictionary needs to be in the settings dictionary of your project file. Click Migrate to auto-migrate, or Cancel to do nothing.\n\nNOTE: If it takes a long time, Sublime will probably start crashing. Just restart and everything should be okay."):
            window = self.view.window()
            filename = window.project_file_name()
            if not filename:
                sublime.error_message("Could not determine the filename of the project.")
                return
            data = window.project_data()
            cmake = data.pop("cmake", None)
            if cmake:
                if not data.get("settings", None): data["settings"] = {}
                data["settings"]["cmake"] = cmake
                self.view.window().set_project_data(data)
            self.view.window().open_file(filename)
            self.view.window().run_command("cmake_diagnose")
