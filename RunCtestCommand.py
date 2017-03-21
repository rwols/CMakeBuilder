import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from .ExpandVariables import *

class CmakeRunCtestOldCommand(Default.exec.ExecCommand):
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

    def run(self, extra_args=None, test_framework='boost'):
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

        regex = r'(.+[^:]):(\d+):() (?:fatal )?((?:error|warning): .+)$'
        #TODO: check out google test style errors, right now I just assume
        #      everybody uses boost unit test framework

        SYNTAX = 'Packages/CMakeBuilder/Syntax/CTest.sublime-syntax'
        super().run(shell_cmd=cmd, 
            working_dir=build_folder, 
            file_regex=regex,
            syntax=SYNTAX)
    
    def on_finished(self, proc):
        super().on_finished(proc)

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

    def run(self, test_framework='boost'):
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
        cmd = 'ctest'
        settings = sublime.load_settings('CMakeBuilder.sublime-settings')
        command_line_args = settings.get('ctest_command_line_args', None)
        if command_line_args:
            cmd += ' ' + command_line_args
        #TODO: check out google test style errors, right now I just assume
        #      everybody uses boost unit test framework
        super().run(shell_cmd=cmd, 
            # Guaranteed to exist at this point.
            working_dir=cmake.get('build_folder'), 
            file_regex=r'(.+[^:]):(\d+):() (?:fatal )?((?:error|warning): .+)$',
            syntax='Packages/CMakeBuilder/Syntax/CTest.sublime-syntax')
    
    def on_finished(self, proc):
        super().on_finished(proc)
