import sublime
import Default.exec
from .Generators import *
from .Support import CMakeDict

class CmakeBuildCommand(Default.exec.ExecCommand):

    def run(self, **kwargs):
        cmake = CMakeDict(self.window.project_data().get('cmake'))
        ClassDefinition = class_from_generator_string(cmake.get('generator'))
        generator = ClassDefinition(self.window, cmake)
        print(kwargs)
