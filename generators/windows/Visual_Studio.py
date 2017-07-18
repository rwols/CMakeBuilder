from CMakeBuilder.generators import CMakeGenerator
from CMakeBuilder.generators.windows.support.vcvarsall import query_vcvarsall
from CMakeBuilder.support.check_output import check_output
import os
import re
import subprocess
import sublime

class Visual_Studio(CMakeGenerator):

    def __repr__(self):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        lines = check_output('cmake --help').splitlines()
        years = {}
        for line in lines:
            print(line)
            if 'Visual Studio' in line:
                match = re.search(r'Visual Studio (\d+) (\d+)', line)
                if not match:
                    continue
                ver = float(match.group(1))
                year = int(match.group(2))
                years[ver] = year
        result = 'Visual Studio'
        ok = False
        vs_versions = self.visual_studio_versions
        if not vs_versions:
            vs_versions = [15.0, 14.1, 14.0, 13.0, 12.0, 11.0, 10.0]
        for version in vs_versions:
            if version in years:
                if isinstance(version, int):
                    result += ' %i %i' % (version, years[version])
                    ok = True
                    break
                elif isinstance(version, float):
                    if version.is_integer():
                        result += ' %i %i' % (int(version), years[version])
                    else:
                        result += ' %0.1f %i' % (version, years[version])
                    ok = True
                    break
        if not ok:
            raise Exception('Could not determine Visual Studio version!')
        if self.target_architecture:
            if self.target_architecture == 'amd64':
                result += ' Win64'
            elif self.target_architecture == 'arm':
                result += ' ARM'
        return result

    def variants(self):
        configs = self.get_cmake_key('configurations')
        variants = []
        for root, dirs, files in os.walk(self.build_folder):
            if 'CMakeFiles' in root:
                continue
            for file in files:
                if not file.endswith('.vcxproj'):
                    continue
                file = file[:-len('.vcxproj')]
                commonprefix = os.path.commonprefix([root, self.build_folder])
                relative = root[len(commonprefix):]
                if relative.startswith('\\'):
                    relative = relative[1:]
                relative = relative.replace('\\', '/')
                if relative == '/' or not relative:
                    target = file
                else:
                    target = relative + '/' + file
                if (self.filter_targets and 
                    not any(f in target for f in self.filter_targets)):
                    continue
                if configs:
                    for config in configs:
                        shell_cmd = 'cmake --build . --target {} --config {}'.format(target, config)
                        variants.append({'name': target + ' [' + config + ']', 
                            'shell_cmd': shell_cmd})
                else:
                    shell_cmd = 'cmake --build . --target {}'.format(target)
                    variants.append({'name': target, 'shell_cmd': shell_cmd})
        return variants

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Visual_Studio.sublime-syntax'

    def file_regex(self):
        return r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) \w+\d\d\d\d: .*) \[.*$'

    def get_env(self):
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
