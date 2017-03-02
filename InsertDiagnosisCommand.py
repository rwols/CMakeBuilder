import sublime, sublime_plugin, subprocess, os, shutil

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

        if self._command_exists('cmake'):
            self._OK(edit, 'CMake executable exists.')
        else:
            self._ERR(edit, 'Could not find the CMake executable! Make sure CMake is installed.')

        if self._command_exists('ctest'):
            self._OK(edit, 'CTest executable exists.')
        else:
            self._ERR(edit, 'Could not find the CTest executable! Make sure CMake is installed.')

        project = self.view.window().project_data()
        projectFilename = self.view.window().project_file_name()

        if projectFilename:
            self._OK(edit, 'Found project "{}"'.format(projectFilename))
        else:
            self._ERR(edit, 'Did NOT find a sublime-project file.\nYou should open a project file by going to Project -> Open Project.')
            return

        if not project:
            self._ERR(edit, 'Could not open file "{}"'.format(projectFilename))
            return

        cmake = project['cmake']

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
                self._ERR(edit, 'No build_folder present in cmake dictionary of "{}".'.format(projectFilename))
                self._ERR(edit, 'You should write a key-value pair in the "cmake" dictionary')
                self._ERR(edit, 'where the key is equal to "build_folder" and the value is the')
                self._ERR(edit, 'directory where you want to build your project.')
                self._ERR(edit, 'See the instructions at github.com/rwols/CMakeBuilder')
        else:
            self._ERR(edit, 'No cmake dictionary found in "{}".\nPlease read the instructions at github.com/rwols/CMakeBuilder'.format(projectFilename))
            return

    def _printLine(self, edit, str):
        self.view.insert(edit, self.view.size(), str + '\n')

    def _OK(self, edit, str):
        self._printLine(edit, '\n\u2705 ' + str)

    def _ERR(self, edit, str):
        self._printLine(edit, '\n\u274C ' + str)
        self.errorCount += 1
