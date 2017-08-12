from .command import CmakeCommand, ServerManager


class CmakeSwitchSchemeCommand(CmakeCommand):

    def run(self):
        ServerManager._servers.pop(self.window.id(), None)
        ServerManager.on_activated(self.window.active_view())

    @classmethod
    def description(cls):
        return "Switch Scheme"
