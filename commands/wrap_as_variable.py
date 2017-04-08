import sublime_plugin
import sublime

class CmakeWrapAsVariableCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        for sel in self.view.sel():
            self.wrap_selection(edit, sel)

    def wrap_selection(self, edit, sel):
        print('\n')
        word = self.view.substr(sublime.Region(sel.b - 1, sel.b))
        # if sel.a == sel.b:
        #     word = self.view.substr(sublime.Region(sel.a - 1, sel.b))
        #     print(word)
        if word == '}':
            sel = sublime.Region(sel.a, sel.b - 1)
        elif word == '"':
            sel = sublime.Region(sel.a, sel.b - 2)
        region = self.view.word(sel)
        expanded_region = sublime.Region(region.a - 2, region.b + 1)
        word = self.view.substr(region)
        expanded_word = self.view.substr(expanded_region)
        print(word)
        print(expanded_word)
        if expanded_word.startswith('${') and expanded_word.endswith('}'):
            expanded_word = '"%s"' % expanded_word
            self.view.replace(edit, expanded_region, expanded_word)
        else:
            word = '${%s}' % word
            self.view.replace(edit, region, word)
        
