import sublime
import sublime_plugin
from ..support import get_setting

class ConfigureOnSave(sublime_plugin.EventListener):
    
    def on_activated(self, view):
        if view and view.file_name() and view.file_name().endswith(".sublime-project"):
            settings = view.settings()
            if settings.get("cmake") and settings.get("configure_on_save"):
                settings.add_on_change("cmake", lambda: view.window().run_command("cmake_configure"))

    def on_deactivated(self, view):
        if view and view.file_name() and view.file_name().endswith(".sublime-project"):
            view.settings().clear_on_change("cmake")

    def on_post_save(self, view):
        if not view:
            return
        if not view.settings().get("configure_on_save", False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith("CMakeLists.txt") or name.endswith("CMakeCache.txt"):
            view.window().run_command("cmake_configure")
