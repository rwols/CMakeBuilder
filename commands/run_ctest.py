import Default.exec
from CMakeBuilder.support import get_setting
from .command import ServerManager


class CmakeRunCtestCommand(Default.exec.ExecCommand):
    """Runs CTest in a console window."""

    def is_enabled(self):
        self.server = ServerManager.get(self.window)
        return self.server is not None

    @classmethod
    def description(cls):
        return 'Run CTest'

    def run(self, test_framework='boost'):
        cmd = 'ctest'
        command_line_args = get_setting(self.window.active_view(),
                                        'ctest_command_line_args')
        if command_line_args:
            cmd += ' ' + command_line_args
        # TODO: check out google test style errors, right now I just assume
        # everybody uses boost unit test framework

        regex = r'(.+[^:]):(\d+):() (?:fatal )?((?:error|warning): .+)$'

        super().run(
            shell_cmd=cmd,
            # Guaranteed to exist at this point.
            working_dir=self.server.cmake.build_folder,
            file_regex=regex,
            syntax='Packages/CMakeBuilder/Syntax/CTest.sublime-syntax')

    def on_finished(self, proc):
        super().on_finished(proc)
