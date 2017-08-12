from .command import CmakeCommand, ServerManager


class CmakeSwitchSchemeCommand(CmakeCommand):

    def run(self):
        ServerManager._servers.pop(self.window.id(), None)
        ServerManager.on_load(self.window.active_view())

    def description(self):
        return "Switch Scheme"
