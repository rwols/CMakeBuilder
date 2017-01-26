import sublime, sublime_plugin, os, glob

class CmakeCacheResetCommand(sublime_plugin.WindowCommand):
    """Clears the CMake-generated files"""

    def run(self):
        project = self.window.project_data()
        if project is None:
            sublime.error_message('No sublime-project file found.')
            return
        cmakeDict = project.get('cmake')
        if cmakeDict is None:
            sublime.error_message(
                'No \"cmake\" dictionary in sublime-project file found.')
            return
        cmakeDict = sublime.expand_variables(
            cmakeDict, self.window.extract_variables())
        buildFolder = cmakeDict.get('build_folder')
        if buildFolder:
            files_to_remove = []
            dirs_to_remove = []
            cmakefiles_dir = os.path.join(buildFolder, 'CMakeFiles')
            if os.path.exists(cmakefiles_dir):
                for root, dirs, files in os.walk(cmakefiles_dir, topdown=False):
                    files_to_remove.extend([name for name in files])
                    dirs_to_remove.extend([name for name in dirs])
                dirs_to_remove.append(cmakefiles_dir)
            cmakecache_file = os.path.join(buildFolder, 'CMakeCache.txt')
            cmakeinstall_file = os.path.join(buildFolder, 'cmake_install.cmake')
            if os.path.exists(cmakecache_file):
                files_to_remove.append(cmakecache_file)
            if os.path.exists(cmakeinstall_file):
                files_to_remove.append(cmakeinstall_file)

            self.panel = self.window.create_output_panel('files_to_be_deleted')
            self.window.run_command('show_panel', {'panel': 'output.files_to_be_deleted'})
            self.panel.run_command('append', {'characters': 'Deleted files:\n' + \
                                              '\n'.join(files_to_remove + dirs_to_remove)})

            for file in files_to_remove:
                try:
                    os.remove(os.path.join(buildFolder, file))
                except Exception as e:
                    sublime.error_message('Cannot remove '+file)
            for directory in dirs_to_remove:
                try:
                    os.rmdir(os.path.join(buildFolder, directory))
                except Exception as e:
                    sublime.error_message('Cannot remove '+directory)

            return
        else:
            sublime.error_message(
                'No \"build_folder\" string specified in \"cmake\" dictionary \
                in sublime-project file.')
            return
