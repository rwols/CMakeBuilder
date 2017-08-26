from .command import CmakeCommand


class CmakeSetGlobalSettingCommand(CmakeCommand):

    def run(self):
        self.server.global_settings()

    @classmethod
    def description(cls):
        return "Set Global Setting..."
