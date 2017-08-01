import sublime_plugin
import sublime
import os
from ..generators import CMakeGenerator
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
            cmake = CMakeGenerator.create(self.window)
            ServerManager._servers[window_id] = Server(cmake)
        except Exception as e:
            sublime.errror_message(str(e))

    @classmethod
    def description(cls):
        return "Restart Server For This Project"


class ServerManager(sublime_plugin.EventListener):
    """Manages the bijection between cmake-enabled projects and server
    objects."""

    _servers = {}

    @classmethod
    def get(cls, window):
        return cls._servers.get(window.id(), None)

    def on_load(self, view):
        if not capabilities("serverMode"):
            print("CMakeBuilder: cmake is not capable of server mode")
            return
        try:
            window_id = view.window().id()
            cmake = CMakeGenerator.create(view.window())
        except KeyError as e:
            return
        except AttributeError as e:
            return
        except TypeError as e:
            return
        server = self.__class__._servers.get(window_id, None)
        if not server:
            try:
                self.__class__._servers[window_id] = Server(cmake)
            except Exception as e:
                print(str(e))
                return
        elif str(server.cmake) != str(cmake):
            self.__class__._servers[window_id] = Server(cmake)

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
