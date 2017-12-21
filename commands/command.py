import sublime_plugin
import sublime
import os
import pickle
from ..support.server import Server
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
            self.window.focus_view(self.window.active_view())
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
        self.__class__._is_selecting = False
        self.__class__.generator = ""
        self.__class__.source_folder = ""
        self.__class__.build_folder = ""
        self.__class__.toolset = ""
        self.__class__.platform = ""

    @classmethod
    def on_load(cls, view):
        if not capabilities("serverMode"):
            print("CMakeBuilder: cmake is not capable of server mode")
            return
        if cls._is_selecting:
            # User is busy entering stuff
            return
        if not capabilities("serverMode"):
            print("CMakeBuilder: cmake is not capable of server mode")
            return
        # Check if there's a server running for this window.
        cls.window = view.window()
        if not cls.window:
            return
        server = cls.get(cls.window)
        if server:
            return

        # No server running. Check if there are build settings.
        data = cls.window.project_data()
        if not data:
            return
        settings = data.get("settings", None)
        if not settings or not isinstance(settings, dict):
            return
        cmake = settings.get("cmake", None)
        if not cmake or not isinstance(cmake, dict):
            return
        cls.schemes = cmake.get("schemes", None)
        if (not cls.schemes or
                not isinstance(cls.schemes, list) or
                len(cls.schemes) == 0):
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
        cls.source_folder = os.path.dirname(cmake_file)
        print("found source folder:", cls.source_folder)

        # At this point we have a bunch of schemes and we have a source folder.
        cls.items = []
        for scheme in cls.schemes:
            if not isinstance(scheme, dict):
                sublime.error_message("Please make sure all of your schemes "
                                      "are JSON dictionaries.")
                cls.items.append(["INVALID SCHEME", ""])
                continue
            name = scheme.get("name", "Untitled Scheme")
            build_folder = scheme.get("build_folder", "${project_path}/build")
            variables = cls.window.extract_variables()
            build_folder = sublime.expand_variables(build_folder, variables)
            cls.items.append([name, build_folder])
        if len(cls.schemes) == 0:
            print("found schemes dict, but it is empty")
            return
        cls._is_selecting = True
        if len(cls.schemes) == 1:
            # Select the only scheme possible.
            cls._on_done_select_scheme(0)
        else:
            # Ask the user what he/she wants.
            cls.window.show_quick_panel(cls.items,
                                         cls._on_done_select_scheme)

    @classmethod
    def _on_done_select_scheme(cls, index):
        if index == -1:
            cls._is_selecting = False
            return
        cls.name = cls.items[index][0]
        if cls.name == "INVALID SCHEME":
            cls._is_selecting = False
            return
        cls.build_folder_pre_expansion = cls.schemes[index]["build_folder"]
        cls.build_folder = sublime.expand_variables(
            cls.build_folder_pre_expansion, cls.window.extract_variables())
        cls.command_line_overrides = cls.schemes[index].get(
            "command_line_overrides", {})
        cls._select_generator()

    @classmethod
    def _select_generator(cls):
        if cls.generator:
            cls._select_toolset()
            return
        cls.items = []
        for g in capabilities("generators"):
            platform_support = bool(g["platformSupport"])
            toolset_support = bool(g["toolsetSupport"])
            platform_support = "Platform support: {}".format(platform_support)
            toolset_support = "Toolset support: {}".format(toolset_support)
            cls.items.append([g["name"], platform_support, toolset_support])
        if len(cls.items) == 1:
            cls._on_done_select_generator(0)
        else:
            cls.window.show_quick_panel(cls.items,
                                        cls._on_done_select_generator)

    @classmethod
    def _on_done_select_generator(cls, index):
        if index == -1:
            cls._is_selecting = False
            return
        cls.generator = cls.items[index][0]
        platform_support = cls.items[index][1]
        toolset_support = cls.items[index][2]
        cls.platform_support = True if "True" in platform_support else False
        cls.toolset_support = True if "True" in toolset_support else False
        print("CMakeBuilder: Selected generator is", cls.generator)
        if cls.platform_support:
            text = "Platform for {} (Press Enter for default): ".format(
                cls.generator)
            print("CMakeBuilder: Presenting input panel for platform.")
            cls.window.show_input_panel(text, "",
                                        cls._on_done_select_platform,
                                        None, None)
        elif cls.toolset_support:
            cls._select_toolset()
        else:
            cls._run_configure_with_new_settings()

    @classmethod
    def _select_toolset(cls):
        if cls.toolset:
            print("CMakeBuilder: toolset already present:", cls.toolset)
            return
        print("CMakeBuilder: Presenting input panel for toolset.")
        text = "Toolset for {}: (Press Enter for default): ".format(
            cls.generator)
        cls.window.show_input_panel(text, "", cls._on_done_select_toolset,
                                    None, None)

    @classmethod
    def _on_done_select_platform(cls, platform):
        cls.platform = platform
        print("CMakeBuilder: Selected platform is", cls.platform)
        if cls.toolset_support:
            cls._select_toolset()
        else:
            cls._run_configure_with_new_settings()

    @classmethod
    def _on_done_select_toolset(cls, toolset):
        cls.toolset = toolset
        print("CMakeBuilder: Selected toolset is", cls.toolset)
        cls._run_configure_with_new_settings()

    @classmethod
    def _run_configure_with_new_settings(cls):
        cls._is_selecting = False
        cmake_settings = CMakeSettings()
        cmake_settings.source_folder = cls.source_folder
        cmake_settings.build_folder = cls.build_folder

        cmake_settings.build_folder_pre_expansion = \
            cls.build_folder_pre_expansion

        cmake_settings.generator = cls.generator
        cmake_settings.platform = cls.platform
        cmake_settings.toolset = cls.toolset
        cmake_settings.command_line_overrides = cls.command_line_overrides

        if sublime.platform() in ("osx", "linux"):
            cmake_settings.file_regex = \
                r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'
            if "Makefile" in cls.generator:
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
            elif "Ninja" in cls.generator:
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax"
            else:
                print("CMakeBuilder: Warning: Generator", cls.generator,
                      "will not have syntax highlighting in the output panel.")
        elif sublime.platform() == "windows":
            if "Ninja" in cls.generator:
                cmake_settings.file_regex = r'^(.+)\((\d+)\):() (.+)$'
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Ninja+CL.sublime-syntax"
            elif "Visual Studio" in cls.generator:
                cmake_settings.file_regex = \
                    (r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) ',
                     r'\w+\d\d\d\d: .*) \[.*$')
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Visual_Studio.sublime-syntax"
            elif "NMake" in cls.generator:
                cmake_settings.file_regex = r'^(.+)\((\d+)\):() (.+)$'
                cmake_settings.syntax = \
                    "Packages/CMakeBuilder/Syntax/Make.sublime-syntax"
            else:
                print("CMakeBuilder: Warning: Generator", cls.generator,
                      "will not have syntax highlighting in the output panel.")
        else:
            sublime.error_message("Unknown platform: " + sublime.platform())
            return
        path = os.path.join(cls.build_folder, "CMakeFiles", "CMakeBuilder")
        os.makedirs(path, exist_ok=True)
        path = os.path.join(path, "settings.pickle")

        # Unpickle the settings first, if there are any.
        if os.path.isfile(path):
            old_settings = pickle.load(open(path, "rb"))
            if (old_settings.generator != cmake_settings.generator or
                    old_settings.platform != cmake_settings.platform or
                    old_settings.toolset != cmake_settings.toolset):
                print("CMakeBuilder: clearing cache for mismatching generator")
                try:
                    os.remove(os.path.join(cmake_settings.build_folder,
                                           "CMakeCache.txt"))
                except Exception as e:
                    sublime.error_message(str(e))
                    return
        pickle.dump(cmake_settings, open(path, "wb"))
        version = capabilities("version")
        if version["major"] >= 3 and version["minor"] >= 10:
            protocol = (1, 1)
        else:
            protocol = (1, 0)
        print("Chosen protocol is", protocol)
        server = Server(cls.window, cmake_settings, protocol=protocol,
                        on_codemodel_done_handler=cls._codemodel_handler)
        cls.source_folder = ""
        cls.build_folder = ""
        cls.build_folder_pre_expansion = ""
        cls.generator = ""
        cls.platform = ""
        cls.toolset = ""
        cls.items = []
        cls.schemes = []
        cls.command_line_overrides = {}
        cls._servers[cls.window.id()] = server

    @classmethod
    def _codemodel_handler(cls, server):
        view = server.window.active_view()
        if view:
            cls.on_activated(view)
            status = view.get_status("cmake_active_target")
            if not status:
                server.window.run_command(
                    "set_build_system",
                    {"file":
                        "$packages/CMakeBuilder/CMakeBuilder.sublime-build"})
                server.window.run_command("cmake_set_target")

    @classmethod
    def on_activated(cls, view):
        cls.on_load(view)
        try:
            server = cls.get(view.window())
            path = os.path.join(server.cmake.build_folder,
                                "CMakeFiles",
                                "CMakeBuilder",
                                "active_target.txt")
            with open(path, "r") as f:
                active_target = f.read()
            view.set_status("cmake_active_target", "TARGET: " + active_target)
        except Exception as e:
            view.erase_status("cmake_active_target")

    @classmethod
    def on_post_save(cls, view):
        if not view:
            return
        if not get_setting(view, "configure_on_save", False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith(".sublime-project"):
            server = cls.get(view.window())
            if not server:
                _configure(view.window())
            else:
                view.window().run_command("cmake_clear_cache",
                                          {"with_confirmation": False})
                view.window().run_command("cmake_restart_server")
        elif name.endswith("CMakeLists.txt") or name.endswith("CMakeCache.txt"):
            _configure(view.window())
