import os
import sublime
from .command import CmakeCommand


class CmakeSetTargetCommand(CmakeCommand):

    def run(self, index=None, name=None):
        if self.server.is_configuring:
            sublime.error_message("CMake is configuring, please wait.")
            return
        if not self.server.targets:
            sublime.error_message("No targets found! "
                                  "Did you configure the project?")
            return
        if name is not None:
            self._on_done(name)
        elif not index:
            self.items = [
                [t.name, t.type, t.directory] for t in self.server.targets]
            self.window.show_quick_panel(self.items, self._on_done)
        else:
            self._on_done(index)

    def _on_done(self, index):
        if isinstance(index, str):
            self._write_to_file(index)
        elif index == -1:
            self.window.active_view().erase_status("cmake_active_target")
        else:
            name = self.server.targets[index].name
            self._write_to_file(name)

    def _write_to_file(self, name):
        folder = os.path.join(self.server.cmake.build_folder,
                              "CMakeFiles",
                              "CMakeBuilder")
        path = os.path.join(folder, "active_target.txt")
        os.makedirs(folder, exist_ok=True)
        with open(path, "w") as f:
            f.write(name)
        self.window.active_view() \
                   .set_status("cmake_active_target", "TARGET: " + name)

    def description(self):
        return "Set Target..."
