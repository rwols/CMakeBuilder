import sublime
import sublime_plugin
from .Generators import get_valid_generators

def plugin_loaded():
    print("""CMakeBuilder: Available commands:

\t[WindowCommand] cmake_build,                     args: { **kwargs }
\t[WindowCommand] cmake_clear_cache_and_configure, args: None
\t[WindowCommand] cmake_clear_cache,               args: { with_confirmation : bool }
\t[WindowCommand] cmake_configure,                 args: None
\t[WindowCommand] cmake_diagnose,                  args: None
\t[WindowCommand] cmake_open_build_folder,         args: None
\t[WindowCommand] cmake_run_ctest,                 args: { extra_args : string, test_framework : string }
\t[WindowCommand] cmake_write_build_targets,       args: None
""")
    print('CMakeBuilder: Available generators for {}:\n'.format(sublime.platform()))
    gens = get_valid_generators()
    for gen in gens:
        print('\t{}'.format(gen))
    print('')  

class ConfigureOnSaveListener(sublime_plugin.EventListener):

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
