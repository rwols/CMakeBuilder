import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from .ExpandVariables import *

class CmakeConfigureCommand(Default.exec.ExecCommand):
    """Configures a CMake project with options set in the sublime project
    file."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        project_file_name = self.window.project_file_name()
        if not project_file_name:
            return False
        return True

    def description(self):
        return 'Configure'

    def run(self, write_build_targets=False):
        self.write_build_targets = write_build_targets
        project = self.window.project_data()
        project_file_name = self.window.project_file_name()
        project_name = os.path.splitext(project_file_name)[0]
        project_path = os.path.dirname(project_file_name)
        if not os.path.isfile(os.path.join(project_path, 'CMakeLists.txt')):
            must_have_root_path = True
        else:
            must_have_root_path = False
        tempdir = tempfile.mkdtemp()
        cmake = project.get('cmake')
        if cmake is None:
            project['cmake'] = {'build_folder': tempdir}
            print('CMakeBuilder: Temporary directory shall be "{}"'
                .format(tempdir))
            self.window.set_project_data(project)
            project = self.window.project_data()
            cmake = project['cmake']
        build_folder_before_expansion = cmake.get('build_folder')
        if build_folder_before_expansion is None:
            cmake['build_folder'] = tempdir
            print('CMakeBuilder: Temporary directory shall be "{}"'
                .format(tempdir))
            project['cmake'] = cmake
            self.window.set_project_data(project)
            project = self.window.project_data()
            cmake = project['cmake']
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
        build_folder = cmake.get('build_folder')
        build_folder = os.path.realpath(build_folder)
        generator = cmake.get('generator')
        overrides = cmake.get('command_line_overrides')
        if build_folder is None:
            sublime.error_message(
                'No "cmake: build_folder" variable found in {}.'.format(
                    project_path))
            return
        try:
            os.makedirs(build_folder, exist_ok=True)
        except OSError as e:
            sublime.error_message("Failed to create build directory: {}"
                .format(str(e)))
            return
        root_folder = cmake.get('root_folder')
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
        if generator:
            cmd += ' -G "{}"'.format(generator)
        try:
            for key, value in overrides.items():
                if type(value) is bool:
                    cmd += ' -D{}={}'.format(key, 'ON' if value else 'OFF')
                else:
                    cmd += ' -D{}={}'.format(key, str(value))
        except AttributeError as e:
            pass
        except ValueError as e:
            pass
        super().run(shell_cmd=cmd, 
            working_dir=root_folder,
            file_regex=r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:',
            syntax='Packages/CMakeBuilder/Syntax/Configure.sublime-syntax')
    
    def on_finished(self, proc):
        super().on_finished(proc)
        if self.write_build_targets:
            sublime.set_timeout(
                functools.partial(
                    self.window.run_command, 
                    'cmake_write_build_targets'), 0)
