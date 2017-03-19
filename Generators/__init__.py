import sublime
import sys
from ..ExpandVariables import *

class CMakeGenerator(object):
    def __init__(self, window, cmake):
        super(CMakeGenerator, self).__init__()
        self.window = window
        self.cmake = cmake
        try:
            self.cmake_platform = self.cmake[sublime.platform()]
        except Exception as e:
            self.cmake_platform = None
        self.build_folder_pre_expansion = self.get_cmake_key('build_folder')
        windowvars = self.window.extract_variables()
        ExpandVariables.expand_variables(self.cmake, windowvars)
        self.build_folder = self.get_cmake_key('build_folder')

    def __repr__(self):
        return type(self)

    def create_sublime_build_system(self):
        raise NotImplemented()

    def get_cmake_key(self, key):
        if self.cmake_platform:
            if key in self.cmake_platform:
                return self.cmake_platform[key]
        elif key in self.cmake:
            return self.cmake[key]
        else:
            return None

    def get_build_folder(self):
        return self.get_cmake_key('build_folder')

    def get_filter_targets(self):
        return self.get_cmake_key('filter_targets')

    def get_command_line_overrides(self):
        return self.get_cmake_key('command_line_overrides')

    def expand_vars(self, dict_or_string):
        windowvars = self.window.extract_variables()
        return ExpandVariables.expand_variables(dict_or_string, windowvars)

def get_generator_module_prefix():
    return 'CMakeBuilder.Generators.' + sublime.platform() + '.'

def get_module_name(generator):
    return get_generator_module_prefix() + generator.replace(' ', '_')

def is_valid_generator(generator):
    return get_module_name(generator) in sys.modules

def get_valid_generators():
    module_prefix = get_generator_module_prefix()
    valid_generators = []
    for key, value in sys.modules.items():
        if module_prefix in key:
            valid_generators.append(key[len(module_prefix):].replace('_', ' '))
    return valid_generators

if sublime.platform() == 'linux':
    print('CMakeBuilder: Generators available on linux:')
    from .linux import *
elif sublime.platform() == 'osx':
    print('CMakeBuilder: Generators available on osx:')
    from .osx import *
elif sublime.platform() == 'windows':
    print('CMakeBuilder: Generators available on windows:')
    from .windows import *
else:
    sublime.error_message('Unknown platform: %s' % sublime.platform())
    
