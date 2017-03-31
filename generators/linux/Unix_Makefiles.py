from .. import CMakeGenerator
import subprocess
import sublime
import multiprocessing

class Unix_Makefiles(CMakeGenerator):

    def __repr__(self):
        return 'Unix Makefiles'

    def file_regex(self):
        return r'(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

    def syntax(self):
        return 'Packages/CMakeBuilder/Syntax/Make.sublime-syntax'

    def shell_cmd(self, target):
        return 'make -j{} --target {}'.format(str(multiprocessing.cpu_count()), target)

    def variants(self):
        env = None
        if self.window.active_view():
            env = self.window.active_view().settings().get('build_env')
            
        shell_cmd = 'cmake --build . --target help'
        proc = subprocess.Popen(
            ['/bin/bash', '-l', '-c', shell_cmd],
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
                variants.append(target)
            except Exception as e:
                sublime.error_message(str(e))
                # Continue anyway; we're in a for-loop
        return variants
        
