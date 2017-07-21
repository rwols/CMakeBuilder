from .command import CmakeCommand


class CmakeSetGlobalSettingCommand(CmakeCommand):

    def run(self):
        self.server.global_settings()
