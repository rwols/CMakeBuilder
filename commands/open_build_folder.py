import sublime, sublime_plugin, os
from CMakeBuilder.support import *

class CmakeOpenBuildFolderCommand(sublime_plugin.WindowCommand):
    """Opens the build folder."""

    def is_enabled(self):
        try:
            build_folder = self.window.project_data()["settings"]["cmake"]["build_folder"]
            build_folder = sublime.expand_variables(build_folder, self.window.extract_variables())
            return os.path.exists(build_folder)
        except Exception as e:
            return False

    @classmethod
    def description(cls):
        return 'Browse Build Folder…'

    def run(self):
        build_folder = self.window.project_data()["settings"]["cmake"]["build_folder"]
        build_folder = sublime.expand_variables(build_folder, self.window.extract_variables())
        self.window.run_command('open_dir', args={'dir': os.path.realpath(build_folder)})
