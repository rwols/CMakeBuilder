import sublime
import sublime_plugin
import os
import shutil
from tabulate import tabulate  # dependencies.json
from CMakeBuilder.support import check_output
from CMakeBuilder.support import capabilities


class CmakeInsertDiagnosisCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.error_count = 0
        self._diagnose(edit)
        self.view.insert(edit, self.view.size(), tabulate(
            self.table,
            headers=["CHECK", "VALUE", "SUGGESTION/FIX"],
            tablefmt="fancy_grid"))

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
            server_mode = capabilities("serverMode")
            self.table.append(["server mode", server_mode, ""])
        except Exception as e:
            self.table.append(["server mode", False,
                               "Have cmake version >= 3.7"])

        project = self.view.window().project_data()
        project_filename = self.view.window().project_file_name()

        if project_filename:
            self.table.append(["project file", project_filename, ""])
        else:
            self.table.append(["project file", "NOT FOUND",
                               "Open a .sublime-project"])
            self.error_count += 1
            return

        cmake = project.get("settings", {}).get("cmake", None)

        if cmake:
            cmake = sublime.expand_variables(
                cmake,
                self.view.window().extract_variables())
            buildFolder = cmake['build_folder']
            if buildFolder:
                self.table.append(["cmake dictionary present in settings",
                                   True, ""])
                cache_file = os.path.join(buildFolder, 'CMakeCache.txt')
                if os.path.isfile(cache_file):
                    self.table.append([
                        "CMakeCache.txt file present", True,
                        "You may run the Write Build Targets command"])
                else:
                    self.table.append(["CMakeCache.txt file present", False,
                                       "Run the Configure command"])
                    self.error_count += 1
                    return
            else:
                self.table.append(["build_folder present in cmake dictionary",
                                   False, "Write a build_folder key"])
                self.error_count += 1
        else:
            self.table.append(["cmake dictionary present in settings", False,
                               "Create a cmake dictionary in your settings"])
            return

    def _printLine(self, edit, str):
        self.view.insert(edit, self.view.size(), str + '\n')

    def _OK(self, edit, str):
        self._printLine(edit, '\n\u2705 ' + str)

    def _ERR(self, edit, str):
        self._printLine(edit, '\n\u274C ' + str)
        self.error_count += 1
