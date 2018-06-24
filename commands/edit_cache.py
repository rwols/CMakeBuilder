from .command import CmakeCommand


class CmakeEditCacheCommand(CmakeCommand):

    def description(self):
        return "Edit Cache..."

    def run(self):
        self.server.cache()
