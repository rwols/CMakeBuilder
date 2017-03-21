from .. import CMakeGenerator
import subprocess

class Ninja(CMakeGenerator):

    def __repr__(self):
        return 'Ninja'

    def syntax(self):
        return r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

    def file_regex(self):
        return 'Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax'

    def variants(self):
        lines = subprocess.check_output('cmake --build . --target help', cwd=self.build_folder).decode('utf-8').splitlines()
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

        LIB_EXTENSIONS = [
            '.so',
            '.dll',
            '.dylib',
            '.a']
        for target in lines:
            try:
                if any(exclude in target for exclude in EXCLUDES): 
                    continue
                target = target.rpartition(':')[0]
                name = target
                for ext in LIB_EXTENSIONS:
                    if name.endswith(ext):
                        name = name[:-len(ext)]
                        break
                if (self.filter_targets and 
                    not any(f in name for f in self.filter_targets)):
                    continue
                shell_cmd = 'cmake --build . --target {}'.format(target)
                self.variants.append({'name': name, 'shell_cmd': shell_cmd})
            except Exception as e:
                print(e)
                sublime.error_message(str(e))
        return variants

        
