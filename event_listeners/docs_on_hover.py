import sublime_plugin
import sublime
import os
import json

class DocsOnHover(sublime_plugin.ViewEventListener):

    @classmethod
    def is_applicable(cls, settings):
        syntax = settings.get('syntax')
        return False if not syntax else 'cmake' in syntax.lower()

    def __init__(self, view):
        super(DocsOnHover, self).__init__(view)
        self.docs = None

    def load_docs(self):
        path = os.path.join(sublime.packages_path(), 'CMakeBuilder', 'docs.json')
        if not os.path.isfile(path):
            self.docs = {}
            print('CMakeBuilder: Error: Could not load documentation!')
            return
        with open(path) as f:
            self.docs = json.load(f)

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not self.view.match_selector(point, 'source.cmake'):
            return
        if not self.docs:
            self.load_docs()
        word = self.view.substr(self.view.word(point))
        doc = self.docs.get(word, None)
        if not doc:
            return
        flags = sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HIDE_ON_MOUSE_MOVE_AWAY
        self.view.show_popup(doc, flags, point)
