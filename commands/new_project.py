import sublime, sublime_plugin, os

CMAKELISTS_FILE = """cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project({0} VERSION 0.1.0 LANGUAGES {1})
add_subdirectory(src)
"""

CMAKELISTS_SRC_FILE = """add_executable(hello main.{0})
"""

CFILE = """#include <stdio.h>

int main(int argc, char** argv)
{
    printf("Hello, world!\\n");
    return 0;
}
"""

CXXFILE = """#include <iostream>

int main(int argc, const char** argv)
{
    std::cout << "Hello, world!\\n";
    return 0;
}
"""

PROJECTFILE = """{
    "build_systems":
    [
    ],
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {
        "cmake":
        {
            "build_folder": "${project_path}/build"
        }
    }
}
"""

class CmakeNewProjectCommand(sublime_plugin.WindowCommand):
    """Creates a new template project and opens the project for you."""

    def description(self):
        return "New Project..."

    def run(self):
        self.window.show_input_panel("Type the name of the new project: ", "MyProject", self._on_done_project_name, None, None)

    def _on_done_project_name(self, text):
        self.project_name = text
        initial_text = os.path.expanduser("~")
        if sublime.platform() == "osx":
            initial_text = os.path.join(initial_text, "Documents")
        self.window.show_input_panel("Type the path where you want to initialize %s: " % self.project_name, initial_text, self._on_done_project_dir, None, None)

    def _on_done_project_dir(self, text):
        self.project_dir = os.path.join(text, self.project_name)
        if os.path.exists(self.project_dir):
            sublime.error_message('The directory "%s" already exists!' % self.project_dir)
            return
        msg = 'The new project location will be "%s".\n\nPress OK to continue...' % (self.project_dir)
        if sublime.ok_cancel_dialog(msg):
            self.window.show_quick_panel([["C", "A project suitable for C"], ["C++", "A project suitable for C++"], ["C and C++", "A project suitable for both C and C++"]], self._on_done_select_project_type)

    def _on_done_select_project_type(self, index):
        if index == 0:
            self.type = "C"
            self.suffix = "c"
        elif index == 1:
            self.type = "CXX"
            self.suffix = "cpp"
        elif index == 2:
            self.type = "C CXX"
            self.suffix = "cpp"
        else:
            return
        self._create_project()

    def _create_project(self):
        os.makedirs(self.project_dir, exist_ok=True)
        if not os.path.exists(self.project_dir):
            sublime.error_message("Could not create directory %s" % self.project_dir)
        os.makedirs(os.path.join(self.project_dir, "src"), exist_ok=True)
        with open(os.path.join(self.project_dir, "CMakeLists.txt"), "w") as f:
            f.write(CMAKELISTS_FILE.format(self.project_name, self.type))
        with open(os.path.join(self.project_dir, "src", "main." + self.suffix), "w") as f:
            if self.type == "C":
                f.write(CFILE)
            else:
                f.write(CXXFILE)
        with open(os.path.join(self.project_dir, "src", "CMakeLists.txt"), "w") as f:
            f.write(CMAKELISTS_SRC_FILE.format(self.suffix))
        project_file = os.path.join(self.project_dir, self.project_name + ".sublime-project")
        with open(project_file, "w") as f:
            f.write(PROJECTFILE)
        if sublime.ok_cancel_dialog('Select the file %s in "%s" in the upcoming prompt...' % (self.project_name + ".sublime-project", self.project_dir)):
            sublime.run_command("prompt_open_project_or_workspace")

