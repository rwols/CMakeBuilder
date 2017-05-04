from .. import CMakeGenerator
from .support.vcvarsall import query_vcvarsall
import os
import sublime
import subprocess

class Ninja(CMakeGenerator):

    def __repr__(self):
        return 'Ninja'

    def env(self):
        if self.visual_studio_versions:
            vs_versions = self.visual_studio_versions
        else:
            vs_versions = [ 15, 14.1, 14, 13, 12, 11, 10, 9, 8 ]
        if self.target_architecture:
            arch = self.target_architecture
        else:
            arch = 'x86'
        if sublime.arch() == 'x32':
            host = 'x86'
        elif sublime.arch() == 'x64':
            host = 'amd64'
        else:
            sublime.error_message('Unknown Sublime architecture: %s' % sublime.arch())
            return
        if arch != host:
            arch = host + '_' + arch
        for version in vs_versions:
            try:
                vcvars = query_vcvarsall(version, arch)
                if vcvars:
                    print('found vcvarsall for version', version)
                    return vcvars
            except Exception:
                print('could not find vsvcarsall for version', version)
                continue
        print('warning: did not find vcvarsall.bat')
        return {}

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Ninja+CL.sublime-syntax'

    def file_regex(self):
        return r'^(.+)\((\d+)\):() (.+)$'
    
    def variants(self):

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        lines = subprocess.check_output(
            'cmake --build . --target help', 
            cwd=self.build_folder, 
            startupinfo=startupinfo).decode('utf-8').splitlines()

        variants = []
        EXCLUDES = [
            'All primary targets available:', 
            'help', 
            'edit_cache', 
            '.ninja']
            
        for target in lines:
            try:
                if len(target) == 0:
                    continue
                if any(exclude in target for exclude in EXCLUDES): 
                    continue
                if target.endswith(': phony'):
                    target = target[:-len(': phony')]
                elif target.endswith(': CLEAN'):
                    target = target[:-len(': CLEAN')]
                target = target.strip()
                if (self.filter_targets and 
                    not any(f in target for f in self.filter_targets)):
                    continue
                shell_cmd = 'cmake --build . --target {}'.format(target)
                variants.append({'name': target, 'shell_cmd': shell_cmd})
            except Exception as e:
                sublime.error_message(str(e))
                # Continue anyway; we're in a for-loop
        return variants
