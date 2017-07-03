import sublime
import CMakeBuilder.generators

class Settings(object):
    """Stores the settings defined in the project file. Base class for the
    CMakeGenerator class."""

    @classmethod
    def create(cls, window):
        """Factory method to create a new CMakeGenerator object from a sublime
        Window object."""
        data = window.project_data()["settings"]["cmake"]
        generator_str = data.get("generator", None)
        if not generator_str:
            if sublime.platform() in ("linux", "osx"):
                generator_str = "Unix Makefiles"
            elif sublime.platform() == "windows":
                generator_str = "Visual Studio"
            else:
                raise AttributeError("unknown sublime platform: %s" % sublime.platform())
        generator_class = CMakeBuilder.generators.class_from_generator_string(generator_str)
        return generator_class(window, data)

    def __init__(self, window):
        super(CmakeSettings, self).__init__()
        data = window.project_data()["settings"]["cmake"]
        self.build_folder_pre = data["build_folder"]
        data = sublime.expand_variables(data, window.extract_variables())
        self.build_folder = self._pop(data, "build_folder")
        if not self.build_folder:
            raise KeyError('missing required key "build_folder"')
        self.source_folder = os.path.dirname(window.project_file_name())
        while os.path.isfile(os.path.join(self.source_folder, "..", "CMakeLists.txt")):
            self.source_folder = os.path.join(self.source_folder, "..")
        self.overrides = self._pop(data, "command_line_overrides", {})
        self.filter_targets = self._pop(data, "filter_targets", [])
        self.configurations = self._pop(data, "configurations", [])
        self.env = self._pop(data, "env", {})

    def _pop(self, data, key, default=None):
        return data.get(key, default)
