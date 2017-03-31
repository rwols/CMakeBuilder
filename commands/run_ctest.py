import sublime, sublime_plugin, os, functools, tempfile, Default.exec
from ..support import *

# class CmakeRunCtestOldCommand(Default.exec.ExecCommand):
#     """Runs CTest in a console window."""

#     def is_enabled(self):
#         project = self.window.project_data()
#         if project is None:
#             return False
#         cmake = project.get('cmake')
#         if cmake is None:
#             return False
#         try:
#             # See ExpandVariables.py
#             expand_variables(cmake, self.window.extract_variables())
#         except Exception as e:
#             return False
#         build_folder = cmake.get('build_folder')
#         if not build_folder:
#             return False
#         if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
#             return False
#         return True

#     def description(self):
#         return 'Run CTest'

#     def run(self, build_folder, extra_args='--output-on-failure', test_framework='boost'):
#         cmd = 'ctest'
#         if extra_args:
#             cmd += ' ' + extra_args
#         #TODO: check out google test style errors, right now I just assume
#         #      everybody uses boost unit test framework
#         super().run(shell_cmd=cmd, 
#             working_dir=build_folder, 
#             file_regex=r'(.+[^:]):(\d+):() (?:fatal )?((?:error|warning): .+)$',
#             syntax='Packages/CMakeBuilder/Syntax/CTest.sublime-syntax')
    
#     def on_finished(self, proc):
#         super().on_finished(proc)

class CmakeRunCtestCommand(Default.exec.ExecCommand):
    """Runs CTest in a console window."""

    # def is_enabled(self):
    #     project = self.window.project_data()
    #     if project is None:
    #         return False
    #     cmake = project.get('cmake')
    #     if cmake is None:
    #         return False
    #     try:
    #         # See ExpandVariables.py
    #         expand_variables(cmake, self.window.extract_variables())
    #     except Exception as e:
    #         return False
    #     build_folder = cmake.get('build_folder')
    #     if not build_folder:
    #         return False
    #     if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
    #         return False
    #     return True

    def description(self):
        return 'Run CTest'

    def run(self, build_folder, args=None, test_framework='boost'):
        cmd = 'ctest'
        settings = sublime.load_settings('CMakeBuilder.sublime-settings')
        if not args:
            args = settings.get('ctest_command_line_args', None)
        if args:
            cmd += ' ' + args
        #TODO: check out google test style errors, right now I just assume
        #      everybody uses boost unit test framework
        super().run(shell_cmd=cmd,
            working_dir=build_folder, 
            file_regex=r'(.+[^:]):(\d+):() (?:fatal )?((?:error|warning): .+)$',
            syntax='Packages/CMakeBuilder/Syntax/CTest.sublime-syntax')
    
    def on_finished(self, proc):
        super().on_finished(proc)
