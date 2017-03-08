import sublime, sublime_plugin, os, Default.exec, multiprocessing
from .ExpandVariables import *

class CmakeWriteBuildTargetsCommand(Default.exec.ExecCommand):
    """Writes a build system to the sublime project file. This only works
    when a cmake project has been configured."""

    def is_enabled(self):
        """You may only run this command if there's a `build_folder` with a
        `CMakeCache.txt` file in it. That's when we assume that the project has
        been configured."""
        project = self.window.project_data()
        if project is None:
            return False
        project_file_name = self.window.project_file_name()
        if not project_file_name:
            return False
        cmake = project.get('cmake')
        if not cmake:
            return False
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except Exception as e:
            return False
        build_folder = cmake.get('build_folder')
        if not os.path.exists(os.path.join(build_folder, 'CMakeCache.txt')):
            return False
        return True

    def description(self):
        return 'Write Build Targets to Sublime Project'

    def run(self):
        self.variants = []
        self.isNinja = False
        self.isMake = False
        project = self.window.project_data()
        project_file_name = self.window.project_file_name()
        project_path = os.path.dirname(project_file_name)
        cmake = project.get('cmake')
        self.build_folder_pre_expansion = cmake.get('build_folder')
        try:
            # See ExpandVariables.py
            expand_variables(cmake, self.window.extract_variables())
        except KeyError as e:
            sublime.error_message('Unknown variable in cmake dictionary: {}'
                .format(str(e)))
            return
        except ValueError as e:
            sublime.error_message('Invalid placeholder in cmake dictionary')
            return
        self.build_folder = cmake.get('build_folder')
        self.filter_targets = cmake.get('filter_targets')
        generator = cmake.get('generator')
        if generator:
            generator = generator.lower()
        if not generator:
            self.isMake = True
        elif generator == 'unix makefiles':
            self.isMake = True
        elif generator == 'ninja':
            self.isNinja = True
        else:
            sublime.error_message('Unknown generator specified!')
            return
        shell_cmd = 'cmake --build . --target help'
        super().run(shell_cmd=shell_cmd, working_dir=self.build_folder)
        
    def on_data(self, proc, data):
        super().on_data(proc, data)

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

        try:
            data = data.decode(self.encoding)
            if 'are some of the valid targets for this Makefile:' in data:
                assert self.isMake
            elif 'All primary targets available:' in data:
                assert self.isNinja
            targets = data.splitlines()
            for target in targets:
                if any(exclude in target for exclude in EXCLUDES): 
                    continue
                if self.isMake:
                    target = target[4:]
                elif self.isNinja:
                    target = target.rpartition(':')[0]
                else:
                    continue
                name = target
                for ext in LIB_EXTENSIONS:
                    if name.endswith(ext):
                        name = name[:-len(ext)]
                        break
                if (self.filter_targets and 
                    not any(f in name for f in self.filter_targets)):
                    continue
                shell_cmd = None
                if self.isMake:
                    shell_cmd = 'make {} -j{}'.format(
                        target, str(multiprocessing.cpu_count()))
                else:
                    shell_cmd = 'cmake --build . --target {}'.format(target)
                self.variants.append({'name': name, 'shell_cmd': shell_cmd})
        except Exception as e:
            print(e)
            sublime.error_message(str(e))

    def on_finished(self, proc):
        super().on_finished(proc)

        REGEX = '(.+[^:]):(\d+):(\d+): (?:fatal )?((?:error|warning): .+)$'

        project = self.window.project_data()
        name = os.path.splitext(
            os.path.basename(self.window.project_file_name()))[0]
        shell_cmd = 'cmake --build .'
        syntax = 'Packages/CMakeBuilder/Syntax/Make.sublime-syntax'
        if self.isMake:
            shell_cmd = 'make -j{}'.format(str(multiprocessing.cpu_count()))
            # syntax = 'Packages/CMakeBuilder/Syntax/Make.sublime-syntax'
        elif self.isNinja:
            shell_cmd = 'cmake --build .'
            syntax = 'Packages/CMakeBuilder/Syntax/Ninja.sublime-syntax'
        project['build_systems'] = [
            {'name': name,
            'shell_cmd': shell_cmd,
            'working_dir': self.build_folder_pre_expansion,
            'file_regex': REGEX,
            'syntax': syntax,
            'variants': self.variants}]
        self.window.set_project_data(project)
        self.window.run_command('set_build_system', args={'index': 0})
