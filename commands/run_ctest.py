import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from CMakeBuilder.support import *

class CmakeRunCtestCommand(Default.exec.ExecCommand):
    """Runs CTest in a console window."""

    def is_enabled(self):
        try:
            build_folder = self.window.project_data()["settings"]["cmake"]["build_folder"]
            build_folder = sublime.expand_variables(build_folder, self.window.extract_variables())
            return os.path.exists(os.path.join(build_folder, "CMakeCache.txt"))
        except Exception as e:
            return False

    @classmethod
    def description(cls):
        return 'Run CTest'

    def run(self, test_framework='boost'):
        cmake = self.window.project_data()["settings"]["cmake"]
        cmake = sublime.expand_variables(cmake, self.window.extract_variables())
        cmd = 'ctest'
        command_line_args = get_setting(self.window.active_view(), 'ctest_command_line_args')
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
