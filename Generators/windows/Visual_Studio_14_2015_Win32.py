from .. import CMakeGenerator
import os

class Visual_Studio_14_2015_Win32(CMakeGenerator):

    def create_sublime_build_system(self):
        variants = []
        bf_pre = self.get_build_folder()
        bf = self.expand_vars(bf_pre)
        for root, dirs, files in os.walk(bf):
            if 'CMakeFiles' in root:
                continue
            for file in files:
                if not file.endswith('.vcxproj'):
                    continue
                file = file[:-len('.vcxproj')]
                commonprefix = os.path.commonprefix([root, bf])
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
        shell_cmd = 'cmake --build .'
        # regex = blah
        # syntax = 'Packages/CMakeBuilder/Generators/windows/Visual_Studio.sublime-syntax
        name = os.path.splitext(
            os.path.basename(self.window.project_file_name()))[0]
        return {'name': name,
            'shell_cmd': shell_cmd,
            'working_dir': self.build_folder_pre_expansion,
            # 'file_regex': regex,
            # 'syntax': syntax,
            'variants': variants}
        
