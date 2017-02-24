import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from .ExpandVariables import *

class CmakeRunCtestCommand(Default.exec.ExecCommand):
    """Runs CTest in a console window."""

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
        if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
            return False
        return True

    def description(self):
        return 'Run CTest'

    def run(self, extra_args=None):
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
        # Guaranteed to exist at this point.
        build_folder = cmake.get('build_folder')
        cmd = 'ctest'
        if extra_args:
            cmd += ' ' + extra_args
        super().run(shell_cmd=cmd, working_dir=build_folder)
    
    def on_finished(self, proc):
        super().on_finished(proc)
