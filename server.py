import Default.exec
import json
import sublime
import copy
import time
import os
import pickle
import threading
import shutil


class Target(object):

    __slots__ = ("name", "fullname", "type", "directory", "config")

    def __init__(self, name, fullname, type, directory, config):
        self.name = name
        self.fullname = fullname
        self.type = type
        self.directory = directory
        self.config = config

    def __hash__(self):
        return hash(self.name)

    def cmd(self):
        result = ["cmake", "--build", "."]
        if self.type == "ALL":
            return result
        result.extend(["--target", self.name])
        if self.config:
            result.extend["--config", self.config]
        return result


class Server(Default.exec.ProcessListener):

    def __init__(self,
                 window,
                 cmake_settings,
                 experimental=True,
                 debug=True,
                 protocol=(1, 0),
                 env={}):
        self.window = window
        self.cmake = cmake_settings
        self.experimental = experimental
        self.protocol = protocol
        self.supported_protocols = None
        self.is_configuring = False
        self.is_building = False  # maintained by CmakeBuildCommand
        self.data_parts = ''
        self.inside_json_object = False
        self.include_paths = set()
        self.targets = None
        cmd = ["cmake", "-E", "server"]
        if experimental:
            cmd.append("--experimental")
        if debug:
            cmd.append("--debug")
        self.proc = Default.exec.AsyncProcess(
            cmd=cmd,
            shell_cmd=None,
            listener=self,
            env=env)

    def __del__(self):
        if self.proc:
            self.proc.kill()

    _BEGIN_TOKEN = '[== "CMake Server" ==['
    _END_TOKEN = ']== "CMake Server" ==]'

    def on_data(self, _, data):
        data = data.decode("utf-8").strip()
        if data.startswith("CMake Error:"):
            sublime.error_message(data)
            return

        while data:
            if self.inside_json_object:
                end_index = data.find(self.__class__._END_TOKEN)
                if end_index == -1:
                    # This is okay, wait for more data.
                    self.data_parts += data
                else:
                    self.data_parts += data[0:end_index]
                    data = data[end_index + len(self.__class__._END_TOKEN):]
                    self.__flush_the_data()
            else:  # not inside json object
                begin_index = data.find(self.__class__._BEGIN_TOKEN)
                if begin_index == -1:
                    sublime.error_message(
                        "Received unknown data part: " + data)
                    data = None
                else:
                    begin_token_end = begin_index + len(
                        self.__class__._BEGIN_TOKEN)
                    end_index = data.find(
                        self.__class__._END_TOKEN,
                        begin_token_end)
                    if end_index == -1:
                        # This is okay, wait for more data.
                        self.data_parts += data[begin_token_end:]
                        data = None
                        self.inside_json_object = True
                    else:
                        self.data_parts += data[begin_token_end:end_index]
                        data = data[end_index + len(
                            self.__class__._END_TOKEN):]
                        self.__flush_the_data()

    def __flush_the_data(self):
        d = json.loads(self.data_parts)
        self.data_parts = ""
        self.inside_json_object = False
        self.receive_dict(d)

    def on_finished(self, _):
        self.window.status_message(
            "CMake Server has quit (exit code {})"
            .format(self.proc.exit_code()))

    def send(self, data):
        while not hasattr(self, "proc"):
            time.sleep(0.01)  # terrible hack :(
        self.proc.proc.stdin.write(data)
        self.proc.proc.stdin.flush()

    def send_dict(self, thedict):
        data = b'\n[== "CMake Server" ==[\n'
        data += json.dumps(thedict).encode('utf-8') + b'\n'
        data += b'\n]== "CMake Server" ==]\n'
        self.send(data)

    def send_handshake(self):
        self.protocol = {"major": 1, "minor": 0,
                         "isExperimental": True}
        self.send_dict({
            "type": "handshake",
            "protocolVersion": self.protocol,
            "sourceDirectory": self.cmake.source_folder,
            "buildDirectory": self.cmake.build_folder,
            "generator": self.cmake.generator,
            "platform": self.cmake.platform,
            "toolset": self.cmake.toolset
            })

    def set_global_setting(self, key, value):
        self.send_dict({"type": "setGlobalSettings", key: value})

    def configure(self, cache_arguments={}):
        if self.is_configuring:
            return
        self.is_configuring = True
        self.bad_configure = False
        window = self.window
        view = window.create_output_panel("cmake.configure", True)
        view.settings().set(
            "result_file_regex",
            r'CMake\s(?:Error|Warning)'
            r'(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:')
        view.settings().set("result_base_dir", self.cmake.source_folder)
        view.set_syntax_file(
            "Packages/CMakeBuilder/Syntax/Configure.sublime-syntax")
        settings = sublime.load_settings("CMakeBuilder.sublime-settings")
        if settings.get("server_configure_verbose", False):
            window.run_command("show_panel", {"panel": "output.cmake.configure"})
        overrides = copy.deepcopy(self.cmake.command_line_overrides)
        overrides.update(cache_arguments)
        ovr = []
        for key, value in overrides.items():
            if type(value) is bool:
                value = "ON" if value else "OFF"
            ovr.append("-D{}={}".format(key, value))
        self.send_dict({"type": "configure", "cacheArguments": ovr})

    def compute(self):
        self.send_dict({"type": "compute"})

    def codemodel(self):
        self.send_dict({"type": "codemodel"})

    def cache(self):
        self.send_dict({"type": "cache"})

    def file_system_watchers(self):
        self.send_dict({"type": "fileSystemWatchers"})

    def cmake_inputs(self):
        self.send_dict({"type": "cmakeInputs"})

    def global_settings(self):
        self.send_dict({"type": "globalSettings"})

    def receive_dict(self, thedict):
        t = thedict.pop("type")
        if t == "hello":
            self.supported_protocols = thedict.pop("supportedProtocolVersions")
            self.send_handshake()
        elif t == "reply":
            self.receive_reply(thedict)
        elif t == "error":
            self.receive_error(thedict)
        elif t == "progress":
            self.receive_progress(thedict)
        elif t == "message":
            self.receive_message(thedict)
        elif t == "signal":
            self.receive_signal(thedict)
        else:
            print('CMakeBuilder: Received unknown type "{}"'.format(t))
            print(thedict)

    def receive_reply(self, thedict):
        reply = thedict["inReplyTo"]
        if reply == "handshake":
            self.window.status_message(
                "CMake server protocol {}.{}, handshake is OK"
                .format(self.protocol["major"], self.protocol["minor"]))
            self.configure()
        elif reply == "setGlobalSettings":
            self.window.status_message(
                "Global CMake setting is modified")
        elif reply == "configure":
            if self.bad_configure:
                self.is_configuring = False
                self.window.status_message("Some errors occured during configure!")
            else:
                self.window.status_message("Project is configured")
        elif reply == "compute":
            self.window.status_message("Project is generated")
            self.is_configuring = False
            self.codemodel()
        elif reply == "fileSystemWatchers":
            self.dump_to_new_view(thedict, "File System Watchers")
        elif reply == "cmakeInputs":
            self.dump_to_new_view(thedict, "CMake Inputs")
        elif reply == "globalSettings":
            # thedict.pop("inReplyTo")
            thedict.pop("cookie")
            thedict.pop("capabilities")
            self.items = []
            self.types = []
            for k, v in thedict.items():
                if type(v) in (dict, list):
                    continue
                self.items.append([str(k), str(v)])
                self.types.append(type(v))
            window = self.window

            def on_done(index):
                if index == -1:
                    return
                key = self.items[index][0]
                old_value = self.items[index][1]
                value_type = self.types[index]

                def on_done_input(new_value):
                    if value_type is bool:
                        new_value = bool(new_value)
                    self.set_global_setting(key, new_value)
                window.show_input_panel(
                    'new value for "' + key + '": ',
                    old_value,
                    on_done_input,
                    None,
                    None)
            window.show_quick_panel(self.items, on_done)
        elif reply == "codemodel":
            configurations = thedict.pop("configurations")
            self.include_paths = set()
            self.targets = set()
            for config in configurations:
                # name = config.pop("name")
                projects = config.pop("projects")
                for project in projects:
                    targets = project.pop("targets")
                    for target in targets:
                        target_type = target.pop("type")
                        target_name = target.pop("name")
                        try:
                            target_fullname = target.pop("fullName")
                        except KeyError as e:
                            target_fullname = target_name
                        target_dir = target.pop("buildDirectory")
                        self.targets.add(
                            Target(target_name, target_fullname,
                                   target_type, target_dir, ""))
                        if target_type == "EXECUTABLE":
                            self.targets.add(
                                Target("Run: " + target_name, target_fullname,
                                       "RUN", target_dir, ""))
                        file_groups = target.pop("fileGroups", [])
                        for file_group in file_groups:
                            include_paths = file_group.pop("includePath", [])
                            for include_path in include_paths:
                                path = include_path.pop("path", None)
                                if path:
                                    self.include_paths.add(path)
            self.targets.add(
                Target("BUILD ALL", "BUILD ALL", "ALL",
                       self.cmake.build_folder, ""))
            data = self.window.project_data()
            self.targets = list(self.targets)
            path = os.path.join(self.cmake.build_folder,
                                "compile_commands.json")
            if os.path.isfile(path):
                settings = sublime.load_settings("CMakeBuilder.sublime-settings")
                setting = "auto_update_EasyClangComplete_compile_commands_location"
                if settings.get(setting, False):
                    data["settings"]["ecc_flags_sources"] = [{
                        "file": "compile_commands.json",
                        "search_in": self.cmake.build_folder_pre_expansion}]
                setting = "auto_update_compile_commands_project_setting"
                if settings.get(setting, False):
                    data["settings"]["compile_commands"] = \
                        self.cmake.build_folder_pre_expansion
                setting = "copy_compile_commands_to_project_path"
                if settings.get(setting, False):
                    destination = os.path.join(self.cmake.source_folder,
                                               "compile_commands.json")
                    shutil.copyfile(path, destination)
                self.window.set_project_data(data)
        elif reply == "cache":
            cache = thedict.pop("cache")
            self.items = []
            for item in cache:
                t = item["type"]
                if t in ("INTERNAL", "STATIC"):
                    continue
                try:
                    docstring = item["properties"]["HELPSTRING"]
                except Exception as e:
                    docstring = ""
                key = item["key"]
                value = item["value"]
                self.items.append(
                    [key + " [" + t.lower() + "]", value, docstring])

            def on_done(index):
                if index == -1:
                    return
                item = self.items[index]
                key = item[0].split(" ")[0]
                old_value = item[1]

                def on_done_input(new_value):
                    self.configure({key: value})

                self.window.show_input_panel(
                    'new value for "' + key + '": ',
                    old_value,
                    on_done_input,
                    None,
                    None)

            self.window.show_quick_panel(self.items, on_done)
        else:
            print("received unknown reply type:", reply)

    def receive_error(self, thedict):
        reply = thedict["inReplyTo"]
        msg = thedict["errorMessage"]
        if reply in ("configure", "compute"):
            self.window.status_message(msg)
            if self.is_configuring:
                self.is_configuring = False
        else:
            sublime.error_message("{} (in reply to {})".format(msg, reply))

    def receive_progress(self, thedict):
        view = self.window.active_view()
        minimum = thedict["progressMinimum"]
        maximum = thedict["progressMaximum"]
        current = thedict["progressCurrent"]
        if maximum == current:
            view.erase_status("cmake_" + thedict["inReplyTo"])
            if thedict["inReplyTo"] == "configure" and not self.bad_configure:
                self.compute()
        else:
            status = "{0} {1:.0f}%".format(
                        thedict["progressMessage"],
                        100.0 * (float(current) / float(maximum - minimum)))
            view.set_status("cmake_" + thedict["inReplyTo"], status)

    def receive_message(self, thedict):
        window = self.window
        if thedict["inReplyTo"] in ("configure", "compute"):
            name = "cmake.configure"
        else:
            name = "cmake." + thedict["inReplyTo"]
        view = window.find_output_panel(name)
        assert view
        settings = sublime.load_settings("CMakeBuilder.sublime-settings")
        if settings.get("server_configure_verbose", False):
            window.run_command("show_panel", {"panel": "output.{}".format(name)})
        view.run_command("append", {
            "characters": thedict["message"] + "\n",
            "force": True,
            "scroll_to_end": True})
        self._check_for_errors_in_configure(view)

    _signal_lock = threading.Lock()

    def receive_signal(self, thedict):
        with self.__class__._signal_lock:
            if (thedict["name"] == "dirty" and not
                    self.is_configuring and not
                    self.is_building):
                self.configure()
            else:
                print("received signal")
                print(thedict)

    def dump_to_new_view(self, thedict, name):
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name(name)
        thedict.pop("inReplyTo")
        thedict.pop("cookie")
        view.run_command(
            "append",
            {"characters": json.dumps(thedict, indent=2), "force": True})
        view.set_read_only(True)
        view.set_syntax_file("Packages/JavaScript/JSON.sublime-syntax")

    def _check_for_errors_in_configure(self, view):
        scopes = view.find_by_selector("invalid.illegal")
        errorcount = len(scopes)
        if errorcount > 0:
            self.bad_configure = True
            self.window.run_command("show_panel", {"panel": "output.cmake.configure"})

