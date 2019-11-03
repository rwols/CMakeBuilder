from Default.exec import ExecCommand  # type: ignore
from glob import iglob
from os import makedirs
from os.path import dirname
from os.path import isfile
from os.path import join
from os.path import realpath
from tabulate import tabulate  # dependencies.json
import json
import os
import shlex
import sublime  # type: ignore
import sublime_plugin  # type: ignore
import subprocess

try:
    from typing import Dict, List, Union, Optional, Any, Callable
    assert Dict and List and Union and Optional and Any and Callable
except ImportError:
    pass

try:
    import Terminus  # type: ignore
except ImportError:
    Terminus = None


QUERY = {
    "requests": [
        {"kind": "codemodel",  "version": 2},
    ]
}  # type: Dict[str, Any]


CLIENT_STR = "client-sublimetext"


class CheckOutputException(Exception):
    """Gets raised when there's a non-empty error stream."""
    def __init__(self, errs):
        super(CheckOutputException, self).__init__()
        self.errs = errs

    def __str__(self) -> str:
        return self.errs


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


def get_environment_from_batch_command(env_cmd) -> 'Dict[str, str]':
    shell = os.environ["COMSPEC"]
    result = {}
    cmd = '{shell} /s /c "{env_cmd}" & set'.format(**vars())
    out = check_output(cmd)
    for line in out.split("\n"):
        if '=' not in line:
            continue
        line = line.strip()
        key, value = line.split('=', 1)
        key = key.lower()
        if key in ("include", "lib", "libpath", "path"):
            if value.endswith(os.pathsep):
                value = value[:-1]
            result[key] = value
    return result


def get_vcvarsall_path(desired_vs_major_version: int) -> str:
    if desired_vs_major_version < 15:
        raise ValueError("major versions less than 15 (2017) are not supported")
    for vs in get_all_vs_installed_versions():
        path = vs["path"]
        version = vs["version"]
        major_version = int(version.split(".")[0])
        if major_version == desired_vs_major_version:
            return join(path, "VC", "Auxiliary", "Build", "vcvarsall.bat")
    raise RuntimeError("cannot find a visual studio SDK for major version"
                       " {}".format(desired_vs_major_version))


def parse_vcvarsall(vcvarsall_path: str,
                    target_architecture: str,
                    host_architecture: str) -> 'Dict[str, str]':
    if host_architecture == target_architecture:
        arg = host_architecture
    else:
        arg = "{}_{}".format(host_architecture, target_architecture)
    env_cmd = '"{}" {}'.format(vcvarsall_path, arg)
    shell = os.environ["COMSPEC"]
    out = check_output('{} /s /c "{}" & set'.format(shell, env_cmd))
    result = {}
    for line in out.split("\n"):
        if '=' not in line:
            continue
        line = line.strip()
        key, value = line.split('=', 1)
        key = key.lower()
        if key in ("include", "lib", "libpath", "path"):
            if value.endswith(os.pathsep):
                value = value[:-1]
            result[key] = value
    return result


def get_vs_env(desired_vs_major_version: int,
               host_architecture: str,
               target_architecture: str) -> 'Dict[str, str]':
    return parse_vcvarsall(
        get_vcvarsall_path(desired_vs_major_version),
        host_architecture,
        target_architecture)


def get_vs_env_from_generator_str(
    generator_str: str,
    host_architecture: str,
    target_architecture: str
) -> 'Dict[str, str]':
    return get_vs_env(
        get_vs_major_version_from_generator_str(generator_str),
        host_architecture,
        target_architecture)


def get_vs_major_version_from_generator_str(generator_str: str) -> int:
    if generator_str == "Ninja":
        generator_str = get_default_vs_generator_name()
    words = generator_str.split()
    if len(words) > 2:
        return int(words[2])
    raise RuntimeError("unexpected generator string: {}".format(generator_str))


def cmake_arch_to_vs_arch(arch: str) -> str:
    if arch == "x64":
        return "amd64"
    elif arch == "x86":
        return "x86"
    elif arch == "arm":
        return "arm"
    raise ValueError("unknown platform/toolset architecture: {}".format(arch))


def get_all_vs_generator_names():
    result = []
    for gen in capabilities("generators"):
        name = gen["name"]
        if name.startswith("Visual Studio"):
            if not name.endswith("Win64") and not name.endswith("ARM"):
                result.append(name)
    return result

def get_all_vs_installed_versions():
    cwd = join(os.environ["PROGRAMFILES(X86)"], "Microsoft Visual Studio",
               "Installer")
    cmd = "vswhere.exe -prerelease -legacy -format json -utf8"
    data = json.loads(check_output(cmd, cwd=cwd))
    return [{"path": vs["installationPath"],
             "version": vs["installationVersion"]} for vs in data]


def get_default_vs_generator_name():
    names = get_all_vs_generator_names()
    f = get_vs_major_version_from_generator_str
    versions = [f(n) for n in names]
    installed = get_all_vs_installed_versions()
    for ver, name in sorted(zip(versions, names), reverse=True):
        for installation in installed:
            if installation["version"].startswith(str(ver)):
                return name


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
        __capabilities = json.loads(check_output(command))
    except Exception as e:
        msg = ["There was an error loading cmake's capabilities.",
            "Your \"cmake_binary\" setting is set to \"{}\".".format(cmake),
            "Please make sure that this points to a valid cmake executable."]
        if sublime.platform() == "osx":
            msg.append("Alternatively, it is possible that your ~/.bash_profile is broken.")
        sublime.error_message(" ".join(msg))
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
        return r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) \w+\d\d\d\d: .*) \[.*$'


def make_generator(build_folder: str, generator: 'Optional[str]') -> Generator:
    if generator is None:
        generator = load_reply(build_folder)["cmake"]["generator"]["name"]
    if generator == "Ninja":
        return NinjaGenerator()
    elif generator == "NMake Makefiles":
        return NMakeMakefilesGenerator()
    elif generator.startswith("Visual Studio"):
        return VisualStudioGenerator()
    elif generator == "Unix Makefiles":
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


def expand(window: sublime.Window, d) -> 'Any':
    return sublime.expand_variables(d, window.extract_variables())


def write_query(window: sublime.Window, build_folder: str) -> None:
    ensure_query_path_exists(build_folder)
    with open(join(file_api_query(build_folder), "query.json"), "w") as fp:
        json.dump(QUERY, fp, check_circular=False)


def get_index_file(build_folder: str) -> str:
    path = join(file_api_reply(build_folder), "index-")
    # Whenever a new index file is generated it is given a new name and any old
    # one is deleted. During the short time between these steps there may be
    # multiple index files present; the one with the largest name in
    # lexicographic order is the current index file.
    return sorted(iglob(path + "*.json"), reverse=True)[0]


def load_reply(build_folder: str) -> dict:
    with open(get_index_file(build_folder), "r") as fp:
        return json.load(fp)


def get_cmake_generator(view: sublime.View, cmake: dict) -> 'Optional[str]':
    key = "default_{}_generator".format(sublime.platform())
    default_gen = get_setting(view, key)
    if default_gen is None:
        if sublime.platform() == "windows":
            default_gen = get_default_vs_generator_name()
    return get_cmake_value(cmake, 'generator', default_gen)


def get_setting(view: sublime.View, key, default=None) -> 'Union[bool, str]':
    if view:
        settings = view.settings()
        if settings.has(key):
            return settings.get(key)
    settings = sublime.load_settings('CMakeBuilder.sublime-settings')
    return settings.get(key, default)


def get_cmake_binary() -> str:
    return str(get_setting(None, "cmake_binary", "cmake"))


def get_ctest_binary() -> str:
    return str(get_setting(None, "ctest_binary", "ctest"))


def log(*args) -> None:
    if get_setting(None, "cmake_debug", False):
        print("CMakeBuilder:", *args)


def syntax(name: str) -> str:
    return "Packages/CMakeBuilder/Syntax/{}.sublime-syntax".format(name)


def get_cmake_value(
    the_dict: 'Dict[str, Any]',
    key: str,
    default=None
) -> 'Any':
    try:
        return the_dict[sublime.platform()][key]
    except KeyError:
        pass
    try:
        return the_dict[key]
    except KeyError:
        return default


def get_cmake_env(window: sublime.Window) -> 'Dict[str, str]':
    try:
        data = window.project_data()
        cmake = data["settings"]["cmake"]
        return get_cmake_value(cmake, "env", {})
    except Exception:
        return {}


class CmakeBuildCommand(ExecCommand):

    def run(
        self,
        working_dir: str,
        config: str,
        env: 'Dict[str, str]',
        build_target: 'Optional[str]' = None,
        generator: 'Optional[str]' = None,
    ) -> None:
        gen = make_generator(working_dir, generator)
        cmd = [get_cmake_binary(), "--build", ".", "--config", config]
        if build_target:
            cmd.extend(["--target", build_target])
        super().run(
            cmd=cmd,
            working_dir=working_dir,
            env=env,
            syntax=gen.syntax(),
            file_regex=gen.regex())


cached_command_line_args = ""


class CommandLineArgumentsInputHandler(sublime_plugin.TextInputHandler):

    @classmethod
    def initial_text(cls) -> str:
        return cached_command_line_args

    def confirm(self, text: str) -> None:
        global cached_command_line_args
        cached_command_line_args = text


class CmakeRunCommand(sublime_plugin.WindowCommand):

    def on_done(self, command_line_args: str) -> None:
        global cached_command_line_args
        cached_command_line_args = command_line_args
        if sublime.platform() == "windows":
            posix = False
            shell = ["cmd.exe", "/C"]
            executable = ".\\{}".format(self.artifact.replace("/", "\\"))
            conjunction = "&"
            debugger = []  # type: List[str]
            if self.debug:
                sublime.error_message(
                    "There is no support for WinDbg.exe, because I have not "
                    "found a need for it. If you want to use WinDbg.exe, "
                    "consider contributing on github.com/rwols/CMakeBuilder")
                return
        else:
            posix = True
            shell = ["/bin/bash", "-c"]
            executable = "./{}".format(self.artifact)
            conjunction = "&&"
            if sublime.platform() == "linux":
                debugger = ["gdb", "-q", "--args"] if self.debug else []
            else: # osx
                debugger = ["lldb", "--"] if self.debug else []
        view = self.window.active_view()
        cmd = [get_cmake_binary(), "--build", ".", "--config", self.config,
               "--target", self.build_target, conjunction]
        cmd.extend(debugger)
        cmd.append(executable)
        cmd.extend(shlex.split(command_line_args, posix=posix))
        cmd = shell + [" ".join(cmd)]
        args = {
            "title": self.build_target,
            "env": self.env,
            "cmd": cmd,
            "cwd": self.working_dir,
            "auto_close": get_setting(view, "terminus_auto_close", False)}
        if get_setting(view, "terminus_use_panel", False):
            args["panel_name"] = self.build_target
        self.window.run_command("terminus_open", args)

    def run(
        self,
        working_dir: str,
        config: str,
        env: 'Dict[str, str]',
        build_target: str,
        artifact: str,
        generator: 'Optional[str]' = None,
        debug=False,
    ) -> None:
        if not Terminus:
            sublime.error_message(
                'Cannot run executable "{}": You need to install the '
                '"Terminus" package and then restart '
                'Sublime Text'.format(artifact))
            return
        self.working_dir = working_dir
        self.config = config
        self.env = env
        self.build_target = build_target
        self.artifact = artifact
        self.generator = generator
        self.debug = debug
        self.window.show_input_panel("Command Line Arguments: ",
                                     cached_command_line_args, self.on_done,
                                     None, None)


class CtestRunCommand(ExecCommand):
    def run(
        self,
        env: 'Dict[str, str]',
        working_dir: str,
        config: str,
        generator: 'Optional[str]' = None,
    ) -> None:
        extra_args = get_setting(self.window.active_view(),
                                 "ctest_command_line_args", "")
        super().run(
            cmd=[get_ctest_binary(), "-C", config] + [str(extra_args)],
            working_dir=working_dir,
            env=env,
            syntax=syntax("CTest"))


class CmakeInfo:

    __slots__ = ("unexpanded_build_folder", "build_folder", "overrides",
                 "generator", "platform", "toolset", "env", "vs_major_version",
                 "working_dir", "__data", "window")

    def __init__(self, window: sublime.Window) -> None:
        self.window = window
        try:
            self.__data = window.project_data()["settings"]["cmake"]
        except Exception:
            default = get_setting(window.active_view(), "default_build_folder",
                                  "$folder/build")
            self.__data = {"build_folder": default}
        self.unexpanded_build_folder = self.__get_val("build_folder")  # type: str
        self.__data = expand(window, self.__data)
        self.build_folder = self.__get_val("build_folder")  # type: str
        self.working_dir = self.__get_val("root_folder")  # type: str
        if self.working_dir:
            self.working_dir = realpath(self.working_dir)
        else:
            try:
                self.working_dir = window.extract_variables()["folder"]
            except KeyError:
                self.working_dir = ""
        if not isfile(join(self.working_dir, "CMakeLists.txt")):
            raise FileNotFoundError()

    def __get_val(self, key: str, default: 'Any' = None) -> 'Any':
        return get_cmake_value(self.__data, key, default)

    def load(self) -> None:
        self.overrides = self.__get_val("command_line_overrides", {})  # type: Dict[str, str]
        self.generator = get_cmake_generator(self.window.active_view(), self.__data)
        self.platform = self.__get_val("platform")  # type: Optional[str]
        self.toolset = self.__get_val("toolset")  # type: Dict[str, str]
        self.vs_major_version = self.__get_val("vs_major_version")  # type: int
        if not self.vs_major_version:
            versions = self.__get_val("visual_studio_versions", [])  # type: List[int]
            if versions:
                self.vs_major_version = versions[0]
        self.env = self.__get_val("env", {})  # type: Dict[str, str]
        if sublime.platform() == "windows":
            self.__update_windows_environment(self.__data)

    def to_command(self) -> 'List[str]':
        cmd = [get_cmake_binary(), ".", "-B", self.build_folder]
        if self.generator:
            cmd.extend(["-G", self.generator])
        if self.platform:
            cmd.extend(["-A", self.platform])
        if self.toolset:
            cmd.append(self.__convert_toolset_to_str())
        if self.overrides:
            cmd.extend(self.__convert_overrides_to_list())
        return cmd

    def __str__(self) -> str:
        return " ".join(self.to_command())

    def __convert_toolset_to_str(self) -> str:
        items = ["{}={}".format(*kv) for kv in self.toolset.items()]
        return "-T{}".format(",".join(items))

    def __convert_overrides_to_list(self) -> 'List[str]':
        result = []  # type: List[str]
        for k, val in self.overrides.items():
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

    def __update_windows_environment(self, data: 'Dict[str, Any]') -> None:
        if not self.generator:
            self.generator = get_default_vs_generator_name()
        if self.toolset:
            host_arch = self.toolset.get("host", sublime.arch())
        else:
            host_arch = "x64"
        target_arch = self.platform if self.platform else "x64"
        old_target_arch = get_cmake_value(data, "target_architecture")
        if old_target_arch:
            if old_target_arch == "amd64":
                target_arch = "x64"
            else:
                target_arch = old_target_arch
        host_arch = cmake_arch_to_vs_arch(host_arch)
        target_arch = cmake_arch_to_vs_arch(target_arch)
        if self.vs_major_version:
            env = get_vs_env(self.vs_major_version, host_arch, target_arch)
        else:
            assert self.generator
            env = get_vs_env_from_generator_str(self.generator, host_arch,
                                                target_arch)
        self.env.update(env)


class CmakeConfigureCommand(ExecCommand):

    def __init__(self, window: sublime.Window) -> None:
        super().__init__(window)
        self.info = None  # type: Optional[CmakeInfo]
        self.__build_systems = []  # type: List[Dict[str, Any]]
        self.__error = None  # type: Optional[Exception]
        self.__response_handlers = {
            "codemodel": self.__handle_response_codemodel
        }  # type: Dict[str, Callable]

    def is_enabled(self) -> bool:
        try:
            self.info = CmakeInfo(self.window)
        except FileNotFoundError:
            return False
        return True

    def description(self) -> str:
        return 'Configure'

    def run(self) -> None:
        if self.info is None:
            assert self.is_enabled()
        assert self.info is not None
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
        self.info.load()
        cmd = self.info.to_command()
        if get_setting(self.window.active_view(),
                       "silence_developer_warnings", False):
            cmd.append("-Wno-dev")
        write_query(self.window, self.info.build_folder)
        self.window.status_message("Generating build system...")
        super().run(
            cmd=cmd,
            working_dir=self.info.working_dir,
            file_regex=r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:',
            syntax=syntax("Configure"),
            env=self.info.env)

    def on_finished(self, proc):
        log("finished running cmake")
        super().on_finished(proc)
        exit_code = proc.exit_code()
        if exit_code == 0 or exit_code is None:
            self.window.status_message("Translating...")
            self.__parse_file_api()
            sublime.set_timeout(self.__write_project_data, 0)
        else:
            self.__erase_status()
            log("exited with an error")

    def __parse_file_api(self):
        log("parsing file api response")
        reply = load_reply(self.info.build_folder)
        responses = reply["reply"][CLIENT_STR]["query.json"]["responses"]
        for response in responses:
            try:
                self.__handle_response(response)
            except Exception as e:
                sublime.error_message("Error parsing response: {}".format(e))

    def __load_reply_json_file(self, json_file: str) -> dict:
        assert self.info
        path = join(file_api_reply(self.info.build_folder), json_file)
        with open(path, "r") as fp:
            return json.load(fp)

    def __handle_response(self, response: dict) -> None:
        data = self.__load_reply_json_file(response["jsonFile"])
        kind = response["kind"]
        handler = self.__response_handlers.get(kind)
        if not handler:
            log('no response handler installed for "{}"'.format(kind))
            return
        handler(data)

    def __handle_response_codemodel(self, data: dict) -> None:
        log("parsing codemodel")
        self.__error = None
        self.__build_systems = []
        assert self.info
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
                    "working_dir": self.info.unexpanded_build_folder,
                    "env": self.info.env}
                if self.info.generator:
                    build_system["generator"] = self.info.generator
                targets = configuration["targets"]
                variants = []  # type: List[Dict[str, Any]]
                for target in targets:
                    data = self.__load_reply_json_file(target["jsonFile"])
                    self.__handle_target(variants, name, data)
                variants.append({"name": "ctest", "target": "ctest_run"})
                build_system["variants"] = variants
                self.__build_systems.append(build_system)
        except Exception as ex:
            self.__error = ex

    def __handle_target(self, variants: 'List[Dict[str, Any]]', config: str,
                        data: dict) -> None:
        name = data["name"]
        log("parsing target", name, "for config", config)
        variants.append({"name": name, "build_target": name})
        if data["type"] == "EXECUTABLE":
            artifacts = data["artifacts"]
            name_on_disk = data["nameOnDisk"]
            artifacts = [a["path"] for a in artifacts
                         if a["path"].endswith(name_on_disk)]
            if len(artifacts) == 0:
                log("no suitable artifact for target", name)
                return
            if len(artifacts) > 1:
                log("too many candidate artifacts for target", name)
                return
            variants.append({
                "name": "Run: " + name,
                "build_target": name,
                "target": "cmake_run",
                "artifact": artifacts[0]})
            if sublime.platform() == "linux":
                variants.append({
                    "name": "Run under GDB: " + name,
                    "build_target": name,
                    "target": "cmake_run",
                    "artifact": artifacts[0],
                    "debug": True})
            elif sublime.platform() == "osx":
                variants.append({
                    "name": "Run under LLDB: " + name,
                    "build_target": name,
                    "target": "cmake_run",
                    "artifact": artifacts[0],
                    "debug": True})

    def __write_project_data(self) -> None:
        if self.__error:
            sublime.error_message(
                "Error while configuring project: {}".format(
                    str(self.__error)))
            return
        log("writing project data")
        data = self.window.project_data()

        def is_not_generated_by_us(d):
            return "cmake_build" != d.get("target", "foo")

        bs = filter(is_not_generated_by_us, data.get("build_systems", []))
        data.update({"build_systems": list(bs) + self.__build_systems})
        self.window.set_project_data(data)
        self.window.status_message(
            "Generated build system! Select it in [Tools] -> [Build system]")


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
            self.info = CmakeInfo(self.window)
        except FileNotFoundError:
            return False
        return True

    @classmethod
    def description(cls):
        return 'Clear Cache'

    def run(self, with_confirmation=True):
        assert self.info
        build_folder = self.info.build_folder
        files_to_remove = []
        dirs_to_remove = []
        cmakefiles_dir = os.path.join(build_folder, 'CMakeFiles')
        if os.path.exists(cmakefiles_dir):
            for root, dirs, files in os.walk(cmakefiles_dir, topdown=False):
                files_to_remove.extend(
                    [os.path.join(root, name) for name in files])
                dirs_to_remove.extend(
                    [os.path.join(root, name) for name in dirs])
            dirs_to_remove.append(cmakefiles_dir)

        def append_file_to_remove(relative_name):
            abs_path = os.path.join(build_folder, relative_name)
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
            self.info = CmakeInfo(self.window)
        except FileNotFoundError:
            return False
        return True

    @classmethod
    def description(cls):
        return "Browse Build Folder..."

    def run(self):
        if not self.info:
            if not self.is_enabled():
                return
        args = {"dir": realpath(self.info.build_folder)}
        self.window.run_command("open_dir", args=args)


class CmakeInsertDiagnosisCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.__table = []
        if   not self.__check_cmake_binary():   pass
        elif not self.__check_cmake_version():  pass
        elif not self.__check_cmake_settings(): pass
        self.view.insert(edit, self.view.size(), tabulate(
            self.__table,
            headers=["CHECK", "VALUE", "SUGGESTION/FIX"],
            tablefmt="fancy_grid"))

    def __check_cmake_binary(self) -> bool:
        self.__table.append(["cmake binary", get_cmake_binary(), ""])
        return True

    def __append(self, info: str, success: bool, suggestion: str) -> None:
        self.__table.append([info, success, suggestion])

    def __ok(self, key: str, val: 'Any') -> None:
        self.__append(key, val, "")

    def __fail(self, key: str, suggestion: str) -> None:
        self.__append(key, False, suggestion)

    def __check_cmake_version(self) -> bool:
        try:
            output = check_output(
                "{} --version".format(get_cmake_binary())).splitlines()[0][14:]
        except Exception as e:
            self.__fail("cmake present", "Install cmake")
            return False
        else:
            self.__ok("cmake version", output)
        file_api = capabilities("fileApi")
        if file_api is not None:
            self.__ok("File API", True)
        else:
            self.__fail("File API", "Download cmake version >= 3.15")
            return False
        return True

    def __check_cmake_settings(self) -> bool:
        try:
            info = CmakeInfo(self.view.window())
            info.load()
        except FileNotFoundError:
            self.__fail("CMakeLists.txt present",
                        "Make sure you have a CMakeLists.txt")
            return False
        self.__ok("build_folder", info.build_folder)
        self.__ok("generator", info.generator)
        if info.platform:
            self.__ok("platform", info.platform)
        if info.toolset:
            self.__ok("toolset", info.toolset)
        if info.vs_major_version:
            self.__ok("selected vs major ver", info.vs_major_version)
        self.__ok("command to be run", info)
        return True


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
