import sublime
import sublime_plugin
import os
import functools
import tempfile
import Default.exec
import copy
from ..support import *
from ..generators import *

class CmakeConfigureCommand(Default.exec.ExecCommand):
    """Configures a CMake project."""

    def description(self):
        return 'Configure'

    def run(self, 
            build_folder, 
            source_folder, 
            generator,
            command_line_overrides={}, 
            configurations=[],
            env={}):
        settings = sublime.load_settings('CMakeBuilder.sublime-settings')
        if settings.get('always_clear_cache_before_configure', False):
            self.window.run_command('cmake_clear_cache', args={'with_confirmation': False})
        build_folder = os.path.realpath(build_folder)
        source_folder = os.path.realpath(source_folder)
        try:
            os.makedirs(build_folder, exist_ok=True)
        except OSError as e:
            sublime.error_message("Failed to create build directory: {}"
                .format(str(e)))
            return
        cmd = 'cmake -H"{}" -B"{}"'.format(source_folder, build_folder)
        if settings.get('silence_developer_warnings', False):
            cmd += ' -Wno-dev'
        GeneratorClass = class_from_generator_string(generator)
        try:
            self.builder = GeneratorClass(self.window, 
                source_folder, 
                build_folder, 
                generator, 
                configurations, 
                command_line_overrides, 
                env)
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        if generator != 'Visual Studio': # hacky
            cmd += ' -G "{}"'.format(generator)
        if command_line_overrides:
            for key, value in command_line_overrides.items():
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
        super().run(shell_cmd=cmd, 
            working_dir=source_folder,
            file_regex=r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:',
            syntax='Packages/CMakeBuilder/Syntax/Configure.sublime-syntax',
            env=self.builder.env())
    
    def on_finished(self, proc):
        super().on_finished(proc)
        self.builder.on_post_configure(proc.exit_code())

