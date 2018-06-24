import os
from .command import CmakeCommand


class CmakeOpenBuildFolderCommand(CmakeCommand):
    """Opens the build folder."""

    @classmethod
    def description(cls):
        return "Browse Build Folder..."

    def run(self):
        build_folder = self.server.cmake.build_folder
        args = {"dir": os.path.realpath(build_folder)}
        self.window.run_command("open_dir", args=args)
