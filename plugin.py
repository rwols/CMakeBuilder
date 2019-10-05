from .vcvarsall import query_vcvarsall
from Default.exec import ExecCommand
from glob import iglob
from os import makedirs
from os.path import dirname
from os.path import isfile
from os.path import join
from os.path import realpath
from tabulate import tabulate  # dependencies.json
import json
import os
import shutil
import sublime
import sublime_plugin
import subprocess

try:
    import Terminus
except ImportError:
    Terminus = None


QUERY = {  # type: Dict[str, Any]
    "requests": [
        {"kind": "codemodel",  "version": 2},
    ]
}


CLIENT_STR = "client-sublimetext"


VISUAL_STUDIO_VERSIONS = [18, 17, 16, 15, 14.1, 14, 13, 12, 11, 10, 9, 8]


class CheckOutputException(Exception):
    """Gets raised when there's a non-empty error stream."""
    def __init__(self, errs):
        super(CheckOutputException, self).__init__()
        self.errs = errs


def check_output(shell_cmd, env=None, cwd=None):
    if sublime.platform() == "linux":
        cmd = ["/bin/bash", "-c", shell_cmd]
        startupinfo = None
        shell = False
    elif sublime.platform() == "osx":
        cmd = ["/bin/bash", "-l", "-c", shell_cmd]
        startupinfo = None
        shell = False
    else:  # sublime.platform() == "windows"
        cmd = shell_cmd
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        shell = True
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        shell=shell,
        cwd=cwd)
    outs, errs = proc.communicate()
    errs = errs.decode("utf-8")
    if errs:
        raise CheckOutputException(errs)
    return outs.decode("utf-8")


__capabilities = None


def plugin_loaded():
    settings = sublime.load_settings("CMakeBuilder.sublime-settings")
    settings.add_on_change("CMakeBuilder", __reload_capabilities)
    __reload_capabilities()


def __reload_capabilities():
    global __capabilities
    try:
        settings = sublime.load_settings("CMakeBuilder.sublime-settings")
        cmake = settings.get("cmake_binary", "cmake")
        command = "{} -E capabilities".format(cmake)
        log("running", command)
        output = check_output(command)
        __capabilities = json.loads(output)
    except Exception as e:
        sublime.error_message("There was an error loading cmake's "
                              "capabilities. Your \"cmake_binary\" setting is "
                              "set to \"{}\". Please make sure that this "
                              "points to a valid cmake executable."
                              .format(cmake))
        log(str(e))
        __capabilities = {"error": None}


def capabilities(key):
    global __capabilities
    if __capabilities is None:
        raise KeyError("Capabilities called too early!")
    elif "error" in __capabilities:
        raise ValueError("Error loading capabilities")
    else:
        return __capabilities.get(key, None)


class Generator:

    def env(self) -> dict:
        if sublime.platform() == "windows":
            arch = "amd64"
            host = "x86" if sublime.arch() == "x32" else "amd64"
            if arch != host:
                arch = host + '_' + arch
            for version in VISUAL_STUDIO_VERSIONS:
                try:
                    vcvars = query_vcvarsall(version, arch)
                    if vcvars:
                        log('found vcvarsall for version', version)
                        return vcvars
                except Exception:
                    log('could not find vsvcarsall for version', version)
                    continue
            log('warning: did not find vcvarsall.bat')
        return {}

    def syntax(self) -> str:
        raise NotImplementedError()

    def regex(self) -> str:
        raise NotImplementedError()


class NinjaGenerator(Generator):

    def syntax(self) -> str:
        if sublime.platform() == "windows":
            return syntax("Ninja+CL")
        else:
            return syntax("Ninja")

    def regex(self) -> str:
        if sublime.platform() == "windows":
            return r'^(.+)\((\d+)\):() (.+)$'
        else:
            return r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'


class UnixMakefilesGenerator(Generator):

    def syntax(self) -> str:
        return syntax("Make")

    def regex(self) -> str:
        return r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'


class NMakeMakefilesGenerator(Generator):

    def syntax(self) -> str:
        return syntax("Make")

    def file_regex(self) -> str:
        return r'^(.+)\((\d+)\):() (.+)$'

class VisualStudioGenerator(Generator):

    def syntax(self) -> str:
        return syntax("Visual_Studio")

    def regex(self) -> str:
        return (r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) ',
                r'\w+\d\d\d\d: .*) \[.*$')


def make_generator(generator_str: str) -> Generator:
    if generator_str == "Ninja":
        return NinjaGenerator()
    elif generator_str == "NMake Makefiles":
        return NMakeMakefilesGenerator()
    elif generator_str == "Visual Studio":
        return VisualStudioGenerator()
    elif generator_str == "Unix Makefiles":
        return UnixMakefilesGenerator()
    raise KeyError("unknown generator")


def file_api(build_folder: str) -> str:
    return join(build_folder, ".cmake", "api", "v1")


def file_api_query(build_folder: str) -> str:
    return join(file_api(build_folder), "query", CLIENT_STR)


def file_api_reply(build_folder: str) -> str:
    return join(file_api(build_folder), "reply")


def ensure_query_path_exists(build_folder: str) -> None:
    makedirs(file_api_query(build_folder), exist_ok=True)


def expand(window: sublime.Window, d: dict) -> dict:
    return sublime.expand_variables(d, window.extract_variables())


def write_query(window: sublime.Window, build_folder: str) -> None:
    ensure_query_path_exists(build_folder)
    with open(join(file_api_query(build_folder), "query.json"), "w") as fp:
        json.dump(QUERY, fp, check_circular=False)


def get_index_file(build_folder: str) -> str:
    path = join(file_api_reply(build_folder), "index-")
    return sorted(iglob(path + "*.json"), reverse=True)[0]


def load_reply(build_folder: str) -> dict:
    with open(get_index_file(build_folder), "r") as fp:
        return json.load(fp)


def get_cmake_generator(cmake: dict) -> str:
    generator = get_cmake_value(cmake, 'generator')
    if generator:
        return generator
    if sublime.platform() == 'windows':
        return 'Visual Studio'
    return 'Unix Makefiles'


def get_setting(view: sublime.View, key, default=None) -> 'Union[bool, str]':
    if view:
        settings = view.settings()
        if settings.has(key):
            return settings.get(key)
    settings = sublime.load_settings('CMakeBuilder.sublime-settings')
    return settings.get(key, default)


def get_cmake_binary() -> str:
    return get_setting(None, "cmake_binary", "cmake")


def get_ctest_binary() -> str:
    return get_setting(None, "ctest_binary", "ctest")


def log(*args) -> None:
    if get_setting(None, "cmake_debug", False):
        print("CMakeBuilder:", *args)


def syntax(name: str) -> str:
    return "Packages/CMakeBuilder/Syntax/{}.sublime-syntax".format(name)


def get_cmake_value(
    the_dict: 'Dict[str, Any]',
    key: str,
    default=None
) -> 'Union[None, bool, str, list, dict]':
    try:
        return the_dict[sublime.platform()][key]
    except KeyError:
        pass
    try:
        return the_dict[key]
    except KeyError:
        return default


class CmakeBuildCommand(ExecCommand):

    def run(
        self,
        generator: str,
        working_dir: str,
        config: str,
        build_target: 'Optional[str]' = None
    ) -> None:
        gen = make_generator(generator)
        cmd = [
            get_cmake_binary(),
            "--build",
            ".",
            "--config",
            config]
        if build_target:
            cmd.extend(["--target", build_target])
        super().run(
            cmd=cmd,
            working_dir=working_dir,
            env=gen.env(),
            syntax=gen.syntax(),
            line_regex=gen.regex())


class CmakeRunCommand(sublime_plugin.WindowCommand):

    def run(self,
        generator: str,
        working_dir: str,
        config: str,
        build_target: str,
        artifact: str,
        debug=False
    ) -> None:
        if not Terminus:
            sublime.error_message(
                'Cannot run executable "{}": You need to install the '
                '"Terminus" package and then restart '
                'Sublime Text'.format(artifact))
            return
        shell = os.environ.get("SHELL")
        if not shell:
            if sublime.platform() == "windows":
                shell = ["cmd.exe"]
            else:
                shell = ["/bin/bash"]
        if sublime.platform() == "windows":
            executable = artifact
        else:
            executable = "./{}".format(artifact)
        cmd = [
            get_cmake_binary(),
            "--build",
            ".",
            "--config",
            config,
            "--target",
            build_target,
            "&&"]
        if debug:
            if sublime.platform() == "linux":
                debugger = ["gdb", "-q", "--args"]
            else:
                debugger = ["lldb", "--"]
            cmd.extend(debugger)
        cmd.append(executable)
        view = self.window.active_view()
        auto_close = get_setting(view, "terminus_auto_close", False)
        use_panel = get_setting(view, "terminus_use_panel", False)
        args = {
            "title": build_target,
            "env": make_generator(generator).env(),
            "cmd": [shell, "-c", ' '.join(cmd)],
            "cwd": working_dir,
            "auto_close": auto_close}
        if use_panel:
            args["panel_name"] = build_target
        self.window.run_command("terminus_open", args)


class CtestRunCommand(ExecCommand):
    def run(self, generator: str, working_dir: str, config: str) -> None:
        gen = make_generator(generator)
        extra_args = get_setting(self.window.active_view(),
                                 "ctest_command_line_args", [])
        cmd = [get_ctest_binary(), "-C", config]
        cmd.extend(extra_args)
        super().run(
            cmd=cmd,
            working_dir=working_dir,
            env=gen.env(),
            syntax=syntax("CTest"))


class CmakeConfigureCommand(ExecCommand):

    def __init__(self, window: sublime.Window) -> None:
        super().__init__(window)
        self.__cmake = None  # type: Optional[Dict[str, Any]]
        self.__unexpanded_build_folder = None  # type: Optional[str]
        self.__build_folder = None  # type: Optional[str]
        self.__overrides = {}  # type: Dict[str, Any]
        self.__generator = None  # type: Optional[str]
        self.__response_handlers = {  # type: Dict[str, Callable]
            "codemodel": self.__handle_response_codemodel,
        }
        self.__build_systems = []  # type: List[Dict[str, Any]]

    def is_enabled(self) -> bool:
        try:
            self.__cmake = self.window.project_data()["settings"]["cmake"]
            self.__unexpanded_build_folder = self.__get_cmake_value(
                "build_folder", None)
            if not self.__unexpanded_build_folder:
                raise KeyError("build_folder key not present")
            self.__cmake = expand(self.window, self.__cmake)
            self.__build_folder = self.__get_cmake_value("build_folder", None)
            self.__overrides = self.__get_cmake_value("command_line_overrides",
                                                      {})
            self.__generator = get_cmake_generator(self.__cmake)
            return True
        except Exception as e:
            self.__cmake = None
            self.__unexpanded_build_folder = None
            self.__build_folder = None
            self.__overrides = {}
            self.__generator = None
            e = str(e)
            if e != "'settings'":
                log(str(e))
            return False

    def description(self) -> str:
        return 'Configure'

    def __convert_overrides_to_list(self) -> 'List[str]':
        result = []  # type: List[str]
        if not self.__overrides:
            return result
        for k, val in self.__overrides.items():
            try:
                if isinstance(val, bool):
                    v = "ON" if val else "OFF"
                else:
                    v = str(val)
                result.append("-D")
                result.append("{}={}".format(k, v))
            except AttributeError as e:
                pass
            except ValueError as e:
                pass
        return result

    def run(self) -> None:
        if capabilities("fileApi") is None:
            sublime.error_message("No support for the file API. "
                "This was introduced in cmake version 3.15. You have "
                "version {}. You can download a recent CMake version from "
                "www.cmake.org".format(capabilities("version")["string"]))
            return
        if get_setting(self.window.active_view(),
                       "always_clear_cache_before_configure", False):
            self.window.run_command("cmake_clear_cache",
                                    {"with_confirmation": False})
        working_dir = self.__get_working_dir()
        # -H and -B are undocumented arguments.
        # See: http://stackoverflow.com/questions/31090821
        cmd = [
            get_cmake_binary(),
            working_dir,
            '-B',
            self.__build_folder]
        if get_setting(self.window.active_view(),
                       'silence_developer_warnings', False):
            cmd.append('-Wno-dev')
        cmd.extend(['-G', self.__generator])
        cmd.extend(self.__convert_overrides_to_list())
        write_query(self.window, self.__build_folder)
        super().run(
            cmd=cmd,
            working_dir=working_dir,
            file_regex=r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:',
            syntax=syntax("Configure"),
            env=make_generator(self.__generator).env())

    def __get_cmake_value(
        self,
        key: str,
        default=None
    ) -> 'Union[None, bool, list, dict]':
        return get_cmake_value(self.__cmake, key, default)

    def __get_working_dir(self):
        working_dir = self.__get_cmake_value('root_folder')
        if working_dir:
            return realpath(working_dir)
        return dirname(self.window.project_file_name())

    def on_finished(self, proc):
        super().on_finished(proc)
        if proc.exit_code() == 0:
            self.__parse_file_api()
            sublime.set_timeout(self.__write_project_data, 0)

    def __parse_file_api(self):
        reply = load_reply(self.__build_folder)
        responses = reply["reply"][CLIENT_STR]["query.json"]["responses"]
        for response in responses:
            try:
                self.__handle_response(response)
            except Exception as e:
                print(e)

    def __load_reply_json_file(self, json_file: str) -> dict:
        path = join(file_api_reply(self.__build_folder), json_file)
        with open(path, "r") as fp:
            return json.load(fp)

    def __handle_response(self, response: dict) -> None:
        data = self.__load_reply_json_file(response["jsonFile"])
        kind = response["kind"]
        handler = self.__response_handlers.get(kind)
        if not handler:
            print('no response handler installed for "{}"'.format(kind))
            return
        handler(data)

    def __handle_response_codemodel(self, data: dict) -> None:
        self.__error = None
        self.__build_systems = []
        try:
            configurations = data["configurations"]
            for configuration in configurations:
                name = configuration["name"]
                if not name:
                    # Single-configuration generator and not CMAKE_BUILD_TYPE
                    # specified in the command line overrides
                    name = "Default"
                build_system = {
                    "name": name,
                    "config": name,
                    "target": "cmake_build",
                    "working_dir": self.__unexpanded_build_folder,
                    "generator": self.__generator}
                targets = configuration["targets"]
                variants = []
                for target in targets:
                    data = self.__load_reply_json_file(target["jsonFile"])
                    self.__handle_target(variants, name, data)
                variants.append({"name": "ctest", "target": "ctest_run"})
                build_system["variants"] = variants
                self.__build_systems.append(build_system)
        except Exception as ex:
            self.__error = ex

    def __handle_target(self, variants: 'List[Dict[str, Any]', config: str,
                        data: dict) -> None:
        name = data["name"]
        variants.append({"name": name, "build_target": name})
        if data["type"] == "EXECUTABLE":
            artifacts = data["artifacts"]
            artifacts = [artifact["path"] for artifact in artifacts]
            variants.append({
                "name": "Run: " + name,
                "build_target": name,
                "target": "cmake_run",
                "artifact": artifacts[0],
                "debug": False})
            if sublime.platform() == "linux":
                variants.append({
                    "name": "Run under GDB: " + name,
                    "build_target": name,
                    "target": "cmake_run",
                    "artifact": artifacts[0],
                    "debug": True})
            elif sublime.platform() == "osx":
                variants.append({
                    "name": "Run uner LLDB: " + name,
                    "build_target": name,
                    "target": "cmake_run",
                    "artifact": artifacts[0],
                    "debug": True})

    def __write_project_data(self) -> None:
        if self.__error:
            sublime.error_message(
                "Error while configuring project: {}".format(
                    str(self.__error)))
            self.__error = None
            self.__build_systems = []
            return
        data = self.window.project_data()
        data.update({"build_systems": self.__build_systems})
        self.window.set_project_data(data)
        self.__build_systems = []


# Note: Things in "CMakeFiles" folders get removed anyway. This is where you put
# files that should be removed but are not inside CMakeFiles folders.
TRY_TO_REMOVE = [
    'CMakeCache.txt',
    'cmake_install.cmake'
]

class CmakeClearCacheCommand(sublime_plugin.WindowCommand):
    """Clears the CMake-generated files"""

    def is_enabled(self):
        try:
            settings = self.window.project_data()["settings"]
            self.__build_folder = settings["cmake"]["build_folder"]
            self.__build_folder = expand(self.window, self.__build_folder)
            return isfile(join(self.__build_folder, "CMakeCache.txt"))
        except Exception as e:
            pass
        return False

    @classmethod
    def description(cls):
        return 'Clear Cache'

    def run(self, with_confirmation=True):
        self.__build_folder = sublime.expand_variables(
            self.window.project_data()["settings"]["cmake"]["build_folder"],
            self.window.extract_variables())
        files_to_remove = []
        dirs_to_remove = []
        cmakefiles_dir = os.path.join(self.__build_folder, 'CMakeFiles')
        if os.path.exists(cmakefiles_dir):
            for root, dirs, files in os.walk(cmakefiles_dir, topdown=False):
                files_to_remove.extend(
                    [os.path.join(root, name) for name in files])
                dirs_to_remove.extend(
                    [os.path.join(root, name) for name in dirs])
            dirs_to_remove.append(cmakefiles_dir)

        def append_file_to_remove(relative_name):
            abs_path = os.path.join(self.__build_folder, relative_name)
            if os.path.exists(abs_path):
                files_to_remove.append(abs_path)

        for file in TRY_TO_REMOVE:
            append_file_to_remove(file)

        if not with_confirmation:
            self.remove(files_to_remove, dirs_to_remove)
            return

        panel = self.window.create_output_panel('files_to_be_deleted')

        self.window.run_command('show_panel',
            {'panel': 'output.files_to_be_deleted'})

        panel.run_command('insert',
            {'characters': 'Files to remove:\n' +
             '\n'.join(files_to_remove + dirs_to_remove)})

        def on_done(selected):
            if selected != 0: return
            self.remove(files_to_remove, dirs_to_remove)
            panel.run_command('append',
                {'characters': '\nCleared CMake cache files!',
                 'scroll_to_end': True})

        self.window.show_quick_panel(['Do it', 'Cancel'], on_done,
            sublime.KEEP_OPEN_ON_FOCUS_LOST)

    def remove(self, files_to_remove, dirs_to_remove):
        for file in files_to_remove:
            try:
                os.remove(file)
            except Exception as e:
                sublime.error_message('Cannot remove '+file)
        for directory in dirs_to_remove:
            try:
                os.rmdir(directory)
            except Exception as e:
                sublime.error_message('Cannot remove '+directory)


class CmakeOpenBuildFolderCommand(sublime_plugin.WindowCommand):
    """Opens the build folder."""

    def is_enabled(self) -> bool:
        try:
            settings = self.window.project_data()["settings"]
            self.__build_folder = settings["cmake"]["build_folder"]
            self.__build_folder = expand(self.window, self.__build_folder)
            return isfile(join(self.__build_folder, "CMakeCache.txt"))
        except Exception as e:
            pass
        return False

    @classmethod
    def description(cls):
        return "Browse Build Folder..."

    def run(self):
        args = {"dir": realpath(self.__build_folder)}
        self.window.run_command("open_dir", args=args)


class CmakeInsertDiagnosisCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.__diagnose(edit)
        self.view.insert(edit, self.view.size(), tabulate(
            self.__table,
            headers=["CHECK", "VALUE", "SUGGESTION/FIX"],
            tablefmt="fancy_grid"))

    def __diagnose(self, edit):
        self.__table = []
        self.__table.append(["cmake binary", get_cmake_binary(), ""])
        try:
            output = check_output(
                "{} --version".format(get_cmake_binary())).splitlines()[0][14:]
        except Exception as e:
            self.__table.append(["cmake present", False, "Install cmake"])
            return
        else:
            self.__table.append(["cmake version", output, ""])

        file_api = capabilities("fileApi")
        if file_api is not None:
            self.__table.append(["File API", True, ""])
        else:
            self.__table.append(["File API", False,
                                "Download cmake version >= 3.15"])
            return

        project = self.view.window().project_data()
        project_filename = self.view.window().project_file_name()

        if project_filename:
            self.__table.append(["project file", project_filename, ""])
        else:
            self.__table.append(["project file", "NOT FOUND",
                                "Open a .sublime-project"])
            return

        cmake = project.get("settings", {}).get("cmake", None)

        if cmake:
            cmake = sublime.expand_variables(
                cmake,
                self.view.window().extract_variables())
            build_folder = cmake['build_folder']
            if build_folder:
                self.__table.append(["cmake dictionary present in settings",
                                    True, ""])
                self.__table.append(["build folder", build_folder, ""])
                overrides = cmake.get("command_line_overrides", None)
                if overrides:
                    self.__table.append(["overrides", overrides, ""])
                cache_file = os.path.join(build_folder, 'CMakeCache.txt')
                if os.path.isfile(cache_file):
                    self.__table.append([
                        "CMakeCache.txt file present", True, ""])
                else:
                    self.__table.append(["CMakeCache.txt file present", False,
                                       "Run the Configure command"])
                    return
            else:
                self.__table.append(["build_folder present in cmake dictionary",
                                    False, "Write a build_folder key"])
        else:
            self.__table.append(["cmake dictionary present in settings", False,
                               "Create a cmake dictionary in your settings"])
            return


class CmakeDiagnoseCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        view = sublime.active_window().new_file()
        view.set_scratch(True)
        view.settings().set("word_wrap", False)
        view.settings().set("line_numbers", False)
        view.settings().set("rulers", [])
        view.settings().set("gutter", False)
        view.settings().set("draw_centered", True)
        view.settings().set("syntax", syntax("Diagnosis"))
        view.set_name("CMakeBuilder Diagnosis")
        view.run_command("cmake_insert_diagnosis")
        view.set_read_only(True)
        sublime.active_window().focus_view(view)

    @classmethod
    def description(cls):
        return "Diagnose (Help! What should I do?)"
