import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from .ExpandVariables import *

class CmakeRunCtestCommand(Default.exec.ExecCommand):
    """Runs CTest in a console window."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        cmake = project.get('cmake')
        if cmake is None:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            return False
        build_folder = cmake.get('build_folder')
        if not build_folder:
            return False
        if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
            return False
        return True

    def description(self):
        return 'Run CTest'

    def run(self, verbose=False, extra_verbose=False):
        # self.write_build_targets = write_build_targets
        project = self.window.project_data()
        # project_file_name = self.window.project_file_name()
        # project_name = os.path.splitext(project_file_name)[0]
        # project_path = os.path.dirname(project_file_name)
        # if not os.path.isfile(os.path.join(project_path, 'CMakeLists.txt')):
        #     must_have_root_path = True
        # else:
        #     must_have_root_path = False
        # tempdir = tempfile.mkdtemp()
        cmake = project.get('cmake')
        # if cmake is None:
        #     project['cmake'] = {'build_folder': tempdir}
        #     print('CMakeBuilder: Temporary directory shall be "{}"'
        #         .format(tempdir))
        #     self.window.set_project_data(project)
        #     project = self.window.project_data()
        #     cmake = project['cmake']
        # build_folder_before_expansion = cmake.get('build_folder')
        # if build_folder_before_expansion is None:
        #     cmake['build_folder'] = tempdir
        #     print('CMakeBuilder: Temporary directory shall be "{}"'
        #         .format(tempdir))
        #     project['cmake'] = cmake
        #     self.window.set_project_data(project)
        #     project = self.window.project_data()
        #     cmake = project['cmake']
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
        # build_folder = os.path.realpath(build_folder)
        # generator = cmake.get('generator')
        # overrides = cmake.get('command_line_overrides')
        # if build_folder is None:
        #     sublime.error_message(
        #         'No "cmake: build_folder" variable found in {}.'.format(
        #             project_path))
        #     return
        # try:
        #     os.makedirs(build_folder, exist_ok=True)
        # except OSError as e:
        #     sublime.error_message("Failed to create build directory: {}"
        #         .format(str(e)))
        #     return
        # root_folder = cmake.get('root_folder')
        # if root_folder:
        #     root_folder = os.path.realpath(root_folder)
        # elif must_have_root_path:
        #     sublime.error_message(
        #         'No "CMakeLists.txt" file in the project folder is present and \
        #         no "root_folder" specified in the "cmake" dictionary of the \
        #         sublime-project file.')
        cmd = 'ctest'
        if verbose:
            cmd += ' -V'
        elif extra_verbose:
            cmd += ' -VV'
        super().run(shell_cmd=cmd, working_dir=build_folder)
    
    def on_finished(self, proc):
        super().on_finished(proc)
