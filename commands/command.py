import sublime_plugin
from ..generators import CMakeGenerator
from ..server import Server
from ..support import has_server_mode


class CmakeCommand(sublime_plugin.WindowCommand):

    def is_enabled(self):
        try:
            self.cmake = CMakeGenerator.create(self.window)
        except Exception as e:
            return False
        self.server = ServerManager.get(self.window)
        return self.server is not None and super(sublime_plugin.WindowCommand, self).is_enabled()


class ServerManager(sublime_plugin.EventListener):
    """Manages the bijection between cmake-enabled projects and server 
    objects."""

    _servers = {}

    @classmethod
    def get(cls, window):
        return cls._servers.get(window.id(), None)

    def on_load(self, view):
        if not has_server_mode():
            print("cmake is not capable of server mode")
            return
        try:
            window_id = view.window().id()
            cmake = CMakeGenerator.create(view.window())
        except KeyError as e:
            return
        except AttributeError as e:
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
        index = view.settings().get("active_target", None)
        if not index:
            view.erase_status("cmake_active_target")
            return
        server = self.__class__.get(view.window())
        if not server:
            view.erase_status("cmake_active_target")
            return
        if not server.targets:
            view.erase_status("cmake_active_target")
            return
        view.set_status("cmake_active_target", "TARGET: " + server.targets[int(index)].name)

    on_clone = on_load

    def on_window_command(self, window, command_name, command_args):
        if command_name != "build":
            return None
        server = ServerManager.get(window)
        if not server:
            return None
        return ("cmake_build", command_args)
