import sublime, sublime_plugin, os
from ..support import *

# Note: Things in "CMakeFiles" folders get removed anyway. This is where you put
# files that should be removed but are not inside CMakeFiles folders.
TRY_TO_REMOVE = [
    'CMakeCache.txt',
    'cmake_install.cmake'
]

class CmakeClearCacheCommand(sublime_plugin.WindowCommand):
    """Clears the CMake-generated files"""

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
        return 'Clear Cache'

    def run(self, with_confirmation=True):
        cmake = sublime.expand_variables(
            self.window.project_data().get('cmake'), 
            self.window.extract_variables())
        # Guaranteed to exist because is_enabled checks for it.
        build_folder = cmake.get('build_folder')
        files_to_remove = []
        dirs_to_remove = []
        cmakefiles_dir = os.path.join(build_folder, 'CMakeFiles')
        if os.path.exists(cmakefiles_dir):
            for root, dirs, files in os.walk(cmakefiles_dir, topdown=False):
                files_to_remove.extend([os.path.join(root, name) for name in files])
                dirs_to_remove.extend([os.path.join(root, name) for name in dirs])
            dirs_to_remove.append(cmakefiles_dir)

        def append_file_to_remove(relative_name):
            abs_path = os.path.join(build_folder, relative_name)
            if os.path.exists(abs_path):
                files_to_remove.append(abs_path)

        for file in TRY_TO_REMOVE:
            append_file_to_remove(file)

        if not with_confirmation:
            self.remove(files_to_remove, dirs_to_remove)
            return

        panel = self.window.create_output_panel('files_to_be_deleted')

        self.window.run_command('show_panel', 
            {'panel': 'output.files_to_be_deleted'})

        panel.run_command('insert', 
            {'characters': 'Files to remove:\n' +
             '\n'.join(files_to_remove + dirs_to_remove)})

        def on_done(selected):
            if selected != 0: return
            self.remove(files_to_remove, dirs_to_remove)
            panel.run_command('append', 
                {'characters': '\nCleared CMake cache files!',
                 'scroll_to_end': True})

        self.window.show_quick_panel(['Do it', 'Cancel'], on_done, 
            sublime.KEEP_OPEN_ON_FOCUS_LOST)

    def remove(self, files_to_remove, dirs_to_remove):
        for file in files_to_remove:
            try:
                os.remove(file)
            except Exception as e:
                sublime.error_message('Cannot remove '+file)
        for directory in dirs_to_remove:
            try:
                os.rmdir(directory)
            except Exception as e:
                sublime.error_message('Cannot remove '+directory)

        
