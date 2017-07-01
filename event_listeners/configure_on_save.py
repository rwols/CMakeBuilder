import sublime
import sublime_plugin
import functools
from CMakeBuilder.support import get_setting
from CMakeBuilder.commands import CmakeConfigureCommand

def _configure(window):
    if not CmakeConfigureCommand(window).is_enabled(): return
    window.run_command("cmake_configure")

class ConfigureOnSave(sublime_plugin.EventListener):

    def on_post_save(self, view):
        if not view:
            return
        if not get_setting(view, "configure_on_save", False):
            return
        name = view.file_name()
        if not name:
            return
        if (name.endswith("CMakeLists.txt") or 
            name.endswith("CMakeCache.txt") or 
            name.endswith(".sublime-project")):
            _configure(view.window())
