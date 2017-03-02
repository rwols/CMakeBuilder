import sublime, sublime_plugin

class CmakeDiagnoseCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        view = sublime.active_window().new_file()
        view.set_scratch(True)
        view.set_name('CMakeBuilder Diagnosis')
        view.run_command('cmake_insert_diagnosis')
        view.set_read_only(True)
        sublime.active_window().focus_view(view)
