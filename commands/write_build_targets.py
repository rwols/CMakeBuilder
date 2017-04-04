import sublime
import sublime_plugin
import os
import Default.exec
import multiprocessing
import subprocess
import glob
import re
import threading
import copy
from ..support import *
from ..generators import *

class CmakeWriteBuildTargetsCommand(sublime_plugin.WindowCommand):
    """Writes a build system to the sublime project file. This only works
    when a cmake project has been configured."""

    def is_enabled(self):
        """You may only run this command if there's a `build_folder` with a
        `CMakeCache.txt` file in it. That's when we assume that the project has
        been configured."""
        project = self.window.project_data()

        # If there's no project dict, go home.
        if project is None:
            return False

        # If there's no project filename, go home.
        if not self.window.project_file_name():
            return False
        cmake = project.get('cmake')

        # If there's no cmake dict in the project dict, go home.
        if not cmake:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            # We'll end up here if the user wrote a substitution variable that
            # we don't recognize. In that case we go home.
            return False
        build_folder = get_cmake_value(cmake, 'build_folder')

        # If there's no CMakeCache.txt file in the build folder, we assume the
        # user hasn't configured the project yet. So we can't write build
        # targets in that situation.
        if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
            return False

        # There's a build folder containing a CMakeCache.txt file; we think the
        # project has been configured, so we allow this command to be run by the
        # user.
        return True

    def description(self):
        return 'Write Build Targets to Sublime Project'

    def run(self):
        project = self.window.project_data()
        project_file_name = self.window.project_file_name()
        project_path = os.path.dirname(project_file_name)
        cmake = project.get('cmake')
        if not cmake:
            return
        generator = get_cmake_value(cmake, 'generator')
        GeneratorClass = class_from_generator_string(generator)
        try:
            assert cmake
            builder = GeneratorClass(self.window, copy.deepcopy(cmake))
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        try:
            assert builder
            new_build_system = builder.create_sublime_build_system()
            build_systems = project.get('build_systems', None)
            if build_systems:
                for i, build_system in enumerate(build_systems):
                    if build_system.get('name', '') == new_build_system['name']:
                        build_systems[i] = new_build_system
                        self.window.set_project_data(project)
                        self.window.run_command('set_build_system', args={'index': i})
                        return
                build_systems.append(new_build_system)
                self.window.set_project_data(project)
                self.window.run_command('set_build_system', args={'index': len(build_systems) - 1})
            else:
                project['build_systems'] = [new_build_system]
                self.window.set_project_data(project)
                self.window.run_command('set_build_system', args={'index': 0})
        except Exception as e:
            sublime.error_message('An error occured during assigment of the sublime build system: %s' % str(e))

