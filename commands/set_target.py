from .command import CmakeCommand


class CmakeSetTargetCommand(CmakeCommand):

    def run(self, index=None):
        if not index:
            self.items = [ [t.name, t.type, t.directory] for t in self.server.targets ]
            self.window.show_quick_panel(self.items, self._on_done)
        else:
            self._on_done(index)

    def _on_done(self, index):
        data = self.window.project_data()
        if index == -1:
            data.get("settings", {}).pop("active_target", None)
            self.window.active_view().erase_status("cmake_active_target")
        else:
            data["settings"]["active_target"] = index
            name = self.server.targets[index].name
            self.window.active_view().set_status("cmake_active_target", "TARGET: " + name)
        self.window.set_project_data(data)
