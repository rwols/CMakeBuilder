import sublime
import subprocess
import os


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
