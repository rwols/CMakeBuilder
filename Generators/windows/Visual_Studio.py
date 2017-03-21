from .. import CMakeGenerator
import os

class Visual_Studio(CMakeGenerator):

    def variants(self):
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
                shell_cmd = 'cmake --build . --target {}'.format(target)
                variants.append({'name': target, 'shell_cmd': shell_cmd})
        return variants

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Visual_Studio.sublime-syntax'

    def file_regex(self):
        return r'^  (.+)\((\d+)\)(): ((?:fatal )?(?:error|warning) \w+\d\d\d\d: .*) \[.*$'
        
