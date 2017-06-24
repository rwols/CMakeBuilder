import sublime, sublime_plugin

class CmakeDiagnoseCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        view = sublime.active_window().new_file()
        view.set_scratch(True)
        view.settings().set("word_wrap", False)
        view.settings().set("line_numbers", False)
        view.settings().set("rulers", [])
        view.settings().set("gutter", False)
        view.settings().set("draw_centered", True)
        view.settings().set("syntax", 
            "Packages/CMakeBuilder/Syntax/Diagnosis.sublime-syntax")
        view.set_name("CMakeBuilder Diagnosis")
        view.run_command("cmake_insert_diagnosis")
        view.set_read_only(True)
        sublime.active_window().focus_view(view)

    def description(self):
        return "Diagnose (Help! What should I do?)"
