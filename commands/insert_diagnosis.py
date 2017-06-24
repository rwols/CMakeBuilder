import sublime, sublime_plugin, subprocess, os, shutil, sys, json
from tabulate import tabulate  # dependencies.json
from CMakeBuilder.support import check_output


class CmakeInsertDiagnosisCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.error_count = 0
        self._diagnose(edit)
        self.view.insert(edit, self.view.size(), tabulate(self.table, headers=["CHECK", "VALUE", "SUGGESTION/FIX"], tablefmt="fancy_grid"))

    def _command_exists(self, cmd):
        return shutil.which(cmd) is not None

    def _diagnose(self, edit):
        self.table = []
        try:
            output = check_output("cmake --version").splitlines()[0][14:]
        except Exception as e:
            self.table.append(["cmake present", False, "Install cmake"])
            return
        else:
            self.table.append(["cmake version", output, ""])
        try:
            output = json.loads(check_output("cmake -E capabilities"))
            server_mode = output.get("serverMode", False)
            self.table.append(["server mode", server_mode, ""])
        except Exception as e:
            self.table.append(["server mode", False, "Have cmake version >= 3.7"])

        project = self.view.window().project_data()
        project_filename = self.view.window().project_file_name()

        if project_filename:
            self.table.append(["project file", project_filename, ""])
        else:
            self.table.append(["project file", "NOT FOUND", "Open a .sublime-project"])
            self.error_count += 1
            return

        # cmake = project.get("cmake", None)
        # if cmake:
        #     self._ERR(edit, "It looks like you have the cmake dictionary at the top level of your project file.")
        #     self._ERR(edit, "Since version 0.11.0, the cmake dict should be in the settings dict of your project file.")
        #     self._ERR(edit, "Please edit your project file so that the cmake dict is sitting inside your settings")
        #     return

        cmake = project.get("settings", {}).get("cmake", None)

        if cmake:
            cmake = sublime.expand_variables(cmake, self.view.window().extract_variables())
            buildFolder = cmake['build_folder']
            if buildFolder:
                self.table.append(["cmake dictionary present in settings", True, ""])
                # self._OK(edit, 'Found CMake build folder "{}"'.format(buildFolder))
                # self._OK(edit, 'You can run the "Configure" command.')
                cache_file = os.path.join(buildFolder, 'CMakeCache.txt')
                if os.path.isfile(cache_file):
                    self.table.append(["CMakeCache.txt file present", True, "You may run the Write Build Targets command"])
                    # self._OK(edit, 'Found CMakeCache.txt file in "{}"'.format(buildFolder))
                    # self._OK(edit, 'You can run the command "Write Build Targets to Sublime Project File"')
                    # self._OK(edit, 'If you already populated your project file with build targets, you can build your project with Sublime\'s build system. Go to Tools -> Build System and make sure your build system is selected.')
                else:
                    self.table.append(["CMakeCache.txt file present", False, "Run the Configure command"])
                    self.error_count += 1
                    # self._ERR(edit, 'No CMakeCache.txt file found in "{}"'.format(buildFolder))
                    # self._ERR(edit, 'You should run the "Configure" command.')
                    return
            else:
                self.table.append(["build_folder present in cmake dictionary", False, "Write a build_folder key"])
                self.error_count += 1
                # self._ERR(edit, 'No build_folder present in cmake dictionary of "{}".'.format(project_filename))
                # self._ERR(edit, 'You should write a key-value pair in the "cmake" dictionary')
                # self._ERR(edit, 'where the key is equal to "build_folder" and the value is the')
                # self._ERR(edit, 'directory where you want to build your project.')
                # self._ERR(edit, 'See the instructions at github.com/rwols/CMakeBuilder')
        else:
            self.table.append(["cmake dictionary present in settings", False, "Create a cmake dictionary in your settings"])
            return

    def _printLine(self, edit, str):
        self.view.insert(edit, self.view.size(), str + '\n')

    def _OK(self, edit, str):
        self._printLine(edit, '\n\u2705 ' + str)

    def _ERR(self, edit, str):
        self._printLine(edit, '\n\u274C ' + str)
        self.error_count += 1
