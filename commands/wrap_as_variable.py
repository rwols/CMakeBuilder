import sublime_plugin

class CmakeWrapAsVariableCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        for sel in self.view.sel():
            self.wrap_selection(edit, sel)

    def wrap_selection(self, edit, sel):
        region = self.view.word(sel)
        word = '"${%s}"' % self.view.substr(region)
        self.view.replace(edit, region, word)
