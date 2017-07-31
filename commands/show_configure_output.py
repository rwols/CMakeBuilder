from .command import CmakeCommand


class CmakeShowConfigureOutputCommand(CmakeCommand):

    def run(self):
        self.window.run_command("show_panel",
                                {"panel": "output.cmake.configure"})

    @classmethod
    def description(cls):
        return "Show Configure Output"
