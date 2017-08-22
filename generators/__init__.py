import sublime
import sys
import os
import glob
from CMakeBuilder.support import get_setting


class CMakeGenerator(object):

    @classmethod
    def create(cls, window):
        """Factory method to create a new CMakeGenerator object from a sublime
        Window object."""
        data = window.project_data()["settings"]["cmake"]
        generator_str = data.get("generator", None)
        if not generator_str:
            if sublime.platform() in ("linux", "osx"):
                generator_str = "Unix Makefiles"
            elif sublime.platform() == "windows":
                generator_str = "Visual Studio"
            else:
                raise AttributeError(
                    "unknown sublime platform: %s" % sublime.platform())
        GeneratorClass = class_from_generator_string(generator_str)
        return GeneratorClass(window)

    def __init__(self, window):
        super(CMakeGenerator, self).__init__()
        data = window.project_data()["settings"]["cmake"]
        self.build_folder_pre_expansion = data["build_folder"]
        data = sublime.expand_variables(data, window.extract_variables())
        self.build_folder = self._pop(data, "build_folder")
        if not self.build_folder:
            raise KeyError('missing required key "build_folder"')
        self.build_folder = os.path.abspath(self.build_folder)\
                                   .replace("\\", "/")
        pfn = window.project_file_name()
        if not pfn:
            self.source_folder = window.extract_variables()["folder"]
        else:
            self.source_folder = os.path.dirname(pfn)
        while os.path.isfile(
                os.path.join(self.source_folder, "..", "CMakeLists.txt")):
            self.source_folder = os.path.join(self.source_folder, "..")
        self.source_folder = os.path.abspath(self.source_folder)
        self.source_folder = self.source_folder.replace("\\", "/")
        self.command_line_overrides = self._pop(
            data, "command_line_overrides", {})
        self.filter_targets = self._pop(data, "filter_targets", [])
        self.configurations = self._pop(data, "configurations", [])
        self.env = self._pop(data, "env", {})
        self.target_architecture = self._pop(
            data, "target_architecture", "x86")
        self.visual_studio_versions = self._pop(
            data, "visual_studio_versions", [15, 14])
        self.window = window
        assert self.build_folder

    def _pop(self, data, key, default=None):
        return data.get(key, default)

    def __repr__(self):
        return repr(type(self))

    def get_env(self):
        return {}  # Empty dict

    def variants(self):
        return []  # Empty list

    def on_pre_configure(self):
        pass

    def on_post_configure(self, exit_code):
        pass

    def get_build_invocation(self, **kwargs):
        raise NotImplemented()

    def create_sublime_build_system(self):
        view = self.window.active_view()
        if not view:
            sublime.error_message('Could not get the active view!')
        name = get_setting(view, 'generated_name_for_build_system')
        if not name:
            sublime.error_message('Could not find the key '
                                  '"generated_name_for_build_system"'
                                  ' in the settings!')
        name = sublime.expand_variables(name, self.window.extract_variables())
        build_system = {
            'name': name,
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
        env = self.get_env()
        if env:
            build_system['env'] = env
        return build_system

    def shell_cmd(self):
        return 'cmake --build .'

    def cmd(self, target=None):
        result = ["cmake", "--build", "."]
        if target:
            result.extend(["--target", target.name])
        return result

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
            sublime.error_message('Unknown sublime platform: {}'
                                  .format(sublime.platform()))
            return
    module_name = get_module_name(generator_string)
    if module_name not in sys.modules:
        valid_generators = get_valid_generators()
        sublime.error_message('CMakeBuilder: "%s" is not a valid generator. '
                              'The valid generators for this platform are: %s'
                              % (generator_string, ', '.join(valid_generators))
                              )
        return
    GeneratorModule = sys.modules[module_name]
    GeneratorClass = None
    try:
        GeneratorClass = getattr(
            GeneratorModule, generator_string.replace(' ', '_'))
    except AttributeError as e:
        sublime.error_message('Internal error: %s' % str(e))
    return GeneratorClass


def _get_pyfiles_from_dir(dir):
    for file in glob.iglob(dir + '/*.py'):
        if not os.path.isfile(file):
            continue
        base = os.path.basename(file)
        if base.startswith('__'):
            continue
        generator = base[:-3]
        yield generator


def _import_all_platform_specific_generators():
    path = os.path.join(os.path.dirname(__file__), sublime.platform())
    return list(_get_pyfiles_from_dir(path))


def import_user_generators():
    path = os.path.join(
        sublime.packages_path(), 'User', 'generators', sublime.platform())
    return list(_get_pyfiles_from_dir(path))


if sublime.platform() == 'linux':
    from .linux import *
elif sublime.platform() == 'osx':
    from .osx import *
elif sublime.platform() == 'windows':
    from .windows import *
else:
    sublime.error_message('Unknown platform: %s' % sublime.platform())
