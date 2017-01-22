import sublime, sublime_plugin, os, glob, Default.exec

class CmakeCacheResetCommand(Default.exec.ExecCommand):
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
            for root, dirs, files in os.walk(os.path.join(buildFolder, 'CMakeFiles'), topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except Exception:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except Exception:
                        pass
            try:
                os.remove(os.path.join(buildFolder, 'CMakeCache.txt'))
            except Exception:
                pass
            def remove_file(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            map(remove_file, glob.glob(os.path.join(buildFolder, '*.cmake')))
            return
        else:
            sublime.error_message(
                'No \"build_folder\" string specified in \"cmake\" dictionary \
                in sublime-project file.')
            return
