from .command import CmakeCommand


class CmakeDumpFileSystemWatchersCommand(CmakeCommand):
    """Prints the watched files to a new view"""

    def run(self):
        self.server.file_system_watchers()

    @classmethod
    def description(cls):
        return "Dump File System Watchers"
