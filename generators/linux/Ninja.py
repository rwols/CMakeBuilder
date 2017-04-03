from .. import CMakeGenerator
import subprocess
import sublime

class Ninja(CMakeGenerator):

    def __repr__(self):
        return 'Ninja'

    def file_regex(self):
        return r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax'

    def variants(self):
        env = None
        if self.window.active_view():
            env = self.window.active_view().settings().get('build_env')
            
        shell_cmd = 'cmake --build . --target help'
        proc = subprocess.Popen(
            ['/bin/bash', '-c', shell_cmd],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            cwd=self.build_folder)
        outs, errs = proc.communicate()
        errs = errs.decode('utf-8')
        if errs:
            sublime.error_message(errs)
            return
        lines = outs.decode('utf-8').splitlines()
        
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

        variants = []
        for target in lines:
            try:
                if any(exclude in target for exclude in EXCLUDES): 
                    continue
                target = target.rpartition(':')[0]
                if (self.filter_targets and 
                    not any(f in target for f in self.filter_targets)):
                    continue
                shell_cmd = 'cmake --build . --target {}'.format(target)
                variants.append({'name': target, 'shell_cmd': shell_cmd})
            except Exception as e:
                print(e)
                sublime.error_message(str(e))
        return variants
