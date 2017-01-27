import sublime, sublime_plugin, os

# Note: Things in "CMakeFiles" folders get removed anyway. This is where you put
# files that should be removed but are not inside CMakeFiles folders.
TRY_TO_REMOVE = [
    'CmakeCache.txt',
    'cmake_install.cmake'
]

class CmakeClearCacheAndConfigureCommand(sublime_plugin.WindowCommand):
    """Clears the CMake-generated files, and then configures the project."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        cmake = project.get('cmake')
        if cmake is None:
            return False
        cmake = sublime.expand_variables(cmake, self.window.extract_variables())
        build_folder = cmake.get('build_folder')
        if not build_folder:
            return False
        return True

    def description(self):
        return 'Clear Cache And Configure'

    def run(self):
        self.window.run_command('cmake_cache_clear', args={'with_confirmation': False})
        self.window.run_command('cmake_configure', args={'write_build_targets': False})
