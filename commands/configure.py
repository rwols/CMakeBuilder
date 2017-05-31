import sublime
import sublime_plugin
import os
import functools
import tempfile
import Default.exec
import copy
from CMakeBuilder.support import *
from CMakeBuilder.generators import *

class CmakeConfigureCommand(Default.exec.ExecCommand):
    """Configures a CMake project with options set in the sublime project
    file."""
    def is_enabled(self):
        try:
            cmake = self.window.project_data()["settings"]["cmake"]
            build_folder = cmake["build_folder"]
            return True
        except Exception as e:
            return False
    
    def description(self):
        return 'Configure'

    def run(self, write_build_targets=False, silence_dev_warnings=False):
        if get_setting(self.window.active_view(), 'always_clear_cache_before_configure', False):
            self.window.run_command('cmake_clear_cache', args={'with_confirmation': False})
        project = self.window.project_data()
        project_file_name = self.window.project_file_name()
        project_name = os.path.splitext(project_file_name)[0]
        project_path = os.path.dirname(project_file_name)
        if not os.path.isfile(os.path.join(project_path, 'CMakeLists.txt')):
            must_have_root_path = True
        else:
            must_have_root_path = False
        cmake = project["settings"]["cmake"]
        build_folder_before_expansion = get_cmake_value(cmake, 'build_folder')
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        # Guaranteed to exist at this point.
        build_folder = get_cmake_value(cmake, 'build_folder')
        build_folder = os.path.realpath(build_folder)
        generator = get_cmake_value(cmake, 'generator')
        if not generator:
            if   sublime.platform() == 'linux':   generator = 'Unix Makefiles'
            elif sublime.platform() == 'osx':     generator = 'Unix Makefiles'
            elif sublime.platform() == 'windows': generator = 'Visual Studio'
            else:
                sublime.error_message('Unknown sublime platform: {}'.format(sublime.platform()))
                return
        overrides = get_cmake_value(cmake, 'command_line_overrides')
        try:
            os.makedirs(build_folder, exist_ok=True)
        except OSError as e:
            sublime.error_message("Failed to create build directory: {}"
                .format(str(e)))
            return
        root_folder = get_cmake_value(cmake, 'root_folder')
        if root_folder:
            root_folder = os.path.realpath(root_folder)
        elif must_have_root_path:
            sublime.error_message(
                'No "CMakeLists.txt" file in the project folder is present and \
                no "root_folder" specified in the "cmake" dictionary of the \
                sublime-project file.')
        else:
            root_folder = project_path
        # -H and -B are undocumented arguments.
        # See: http://stackoverflow.com/questions/31090821
        cmd = 'cmake -H"{}" -B"{}"'.format(root_folder, build_folder)
        if get_setting(self.window.active_view(), 'silence_developer_warnings', False):
            cmd += ' -Wno-dev'
        GeneratorClass = class_from_generator_string(generator)
        builder = None
        try:
            builder = GeneratorClass(self.window, copy.deepcopy(cmake))
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        self.builder = builder
        cmd += ' -G"{}"'.format(repr(self.builder))
        if overrides:
            for key, value in overrides.items():
                try:
                    if type(value) is bool:
                        cmd += ' -D{}={}'.format(key, 'ON' if value else 'OFF')
                    else:
                        cmd += ' -D{}={}'.format(key, str(value))
                except AttributeError as e:
                    pass
                except ValueError as e:
                    pass
        self.builder.on_pre_configure()
        env = self.builder.env()
        user_env = get_cmake_value(cmake, 'env')
        if user_env: env.update(user_env)
        super().run(shell_cmd=cmd, 
            working_dir=root_folder,
            file_regex=r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:',
            syntax='Packages/CMakeBuilder/Syntax/Configure.sublime-syntax',
            env=env)
    
    def on_finished(self, proc):
        super().on_finished(proc)
        self.builder.on_post_configure(proc.exit_code())
        if proc.exit_code() == 0:
            if get_setting(self.window.active_view(), 'write_build_targets_after_successful_configure', False):
                rc = self.window.run_command
                name = 'cmake_write_build_targets'
                func = functools.partial(rc, name)
                sublime.set_timeout(func, 0)

