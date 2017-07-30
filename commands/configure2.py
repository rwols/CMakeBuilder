from .command import CmakeCommand


class CmakeConfigure2Command(CmakeCommand):

    def run(self):
        self.server.configure(self.server.cmake.command_line_overrides)
