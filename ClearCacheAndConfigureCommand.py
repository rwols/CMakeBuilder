import sublime, sublime_plugin, os
from .ExpandVariables import *

class CmakeClearCacheAndConfigureCommand(sublime_plugin.WindowCommand):
    """Clears the CMake-generated files, and then configures the project."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        cmake = project.get('cmake')
        if cmake is None:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            return False
        build_folder = cmake.get('build_folder')
        if not build_folder:
            return False
        return True

    def description(self):
        return 'Clear Cache And Configure'

    def run(self):
        self.window.run_command('cmake_clear_cache', args={'with_confirmation': False})
        self.window.run_command('cmake_configure', args={'write_build_targets': False})
