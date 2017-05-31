import sublime
import sublime_plugin
import functools
from CMakeBuilder.support import get_setting
from CMakeBuilder.commands import CmakeConfigureCommand

def _configure(window):
    if not CmakeConfigureCommand(window).is_enabled(): return
    window.run_command("cmake_configure")

class ConfigureOnSave(sublime_plugin.EventListener):
    
    def on_activated(self, view):
        if view and view.file_name() and view.file_name().endswith(".sublime-project"):
            settings = view.settings()
            if settings.get("cmake") and get_setting(view, "configure_on_save", False):
                settings.add_on_change("cmake", functools.partial(_configure, view.window()))

    def on_deactivated(self, view):
        if view and view.file_name() and view.file_name().endswith(".sublime-project"):
            view.settings().clear_on_change("cmake")

    def on_post_save(self, view):
        if not view:
            return
        if not get_setting(view, "configure_on_save", False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith("CMakeLists.txt") or name.endswith("CMakeCache.txt"):
            _configure(view.window())
