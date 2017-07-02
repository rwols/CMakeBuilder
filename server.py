import Default.exec
import json
import sublime

class CmakeServer(Default.exec.ProcessListener):

    def __init__(self, source_dir, build_dir, generator):
        self.source_dir = source_dir
        self.build_dir = build_dir
        self.generator = generator
        self.proc = Default.exec.AsyncProcess(
            cmd=["cmake", "-E", "server", "--experimental", "--debug"], 
            shell_cmd=None, 
            listener=self,
            env={})

    def __del__(self):
        self.proc.kill()

    def on_data(self, _, data):
        import re
        for piece in re.split(r'\[== "CMake Server" ==\[|]== "CMake Server" ==]', data.decode('utf-8')):
            if piece == r'\n':
                continue
            try:
                thedict = json.loads(piece)
            except ValueError as e:
                pass
                # print(str(e),":", piece)
            else:
                self.receive_dict(thedict)
            
        # print(data)
        # start = b'\n[== "CMake Server" ==[\n'
        # end = b'\n]== "CMake Server" ==]\n'
        # first = 0
        # while True:
        #     first = data.find(start, first) + len(start)
        #     if first == -1:
        #         break
        #     last = data.find(end, first)
        #     if last == -1:
        #         break
        #     print(data[first:last])
        #     self.receive_dict(json.loads(data[first:last].decode('utf-8')))

    def on_finished(self, _):
        print("finished with status", self.proc.exit_status())

    def send(self, data):
        self.proc.proc.stdin.write(data)
        self.proc.proc.stdin.flush()

    def send_dict(self, thedict):
        data = b'\n[== "CMake Server" ==[\n'
        data += json.dumps(thedict).encode('utf-8') + b'\n'
        data += b'\n]== "CMake Server" ==]\n'
        self.send(data)

    def send_handshake(self, source_dir, build_dir, generator):
        self.send_dict({
            "type": "handshake",
            "protocolVersion": self.protocols[0],
            "sourceDirectory": source_dir,
            "buildDirectory": build_dir,
            "generator": generator
            })

    def set_global_setting(self, key, value):
        self.send_dict({"type": "setGlobalSettings", key: value})

    def set_global_setting_interactive(self):
        self._global_settings_interactive = True
        self.global_settings()

    def configure(self):
        window = sublime.active_window()
        window.create_output_panel("cmake.configure", True)
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
        print(thedict)
        t = thedict["type"]
        if t == "hello":
            self.protocols = thedict["supportedProtocolVersions"]
            print(self.protocols)
            self.send_handshake(self.source_dir, self.build_dir, self.generator)
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

    def receive_reply(self, thedict):
        reply_to = thedict["inReplyTo"]
        if reply_to == "handshake":
            print("handshake is OK")
        elif reply_to == "setGlobalSettings":
            print("global setting was changed")
        elif reply_to == "configure":
            print("project is configured")
        elif reply_to == "compute":
            print("project is computed")
        elif reply_to == "codemodel":
            print(thedict)
        elif reply_to == "fileSystemWatchers":
            view = sublime.active_window().new_file()
            view.set_scratch(True)
            view.set_name("File System Watchers")
            dirs = thedict["watchedDirectories"]
            files = thedict["watchedFiles"]
            view.run_command("append", {"characters": "watched directories:\n", "force": True})
            for d in dirs:
                view.run_command("append", {"characters": "\t{}\n".format(d), "force": True})
            view.run_command("append", {"characters": "\n\nwatched files:\n", "force": True})
            for f in files:
                view.run_command("append", {"characters": "\t{}\n".format(f), "force": True})
            view.set_read_only(True)
        elif reply_to == "cmakeInputs":
            print(thedict)
        elif reply_to == "globalSettings":
            pass
        else:
            print("received unknown reply type:", reply_to)

    def receive_error(self, thedict):
        sublime.error_message("{} (in reply to {})".format(thedict["errorMessage"], thedict["inReplyTo"]))

    def receive_progress(self, thedict):
        print("received progress")
        print(thedict)
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
        print(thedict)
        window = sublime.active_window()
        if thedict["inReplyTo"] in ("configure", "compute"):
            name = "cmake.configure"
        else:
            name = "cmake." + thedict["inReplyTo"]
        view = window.find_output_panel(name)
        assert view
        window.run_command("show_panel", {"panel": "output.{}".format(name)})
        view = window.find_output_panel(name)
        view.run_command("append", {"characters": thedict["message"] + "\n", "force": True, "scroll_to_end": True})
        
    def receive_signal(self, thedict):
        print("received signal")
        print(thedict)
