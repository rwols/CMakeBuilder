from .command import CmakeCommand, ServerManager


class CmakeSwitchSchemeCommand(CmakeCommand):

    def run(self):
        ServerManager._servers.pop(self.window.id(), None)x
        self.window.focus_view(self.window.active_view())

    @classmethod
    def description(cls):
        return "Switch Scheme"
