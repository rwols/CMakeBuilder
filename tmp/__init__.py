import sublime
import sys
import os
import glob
from ..support import *

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
        assert self.build_folder_pre_expansion
        windowvars = self.window.extract_variables()
        expand_variables(self.cmake, windowvars)
        self.build_folder = self.get_cmake_key('build_folder')
        self.filter_targets = self.get_cmake_key('filter_targets')
        self.command_line_overrides = self.get_cmake_key('command_line_overrides')
        assert self.build_folder

    def __repr__(self):
        return repr(type(self))

    def env(self):
        return {} # Empty dict

    def variants(self):
        return [] # Empty list

    def on_pre_configure(self):
        pass

    def on_post_configure(self, exit_code):
        pass

    def get_build_invocation(self, **kwargs):
        raise NotImplemented()

    def create_sublime_build_system(self):
        build_system = {
            'name': os.path.splitext(os.path.basename(self.window.project_file_name()))[0],
            'shell_cmd': self.shell_cmd(), 
            'working_dir': self.build_folder_pre_expansion,
            'variants': self.variants()
        }
        file_regex = self.file_regex()
        if file_regex:
            build_system['file_regex'] = file_regex
        syntax = self.syntax()
        if syntax:
            build_system['syntax'] = syntax
        env = self.env()
        if env:
            build_system['env'] = env
        return build_system

    def shell_cmd(self):
        return 'cmake --build .'

    def syntax(self):
        return None

    def file_regex(self):
        return None

    def get_cmake_key(self, key):
        if self.cmake_platform:
            if key in self.cmake_platform:
                return self.cmake_platform[key]
        if key in self.cmake:
            return self.cmake[key]
        else:
            return None

    def expand_vars(self, dict_or_string):
        windowvars = self.window.extract_variables()
        return expand_variables(dict_or_string, windowvars)

def get_generator_module_prefix():
    return 'CMakeBuilder.generators.' + sublime.platform() + '.'

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

def class_from_generator_string(generator_string):
    if not generator_string:
        if sublime.platform() == 'linux': 
            generator_string = 'Unix Makefiles'
        elif sublime.platform() == 'osx':
            generator_string = 'Unix Makefiles'
        elif sublime.platform() == 'windows':
            generator_string = 'Visual Studio'
        else:
            sublime.error_message('Unknown sublime platform: {}'.format(sublime.platform()))
            return
    module_name = get_module_name(generator_string)
    if not module_name in sys.modules:
        valid_generators = get_valid_generators()
        sublime.error_message('CMakeBuilder: "%s" is not a valid generator. The valid generators for this platform are: %s' % (generator_string, ','.join(valid_generators)))
        return
    GeneratorModule = sys.modules[module_name]
    GeneratorClass = None
    try:
        GeneratorClass = getattr(GeneratorModule, generator_string.replace(' ', '_'))
    except AttributeError:
        sublime.error_message('Internal error.')
    return GeneratorClass

def _import_all_platform_specific_generators():
    result = []
    print('CMakeBuilder: Available generators on {}:'.format(sublime.platform()))
    for file in glob.iglob(os.path.dirname(__file__) + '/' + sublime.platform() + '/*.py'):
        if not os.path.isfile(file): continue
        base = os.path.basename(file)
        if base.startswith('__'): continue
        generator = base[:-3]
        result.append(generator)
        print('\t{}'.format(generator))
    return result

if sublime.platform() == 'linux':
    from .linux import *
elif sublime.platform() == 'osx':
    from .osx import *
elif sublime.platform() == 'windows':
    from .windows import *
else:
    sublime.error_message('Unknown platform: %s' % sublime.platform())
    
