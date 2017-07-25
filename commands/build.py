import sublime
import Default.exec
import os
from .command import CmakeCommand, ServerManager


class CmakeExecCommand(Default.exec.ExecCommand):

    def run(self, window_id, **kwargs):
        self.server = ServerManager.get(sublime.Window(window_id))
        if not self.server:
            sublime.error_message("Unable to locate server!")
            return
        self.server.is_building = True
        super().run(**kwargs)

    def on_finished(self, proc):
        super().on_finished(proc)
        self.server.is_building = False


class CmakeBuildCommand(CmakeCommand):

    def run(self, select=False):
        if not self.is_enabled():
            sublime.error_message("Cannot build a CMake target!")
            return
        path = os.path.join(self.server.cmake.build_folder,
                            "CMakeFiles",
                            "CMakeBuilder",
                            "active_target.txt")
        if os.path.exists(path):
            with open(path, "r") as f:
                active_target = int(f.read())
        else:
            active_target = None
        if select or active_target is None:
            if not self.server.targets:
                sublime.error_message(
                    "No targets found. Did you configure the project?")
            self.items = [
                [t.name, t.type, t.directory] for t in self.server.targets]
            self.window.show_quick_panel(self.items, self._on_done)
        else:
            self._on_done(active_target)

    def _on_done(self, index):
        if isinstance(index, str):
            self.window.run_command("cmake_set_target", {"name": index})
            target = None
            for t in self.server.targets:
                if t.name == index:
                    target = t
                    break
        elif isinstance(index, int):
            if index == -1:
                return
            target = self.server.targets[index]
            self.window.run_command("cmake_set_target", {"index": index})
        else:
            sublime.error_message("Unknown type: " + type(index))
            return
        if target.type == "RUN":
            if sublime.platform() in ("linux", "osx"):
                prefix = "./"
            else:
                prefix = ""
            self.window.run_command(
                "cmake_exec", {
                    "window_id": self.window.id(),
                    "shell_cmd": prefix + target.fullname,
                    "working_dir": target.directory
                    }
                )
        else:
            self.window.run_command(
                "cmake_exec", {
                    "window_id": self.window.id(),
                    "cmd": self.cmake.cmd(
                        None if target.type == "ALL" else target),
                    "file_regex": self.cmake.file_regex(),
                    "syntax": self.cmake.syntax(),
                    "working_dir": self.cmake.build_folder
                    }
                )
