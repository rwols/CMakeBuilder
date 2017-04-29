from .. import CMakeGenerator
import os
import sublime
import subprocess
import sys
import re

from distutils.errors import (DistutilsExecError, DistutilsPlatformError,
                              CompileError, LibError, LinkError)
from distutils.ccompiler import CCompiler, gen_lib_options
from distutils import log
from distutils.util import get_platform

import winreg

class NMake_Makefiles(CMakeGenerator):

    def __repr__(self):
        return 'NMake Makefiles'

    def env(self):
        VS_VERSION = [ 15, 14.1, 14, 13, 12, 11, 10, 9, 8 ]
        for version in VS_VERSION:
            try:
                vcvars = query_vcvarsall(version)
                if vcvars:
                    return vcvars
            except DistutilsPlatformError:
                continue
        return {}

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Make.sublime-syntax'

    def file_regex(self):
        return r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) \w+\d\d\d\d: .*) \[.*$'

    def variants(self):
        lines = subprocess.check_output('cmake --build . --target help',
            cwd=self.build_folder, env=self.env()).decode('utf-8').splitlines()
        variants = []
        EXCLUDES = [
            'are some of the valid targets for this Makefile:',
            'All primary targets available:', 
            'depend',
            'all (the default if no target is provided)',
            'help', 
            'edit_cache', 
            '.ninja', 
            '.o',
            '.i',
            '.s']
            
        for target in lines:
            try:
                if any(exclude in target for exclude in EXCLUDES): 
                    continue
                target = target[4:]
                name = target
                if (self.filter_targets and 
                    not any(f in name for f in self.filter_targets)):
                    continue
                shell_cmd = 'cmake --build . --target {}'.format(target)
                variants.append({'name': name, 'shell_cmd': shell_cmd})
            except Exception as e:
                sublime.error_message(str(e))
                # Continue anyway; we're in a for-loop
        return variants
        

"""distutils.msvc9compiler

Contains MSVCCompiler, an implementation of the abstract CCompiler class
for the Microsoft Visual Studio 2008.

The module is compatible with VS 2005 and VS 2008. You can find legacy support
for older versions of VS in distutils.msvccompiler.
"""

# Written by Perry Stoll
# hacked by Robin Becker and Thomas Heller to do a better job of
#   finding DevStudio (through the registry)
# ported to VS2005 and VS 2008 by Christian Heimes

__revision__ = "$Id$"

RegOpenKeyEx = winreg.OpenKeyEx
RegEnumKey = winreg.EnumKey
RegEnumValue = winreg.EnumValue
RegError = winreg.error

HKEYS = (winreg.HKEY_USERS,
         winreg.HKEY_CURRENT_USER,
         winreg.HKEY_LOCAL_MACHINE,
         winreg.HKEY_CLASSES_ROOT)

NATIVE_WIN64 = (sys.platform == 'win32' and sys.maxsize > 2**32)
if NATIVE_WIN64:
    # Visual C++ is a 32-bit application, so we need to look in
    # the corresponding registry branch, if we're running a
    # 64-bit Python on Win64
    VS_BASE = r"Software\Wow6432Node\Microsoft\VisualStudio\%0.1f"
    VSEXPRESS_BASE = r"Software\Wow6432Node\Microsoft\VCExpress\%0.1f"
    WINSDK_BASE = r"Software\Wow6432Node\Microsoft\Microsoft SDKs\Windows"
    NET_BASE = r"Software\Wow6432Node\Microsoft\.NETFramework"
else:
    VS_BASE = r"Software\Microsoft\VisualStudio\%0.1f"
    VSEXPRESS_BASE = r"Software\Microsoft\VCExpress\%0.1f"
    WINSDK_BASE = r"Software\Microsoft\Microsoft SDKs\Windows"
    NET_BASE = r"Software\Microsoft\.NETFramework"

# A map keyed by get_platform() return values to values accepted by
# 'vcvarsall.bat'.  Note a cross-compile may combine these (eg, 'x86_amd64' is
# the param to cross-compile on x86 targetting amd64.)
PLAT_TO_VCVARS = {
    'win32' : 'x86',
    'win-amd64' : 'amd64',
    'win-ia64' : 'ia64',
}

class Reg:
    """Helper class to read values from the registry
    """

    def get_value(cls, path, key):
        for base in HKEYS:
            d = cls.read_values(base, path)
            if d and key in d:
                return d[key]
        raise KeyError(key)
    get_value = classmethod(get_value)

    def read_keys(cls, base, key):
        """Return list of registry keys."""
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        L = []
        i = 0
        while True:
            try:
                k = RegEnumKey(handle, i)
            except RegError:
                break
            L.append(k)
            i += 1
        return L
    read_keys = classmethod(read_keys)

    def read_values(cls, base, key):
        """Return dict of registry keys and values.

        All names are converted to lowercase.
        """
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        d = {}
        i = 0
        while True:
            try:
                name, value, type = RegEnumValue(handle, i)
            except RegError:
                break
            name = name.lower()
            d[cls.convert_mbcs(name)] = cls.convert_mbcs(value)
            i += 1
        return d
    read_values = classmethod(read_values)

    def convert_mbcs(s):
        dec = getattr(s, "decode", None)
        if dec is not None:
            try:
                s = dec("mbcs")
            except UnicodeError:
                pass
        return s
    convert_mbcs = staticmethod(convert_mbcs)

class MacroExpander:

    def __init__(self, version):
        self.macros = {}
        self.vsbase = VS_BASE % version
        self.load_macros(version)

    def set_macro(self, macro, path, key):
        self.macros["$(%s)" % macro] = Reg.get_value(path, key)

    def load_macros(self, version):
        self.set_macro("VCInstallDir", self.vsbase + r"\Setup\VC", "productdir")
        self.set_macro("VSInstallDir", self.vsbase + r"\Setup\VS", "productdir")
        self.set_macro("FrameworkDir", NET_BASE, "installroot")
        try:
            if version >= 8.0:
                self.set_macro("FrameworkSDKDir", NET_BASE,
                               "sdkinstallrootv2.0")
            else:
                raise KeyError("sdkinstallrootv2.0")
        except KeyError:
            raise DistutilsPlatformError(
            """Python was built with Visual Studio 2008;
extensions must be built with a compiler than can generate compatible binaries.
Visual Studio 2008 was not found on this system. If you have Cygwin installed,
you can try compiling with MingW32, by passing "-c mingw32" to setup.py.""")

        if version >= 9.0:
            self.set_macro("FrameworkVersion", self.vsbase, "clr version")
            self.set_macro("WindowsSdkDir", WINSDK_BASE, "currentinstallfolder")
        else:
            p = r"Software\Microsoft\NET Framework Setup\Product"
            for base in HKEYS:
                try:
                    h = RegOpenKeyEx(base, p)
                except RegError:
                    continue
                key = RegEnumKey(h, 0)
                d = Reg.get_value(base, r"%s\%s" % (p, key))
                self.macros["$(FrameworkVersion)"] = d["version"]

    def sub(self, s):
        for k, v in self.macros.items():
            s = s.replace(k, v)
        return s

def remove_duplicates(variable):
    """Remove duplicate values of an environment variable.
    """
    oldList = variable.split(os.pathsep)
    newList = []
    for i in oldList:
        if i not in newList:
            newList.append(i)
    newVariable = os.pathsep.join(newList)
    return newVariable

def find_vcvarsall(version):
    """Find the vcvarsall.bat file

    At first it tries to find the productdir of VS 2008 in the registry. If
    that fails it falls back to the VS90COMNTOOLS env var.
    """
    vsbase = VS_BASE % version
    try:
        productdir = Reg.get_value(r"%s\Setup\VC" % vsbase,
                                   "productdir")
    except KeyError:
        productdir = None

    # trying Express edition
    if productdir is None:
        vsbase = VSEXPRESS_BASE % version
        try:
            productdir = Reg.get_value(r"%s\Setup\VC" % vsbase,
                                       "productdir")
        except KeyError:
            productdir = None
            log.debug("Unable to find productdir in registry")

    if not productdir or not os.path.isdir(productdir):
        toolskey = "VS%0.f0COMNTOOLS" % version
        toolsdir = os.environ.get(toolskey, None)

        if toolsdir and os.path.isdir(toolsdir):
            productdir = os.path.join(toolsdir, os.pardir, os.pardir, "VC")
            productdir = os.path.abspath(productdir)
            if not os.path.isdir(productdir):
                log.debug("%s is not a valid directory" % productdir)
                return None
        else:
            log.debug("Env var %s is not set or invalid" % toolskey)
    if not productdir:
        log.debug("No productdir found")
        return None
    vcvarsall = os.path.join(productdir, "vcvarsall.bat")
    if os.path.isfile(vcvarsall):
        return vcvarsall
    log.debug("Unable to find vcvarsall.bat")
    return None

def query_vcvarsall(version):
    """Launch vcvarsall.bat and read the settings from its environment
    """
    vcvarsall = find_vcvarsall(version)
    arch = PLAT_TO_VCVARS[get_platform()]
    interesting = set(("INCLUDE", "LIB", "LIBPATH", "Path"))
    result = {}

    if vcvarsall is None:
        raise DistutilsPlatformError("Unable to find vcvarsall.bat")
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    popen = subprocess.Popen('"%s" %s & set' % (vcvarsall, arch),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             startupinfo=startupinfo)

    stdout, stderr = popen.communicate()
    if popen.wait() != 0:
        raise DistutilsPlatformError(stderr.decode("mbcs"))

    stdout = stdout.decode("mbcs")
    for line in stdout.split("\n"):
        line = Reg.convert_mbcs(line)
        if '=' not in line:
            continue
        line = line.strip()
        key, value = line.split('=', 1)
        if key in interesting:
            if value.endswith(os.pathsep):
                value = value[:-1]
            result[key] = remove_duplicates(value)

    if len(result) != len(interesting):
        raise ValueError(str(list(result.keys())))

    return result
