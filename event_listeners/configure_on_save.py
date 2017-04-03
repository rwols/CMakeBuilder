import sublime
import sublime_plugin
from ..support import get_setting

class ConfigureOnSave(sublime_plugin.EventListener):
    
    def on_post_save(self, view):
        if not view:
            return
        if not get_setting(view, 'configure_on_save', False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith('CMakeLists.txt') or name.endswith('CMakeCache.txt'):
            view.window().run_command('cmake_configure')
