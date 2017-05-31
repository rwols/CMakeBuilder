import sublime, sublime_plugin, subprocess, os

class CmakeInsertDiagnosisCommand(sublime_plugin.TextCommand):

    def __init__(self, view):
        super(CmakeInsertDiagnosisCommand, self).__init__(view)
        self.errorCount = 0

    def run(self, edit):
        self._diagnose(edit)
        if self.errorCount == 0:
            self._printLine(edit, '\nEverything seems to be OK!')

    def _command_exists(self, cmd):
        return shutil.which(cmd) is not None

    def _diagnose(self, edit):
        project = self.view.window().project_data()
        project_filename = self.view.window().project_file_name()

        if project_filename:
            self._OK(edit, 'Found project "{}"'.format(project_filename))
        else:
            self._ERR(edit, 'Did NOT find a sublime-project file.\nYou should open a project file by going to Project -> Open Project.')
            return

        if not project:
            self._ERR(edit, 'Could not open file "{}"'.format(project_filename))
            return

        cmake = project.get("cmake", None)
        if cmake:
            self._ERR(edit, "It looks like you have the cmake dictionary at the top level of your project file.")
            self._ERR(edit, "Since version 0.11.0, the cmake dict should be in the settings dict of your project file.")
            self._ERR(edit, "Please edit your project file so that the cmake dict is sitting inside your settings")
            return

        cmake = project.get("settings", {}).get("cmake", None)

        if cmake:
            cmake = sublime.expand_variables(cmake, self.view.window().extract_variables())
            buildFolder = cmake['build_folder']
            if buildFolder:
                self._OK(edit, 'Found CMake build folder "{}"'.format(buildFolder))
                self._OK(edit, 'You can run the "Configure" command.')
                cache_file = os.path.join(buildFolder, 'CMakeCache.txt')
                if os.path.isfile(cache_file):
                    self._OK(edit, 'Found CMakeCache.txt file in "{}"'.format(buildFolder))
                    self._OK(edit, 'You can run the command "Write Build Targets to Sublime Project File"')
                    self._OK(edit, 'If you already populated your project file with build targets, you can build your project with Sublime\'s build system. Go to Tools -> Build System and make sure your build system is selected.')
                else:
                    self._ERR(edit, 'No CMakeCache.txt file found in "{}"'.format(buildFolder))
                    self._ERR(edit, 'You should run the "Configure" command.')
                    return
            else:
                self._ERR(edit, 'No build_folder present in cmake dictionary of "{}".'.format(project_filename))
                self._ERR(edit, 'You should write a key-value pair in the "cmake" dictionary')
                self._ERR(edit, 'where the key is equal to "build_folder" and the value is the')
                self._ERR(edit, 'directory where you want to build your project.')
                self._ERR(edit, 'See the instructions at github.com/rwols/CMakeBuilder')
        else:
            self._ERR(edit, 'No cmake dictionary found in "{}".\nPlease read the instructions at github.com/rwols/CMakeBuilder'.format(project_filename))
            return

    def _printLine(self, edit, str):
        self.view.insert(edit, self.view.size(), str + '\n')

    def _OK(self, edit, str):
        self._printLine(edit, '\n\u2705 ' + str)

    def _ERR(self, edit, str):
        self._printLine(edit, '\n\u274C ' + str)
        self.errorCount += 1
