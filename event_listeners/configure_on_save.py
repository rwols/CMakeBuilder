import sublime_plugin
from ..support import get_setting
from ..commands import CmakeConfigure2Command


def _configure(window):
    if not CmakeConfigure2Command(window).is_enabled():
        return
    window.run_command("cmake_configure2")


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
