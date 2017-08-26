import sublime
import sublime_plugin
import os
from .command import CmakeCommand
from ..support import capabilities


if capabilities("serverMode"):


    class CmakeEditCacheCommand(CmakeCommand):

        def description(self):
            return "Edit Cache..."

        def run(self):
            self.server.cache()

else:


    class CmakeEditCacheCommand(sublime_plugin.WindowCommand):

        """Edit an entry from the CMake cache."""
        def is_enabled(self):
            try:
                build_folder = self.window.project_data()["settings"]["cmake"]["build_folder"]
                build_folder = sublime.expand_variables(build_folder, self.window.extract_variables())
                return os.path.exists(os.path.join(build_folder, "CMakeCache.txt"))
            except Exception as e:
                return False

        def description(self):
            return "Edit Cache..."

        def run(self):
            build_folder = self.window.project_data()["settings"]["cmake"]["build_folder"]
            build_folder = sublime.expand_variables(build_folder, self.window.extract_variables())
            self.window.open_file(os.path.join(build_folder, "CMakeCache.txt"))
            self.window.run_command("show_overlay", args={"overlay": "goto", "text": "@"})
