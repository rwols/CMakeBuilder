import sublime, sublime_plugin, os
from ..support import *

class CmakeOpenBuildFolderCommand(sublime_plugin.WindowCommand):
    """Opens the build folder."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        project_file_name = self.window.project_file_name()
        if not project_file_name:
            return False
        cmake = project.get('cmake')
        if not cmake:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            return False
        build_folder = cmake.get('build_folder')
        if not build_folder:
            return False
        if os.path.exists(build_folder):
            return True
        else:
            return False

    def description(self):
        return 'Browse Build Folder…'

    def run(self):
        project = self.window.project_data()
        cmake = project.get('cmake')
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        build_folder = cmake.get('build_folder')
        self.window.run_command(
            'open_dir', args={'dir': os.path.realpath(build_folder)})
