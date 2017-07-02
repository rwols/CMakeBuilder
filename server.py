import Default.exec
import json
import sublime

class Server(Default.exec.ProcessListener):

    def __init__(self, 
            source_dir, 
            build_dir, 
            generator, 
            experimental=True, 
            debug=True, 
            protocol=(1,0),
            env={}):
        self.source_dir = source_dir
        self.build_dir = build_dir
        self.generator = generator
        self.experimental = experimental
        self.protocol = protocol
        self.is_configuring = False
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
        self.proc.kill()

    def on_data(self, _, data):
        data = data.decode("utf-8")
        if data.startswith("CMake Error:"):
            sublime.error_message(data)
            return
        import re
        for piece in re.split(
                r'\[== "CMake Server" ==\[|]== "CMake Server" ==]', data):
            if piece == r'\n':
                continue
            try:
                thedict = json.loads(piece)
            except ValueError as e:
                pass
            else:
                self.receive_dict(thedict)

    def on_finished(self, _):
        sublime.active_window().status_message(
            "CMake Server has quit (exit code {})"
            .format(self.proc.exit_code()))

    def send(self, data):
        self.proc.proc.stdin.write(data)
        self.proc.proc.stdin.flush()

    def send_dict(self, thedict):
        data = b'\n[== "CMake Server" ==[\n'
        data += json.dumps(thedict).encode('utf-8') + b'\n'
        data += b'\n]== "CMake Server" ==]\n'
        self.send(data)

    def send_handshake(self):
        best_protocol = self.protocols[0]
        for protocol in self.protocols:
            if (protocol["major"] == self.protocol[0] and 
                protocol["minor"] == self.protocol[1]):
                best_protocol = protocol
                break
            if protocol["isExperimental"] and not self.experimental:
                continue
            if protocol["major"] > best_protocol["major"]:
                best_protocol = protocol
            elif (protocol["major"] == best_protocol["major"] and 
                  protocol["minor"] > best_protocol["minor"]):
                best_protocol = protocol
        self.protocol = best_protocol
        self.send_dict({
            "type": "handshake",
            "protocolVersion": self.protocol,
            "sourceDirectory": self.source_dir,
            "buildDirectory": self.build_dir,
            "generator": self.generator
            })

    def set_global_setting(self, key, value):
        self.send_dict({"type": "setGlobalSettings", key: value})

    def configure(self):
        self.is_configuring = True
        window = sublime.active_window()
        view = window.create_output_panel("cmake.configure", True)
        view.settings().set(
            "result_file_regex", 
            r'CMake\s(?:Error|Warning)(?:\s\(dev\))?\sat\s(.+):(\d+)()\s?\(?(\w*)\)?:')
        view.settings().set("result_base_dir", self.source_dir)
        view.set_syntax_file(
            "Packages/CMakeBuilder/Syntax/Configure.sublime-syntax")
        window.run_command("show_panel", {"panel": "output.cmake.configure"})
        self.send_dict({"type": "configure"})

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
        t = thedict["type"]
        if t == "hello":
            self.protocols = thedict["supportedProtocolVersions"]
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
            sublime.active_window().status_message(
                "CMake server {}.{} at your service!"
                .format(self.protocol["major"], self.protocol["minor"]))
        elif reply == "setGlobalSettings":
            sublime.active_window().status_message(
                "Global CMake setting is modified")
        elif reply == "configure":
            sublime.active_window().status_message("Project is configured")
        elif reply == "compute":
            sublime.active_window().status_message("Project is generated")
            self.is_configuring = False
        elif reply == "codemodel":
            print(thedict)
        elif reply == "fileSystemWatchers":
            self.dump_to_new_view(thedict, "File System Watchers")
        elif reply == "cmakeInputs":
            self.dump_to_new_view(thedict, "CMake Inputs")
        elif reply == "globalSettings":
            thedict.pop("type")
            thedict.pop("inReplyTo")
            thedict.pop("cookie")
            thedict.pop("capabilities")
            self.items = []
            self.types = []
            for k,v in thedict.items():
                if type(v) in (dict, list):
                    continue
                self.items.append([str(k), str(v)])
                self.types.append(type(v))
            window = sublime.active_window()
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
            print("received codemodel reply")
            print(thedict)
        else:
            print("received unknown reply type:", reply)

    def receive_error(self, thedict):
        reply = thedict["inReplyTo"]
        msg = thedict["errorMessage"]
        if reply in ("configure", "compute"):

            sublime.active_window().status_message(msg)
        else:
            sublime.error_message("{} (in reply to {})".format(msg, reply))

    def receive_progress(self, thedict):
        view = sublime.active_window().active_view()
        minimum = thedict["progressMinimum"]
        maximum = thedict["progressMaximum"]
        current = thedict["progressCurrent"]
        if maximum == current:
            view.erase_status("cmake_" + thedict["inReplyTo"])
            if thedict["inReplyTo"] == "configure":
                self.compute()
        else:
            status = "{0} {1:.0f}%".format(
                        thedict["progressMessage"], 
                        100.0 * (float(current) / float(maximum - minimum)))
            view.set_status("cmake_" + thedict["inReplyTo"], status)

    def receive_message(self, thedict):
        window = sublime.active_window()
        if thedict["inReplyTo"] in ("configure", "compute"):
            name = "cmake.configure"
        else:
            name = "cmake." + thedict["inReplyTo"]
        view = window.find_output_panel(name)
        assert view
        window.run_command("show_panel", {"panel": "output.{}".format(name)})
        view = window.find_output_panel(name)
        view.run_command("append", 
            {"characters": thedict["message"] + "\n", 
             "force": True, 
             "scroll_to_end": True})
        
    def receive_signal(self, thedict):
        if thedict["name"] == "dirty" and not self.is_configuring:
            self.configure()
        else:
            print("received signal")
            print(thedict)

    def dump_to_new_view(self, thedict, name):
        view = sublime.active_window().new_file()
        view.set_scratch(True)
        view.set_name(name)
        thedict.pop("type")
        thedict.pop("inReplyTo")
        thedict.pop("cookie")
        view.run_command(
            "append", 
            {"characters": json.dumps(thedict, indent=2), "force": True})
        view.set_read_only(True)
        view.set_syntax_file("Packages/JavaScript/JSON.sublime-syntax")
