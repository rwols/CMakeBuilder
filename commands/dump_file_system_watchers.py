from .command import CmakeCommand


class CmakeDumpFileSystemWatchersCommand(CmakeCommand):
    """Prints the watched files to a new view"""
    
    def run(self):
        self.server.file_system_watchers()

    def description(self):
        return "Dump File System Watchers"
