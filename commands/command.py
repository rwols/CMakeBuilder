import sublime_plugin
import sublime
import os
from ..server import Server
from ..support import capabilities
from ..support import get_setting


def _configure(window):
    try:
        cmake = window.project_data()["settings"]["cmake"]
        build_folder = cmake["build_folder"]
        build_folder = sublime.expand_variables(
            build_folder, window.extract_variables())
        if os.path.exists(build_folder):
            window.run_command("cmake_configure")
    except Exception:
        pass


class CmakeCommand(sublime_plugin.WindowCommand):

    def is_enabled(self):
        self.server = ServerManager.get(self.window)
        return (self.server is not None and
                super(CmakeCommand, self).is_enabled())


class CmakeRestartServerCommand(CmakeCommand):

    def run(self):
        try:
            window_id = self.window.id()
            ServerManager._servers.pop(window_id, None)
        except Exception as e:
            sublime.errror_message(str(e))

    @classmethod
    def description(cls):
        return "Restart Server For This Project"


class CMakeSettings(object):

    __slots__ = ("source_folder", "build_folder", "build_folder_pre_expansion",
                 "generator", "toolset", "platform", "command_line_overrides",
                 "file_regex", "syntax")

    """docstring for CMakeSettings"""
    def __init__(self):
        super(CMakeSettings, self).__init__()
        self.source_folder = ""
        self.build_folder = ""
        self.build_folder_pre_expansion = ""
        self.generator = ""
        self.toolset = ""
        self.platform = ""
        self.command_line_overrides = {}
        self.file_regex = ""
        self.syntax = ""

    def cmd(self, target):
        return target.cmd()


class ServerManager(sublime_plugin.EventListener):
    """Manages the bijection between cmake-enabled projects and server
    objects."""

    _servers = {}

    @classmethod
    def get(cls, window):
        return cls._servers.get(window.id(), None)

    def __init__(self):
        self._is_selecting = False
        self.generator = ""
        self.source_folder = ""
        self.build_folder = ""
        self.toolset = ""
        self.platform = ""

    def on_load(self, view):
        if not capabilities("serverMode"):
            print("CMakeBuilder: cmake is not capable of server mode")
            return
        if self._is_selecting:
            # User is busy entering stuff
            return
        if not capabilities("serverMode"):
            print("CMakeBuilder: cmake is not capable of server mode")
            return
        # Check if there's a server running for this window.
        self.window = view.window()
        if not self.window:
            return
        server = self.get(self.window)
        if server:
            return

        # No server running. Check if there are build settings.
        data = self.window.project_data()
        settings = data.get("settings", None)
        if not settings or not isinstance(settings, dict):
            print("no settings")
            return
        cmake = settings.get("cmake", None)
        if not cmake or not isinstance(cmake, dict):
            print("no cmake dict")
            return
        self.schemes = cmake.get("schemes", None)
        if (not self.schemes or
                not isinstance(self.schemes, list) or
                len(self.schemes) == 0):
            print("no schemes")
            return

        # At this point we found schemes. Let's check if there's a
        # CMakeLists.txt file to be found somewhere up the directory tree.
        if not view.file_name():
            return
        cmake_file = os.path.dirname(view.file_name())
        cmake_file = os.path.join(cmake_file, "CMakeLists.txt")
        while not os.path.isfile(cmake_file):
            cmake_file = os.path.dirname(os.path.dirname(cmake_file))
            if os.path.dirname(cmake_file) == cmake_file:
                # We're at the root of the filesystem.
                cmake_file = None
                break
            cmake_file = os.path.join(cmake_file, "CMakeLists.txt")
        if not cmake_file:
            # Not a cmake project
            return
        # We found a CMakeLists.txt file, but we might be embedded into a
        # larger project. Find the true root file.
        while True:
            old_cmake_file = cmake_file
            cmake_file = cmake_file = os.path.dirname(
                os.path.dirname(cmake_file))
            cmake_file = os.path.join(cmake_file, "CMakeLists.txt")
            while not os.path.isfile(cmake_file):
                cmake_file = os.path.dirname(os.path.dirname(cmake_file))
                if os.path.dirname(cmake_file) == cmake_file:
                    # We're at the root of the filesystem.
                    cmake_file = None
                    break
                cmake_file = os.path.join(cmake_file, "CMakeLists.txt")
            if not cmake_file:
                # We found the actual root of the project earlier.
                cmake_file = old_cmake_file
                break
        self.source_folder = os.path.dirname(cmake_file)
        print("found source folder:", self.source_folder)

        # At this point we have a bunch of schemes and we have a source folder.
        self.items = []
        for scheme in self.schemes:
            if not isinstance(scheme, dict):
                sublime.error_message("Please make sure all of your schemes "
                                      "are JSON dictionaries.")
                self.items.append(["INVALID SCHEME", ""])
                continue
            name = scheme.get("name", "Untitled Scheme")
            build_folder = scheme.get("build_folder", "${project_path}/build")
            variables = self.window.extract_variables()
            build_folder = sublime.expand_variables(build_folder, variables)
            self.items.append([name, build_folder])
        if len(self.schemes) == 0:
            print("found schemes dict, but it is empty")
            return
        self._is_selecting = True
        if len(self.schemes) == 1:
            # Select the only scheme possible.
            self._on_done_select_scheme(0)
        else:
            # Ask the user what he/she wants.
            self.window.show_quick_panel(self.items,
                                         self._on_done_select_scheme)

    def _on_done_select_scheme(self, index):
        if index == -1:
            self._is_selecting = False
            return
        self.name = self.items[index][0]
        if self.name == "INVALID SCHEME":
            self._is_selecting = False
            return
        self.build_folder_pre_expansion = self.schemes[index]["build_folder"]
        self.build_folder = sublime.expand_variables(
            self.build_folder_pre_expansion, self.window.extract_variables())
        self.command_line_overrides = self.schemes[index].get(
            "command_line_overrides", {})
        self._select_generator()

    def _select_generator(self):
        if self.generator:
            self._select_toolset()
            return
        self.items = []
        for g in capabilities("generators"):
            platform_support = bool(g["platformSupport"])
            toolset_support = bool(g["toolsetSupport"])
            platform_support = "Platform support: {}".format(platform_support)
            toolset_support = "Toolset support: {}".format(toolset_support)
            self.items.append([g["name"], platform_support, toolset_support])
        if len(self.items) == 1:
            self._on_done_select_generator(0)
        else:
            self.window.show_quick_panel(self.items,
                                         self._on_done_select_generator)

    def _on_done_select_generator(self, index):
        if index == 1:
            self._is_selecting = False
            return
        self.generator = self.items[index][0]
        platform_support = self.items[index][1]
        toolset_support = self.items[index][2]
        self.platform_support = True if "True" in platform_support else False
        self.toolset_support = True if "True" in toolset_support else False
        if self.platform_support:
            text = "Platform for {} (Press Enter for default): ".format(
                self.generator)
            self.window.show_input_panel(text, "",
                                         self._on_done_select_platform,
                                         None, None)
        elif self.toolset_support:
            self._select_toolset()
        else:
            self._run_configure_with_new_settings()

    def _select_toolset(self):
        if self.toolset:
            return
        text = "Toolset for {}: (Press Enter for default): ".format(
            self.generator)
        self.window.show_input_panel(text, "", self._on_done_select_toolset,
                                     None, None)

    def _on_done_select_platform(self, platform):
        self.platform = platform
        if self.toolset_support:
            self._select_toolset()
        else:
            self._run_configure_with_new_settings()

    def _on_done_select_toolset(self, toolset):
        self.toolset = toolset
        self._run_configure_with_new_settings()

    def _run_configure_with_new_settings(self):
        self._is_selecting = False
        cmake_settings = CMakeSettings()
        cmake_settings.source_folder = self.source_folder
        cmake_settings.build_folder = self.build_folder

        cmake_settings.build_folder_pre_expansion = \
            self.build_folder_pre_expansion

        cmake_settings.generator = self.generator
        cmake_settings.platform = self.platform
        cmake_settings.toolset = self.toolset
        cmake_settings.command_line_overrides = self.command_line_overrides

        if sublime.platform() in ("osx", "linux"):
            cmake_settings.file_regex = \
                r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'
            if "Makefile" in self.generator:
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
            elif "Ninja" in self.generator:
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax"
            else:
                print("CMakeBuilder: Warning: Generator", self.generator,
                      "will not have syntax highlighting in the output panel.")
        elif sublime.platform() == "windows":
            if "Ninja" in self.generator:
                cmake_settings.file_regex = r'^(.+)\((\d+)\):() (.+)$'
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Ninja+CL.sublime-syntax"
            elif "Visual Studio" in self.generator:
                cmake_settings.file_regex = \
                    (r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) ',
                     r'\w+\d\d\d\d: .*) \[.*$')
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Visual_Studio.sublime-syntax"
            elif "NMake" in self.generator:
                cmake_settings.file_regex = r'^(.+)\((\d+)\):() (.+)$'
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
            else:
                print("CMakeBuilder: Warning: Generator", self.generator,
                      "will not have syntax highlighting in the output panel.")
        else:
            sublime.error_message("Unknown platform: " + sublime.platform())
            return

        server = Server(self.window, cmake_settings)
        self.source_folder = ""
        self.build_folder = ""
        self.build_folder_pre_expansion = ""
        self.generator = ""
        self.platform = ""
        self.toolset = ""
        self.items = []
        self.schemes = []
        self.command_line_overrides = {}
        self.__class__._servers[self.window.id()] = server

    def on_activated(self, view):
        self.on_load(view)
        try:
            server = self.__class__.get(view.window())
            path = os.path.join(server.cmake.build_folder,
                                "CMakeFiles",
                                "CMakeBuilder",
                                "active_target.txt")
            with open(path, "r") as f:
                active_target = f.read()
            view.set_status("cmake_active_target", "TARGET: " + active_target)
        except Exception as e:
            view.erase_status("cmake_active_target")


    def on_post_save(self, view):
        if not view:
            return
        if not get_setting(view, "configure_on_save", False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith(".sublime-project"):
            server = self.__class__.get(view.window())
            if not server:
                _configure(view.window())
            else:
                view.window().run_command("cmake_clear_cache",
                                          {"with_confirmation": False})
                view.window().run_command("cmake_restart_server")
        elif name.endswith("CMakeLists.txt") or name.endswith("CMakeCache.txt"):
            _configure(view.window())
