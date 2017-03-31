import Default.exec
import sublime
from ..generators import *
from ..support import *

class CmakeBuildCommand(Default.exec.ExecCommand):

    def _expand(self, keyname, value):
        try:
            return expand_variables(value, self.window.extract_variables())
        except Exception as e:
            sublime.error_message(
                'Error while expanding variables of key "{}"'.format(keyname))
            raise e

    def init_variables(self, **kwargs):
        try:
            self.build_folder = kwargs.get('build_folder')
            if not self.build_folder:
                sublime.error_message('Missing variable "build_folder"')
                return False
            self.build_folder = self._expand('build_folder', self.build_folder)
            self.source_folder = kwargs.get('source_folder')
            if not self.source_folder:
                sublime.error_message('Missing variable "source_folder".')
                return False
            self.source_folder = self._expand('source_folder', 
                self.source_folder)
            self.generator = kwargs.get('generator')
            if not self.generator:
                if sublime.platform() == 'linux':
                    self.generator = 'Unix Makefiles'
                elif sublime.platform() == 'osx':
                    self.generator = 'Unix Makefiles'
                elif sublime.platform() == 'windows':
                    self.generator = 'Visual Studio'
            self.command_line_overrides = kwargs.get('command_line_overrides')
            self.command_line_overrides = self._expand('command_line_overrides',
                self.command_line_overrides)
            self.env = kwargs.get('env')
            if not self.env:
                self.env = {}
            else:
                self.env = self._expand('env', self.env)
            self.filter_targets = kwargs.get('filter_targets')
            self.select = kwargs.get('select')
            if not self.select:
                self.select = False
            self.clear_cache = kwargs.get('clear_cache')
            if not self.clear_cache:
                self.clear_cache = False
            self.configure = kwargs.get('configure')
            if not self.configure:
                self.configure = False
            self.run_ctest = kwargs.get('run_ctest')
            if not self.run_ctest:
                self.run_ctest = False
            self.configurations = kwargs.get('configurations')
            if not self.configurations:
                self.configurations = []
        except Exception as e:
            print(str(e))
            return False
        GeneratorClass = None
        try:
            GeneratorClass = class_from_generator_string(self.generator)
        except Exception as e:
            sublime.error_message('Could not create generator "{}"'.format(
                self.generator))
            return False
        try:
            self.builder = GeneratorClass(self.window, self.source_folder, 
                self.build_folder, self.generator, self.configurations, 
                self.command_line_overrides, self.env)
        except Exception as e:
            sublime.error_message(
                """Could not instantiate generator "{}"
                (are your variables in your build system correct?)""".format(
                    self.generator))
            return False
        return True

    def is_cmake_cache_present(self):
        return os.path.isfile(os.path.join(self.build_folder, 'CMakeCache.txt'))

    def get_cache_path(self):
        return os.path.join(self.build_folder, 
            'CMakeFiles', 'CMakeBuilder.json')

    def read_cache(self):
        with open(self.get_cache_path(), 'r') as f:
            return json.load(f)

    def write_cache(self, cache):
        with open(self.get_cache_path(), 'w') as f:
            json.dump(cache, f)

    def run(self, **kwargs):
        if not self.init_variables(**kwargs):
            return
        try:
            self.cache = self.read_cache()
        except IOError as e:
            self.cache = { 'configuring': False, 'success': False }
            # sublime.error_message(
            #     'Could not read the cache! Make sure you configured the project succesfully.')
            # return
        if self.cache['configuring']:
            if not sublime.ok_cancel_dialog(
                    'Configuring is still in progress!',
                    'Continue Anyway'):
                return
        if self.configure:
            self.window.run_command('cmake_configure', args={
                'build_folder': self.build_folder, 
                'source_folder': self.source_folder, 
                'command_line_overrides': self.command_line_overrides,
                'configurations': self.configurations,
                'generator': self.generator,
                'env': self.env})
            return
        elif self.clear_cache:
            self.window.run_command('cmake_clear_cache', args={
                'with_confirmation': True, 'build_folder': self.build_folder})
            return
        elif self.run_ctest:
            self.window.run_command('cmake_run_ctest', args={
                'build_folder': self.build_folder})
        elif self.select:
            if not self.is_cmake_cache_present():
                sublime.error_message('CMake cache is not present in "{}". Make sure to Configure the project first.'.format(self.build_folder))
                return
            elif not self.cache['success']:
                sublime.error_message('The project was not configured correctly.')
                return
            self.window.show_quick_panel(
                self.cache['targets'], 
                self.on_done_select_target)
        else:
            if not self.cache['success']:
                sublime.error_message('The project was not configured correctly.')
            elif self.cache['last_selected_target']:
                self.build_last_selected_target()
            else:
                self.window.show_quick_panel(
                    self.cache['targets'], 
                    self.on_done_select_target)

    def on_done_select_target(self, index):
        if index == -1:
            return
        self.cache['last_selected_target'] = self.cache['targets'][index]
        self.write_cache(self.cache)
        self.build_last_selected_target()

    def build_last_selected_target(self):
        last_selected_target = self.cache['last_selected_target']
        assert last_selected_target
        super().run(shell_cmd=self.builder.shell_cmd(last_selected_target),
            working_dir=self.build_folder,
            file_regex=self.builder.file_regex(),
            syntax=self.builder.syntax(),
            env=self.builder.env())


    
