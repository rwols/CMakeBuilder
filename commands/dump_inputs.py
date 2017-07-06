from .command import CmakeCommand


class CmakeDumpInputsCommand(CmakeCommand):
    """Prints the cmake inputs to a new view"""
    
    def run(self):
        self.server.cmake_inputs()

    def description(self):
        return "Dump CMake Inputs"
