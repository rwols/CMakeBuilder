import sublime, sublime_plugin, os, re
from ..support import *

class CmakeEditCacheCommand(sublime_plugin.WindowCommand):
    """Edit an entry from the CMake cache."""

    def is_enabled(self):
        project = self.window.project_data()
        if project is None:
            return False
        cmake = project.get('cmake')
        if cmake is None:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            return False
        build_folder = cmake.get('build_folder')
        if not build_folder:
            return False
        if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
            return False
        return True

    def description(self):
        return 'Edit Cache...'

    def run(self):
        project = self.window.project_data()
        cmake = project.get('cmake')
        expand_variables(cmake, self.window.extract_variables())
        build_folder = cmake.get('build_folder')
        path = os.path.join(build_folder, 'CMakeCache.txt')
        for view in self.window.views():
            if view.file_name() == path:
                self.window.focus_view(view)
                return
        self.window.open_file(path)

    # def _parse_cache(self, path):
    #     docstring = re.compile(r'^\s*//(.*)$')
    #     comment = re.compile(r'^\s*#.*$')
    #     entry = re.compile(r'^([^:]+):([^=]+)=(.*)$')
    #     self.items = []
    #     print('opening', path)
    #     with open(path, 'r', encoding="utf-8") as f:
    #         for line in f:
    #             match = re.match(comment, line)
    #             if match:
    #                 continue
    #             match = re.match(entry, line)
    #             if match:
    #                 print(match.group(0), match.group(1), match.group(2), match.group(3))
    #                 key = str(match.group(1))
    #                 kind = str(match.group(2))
    #                 if kind == 'INTERNAL':
    #                     doc = ""
    #                     continue
    #                 value = str(match.group(3))
    #                 if doc:
    #                     item = [key, kind, value, doc]
    #                 else:
    #                     item = [key, kind, value, ""]
    #                 self.items.append(item)
    #                 doc = ""
    #             else:
    #                 match = re.match(docstring, line)
    #                 if match:
    #                     doc = str(match.group(1))
    #                 else:
    #                     doc = ""

    # def _on_done(self, index):
    #     if index == -1:
    #         return
    #     item = self.items[index]
    #     key = item[0]
    #     initial_text = item[2]
    #     self.window.show_input_panel('New value for %s: ' % key, initial_text, self._on_done_input, self._on_change, self._on_cancel)

    # def _on_done_input(self, user_input):
    #     print(user_input)
    #     self.window.run_command('cmake_configure')

    # def _on_change(self, user_input):
    #     pass

    # def _on_cancel(self):
    #     pass
