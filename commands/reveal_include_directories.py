from .command import CmakeCommand


class CmakeRevealIncludeDirectories(CmakeCommand):
    """Prints the include directories to a new view"""

    def run(self):
        view = self.window.new_file()
        view.set_name("Project Include Directories")
        view.set_scratch(True)
        for path in self.server.include_paths:
            view.run_command("append", {"characters": path + "\n", "force": True})

    @classmethod
    def description(cls):
        return "Reveal Include Directories"
