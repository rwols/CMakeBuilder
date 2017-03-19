import sublime
import sublime_plugin

class CMakeListsListener(sublime_plugin.EventListener):

    def on_post_save(self, view):
        if not view:
            return
        settings = sublime.load_settings('CMakeBuilder.sublime-settings')
        if not settings.get('configure_on_save', False):
            return
        name = view.file_name()
        if not name:
            return
        if name.endswith('CMakeLists.txt') or name.endswith('CMakeCache.txt'):
            view.window().run_command('cmake_configure')
