import sublime, sublime_plugin, os, functools, tempfile, Default.exec

class CmakeConfigureCommand(Default.exec.ExecCommand):
	"""Configures a CMake project with options set in the sublime project
	file."""

	def run(self, write_build_targets=False):
		self.write_build_targets = write_build_targets
		project = self.window.project_data()
		if project is None:
			sublime.error_message('No sublime-project file found.')
			return
		project_name = os.path.splitext(self.window.project_file_name())[0]
		project_path = os.path.dirname(self.window.project_file_name())
		if not os.path.isfile(os.path.join(project_path, 'CMakeLists.txt')):
			must_have_root_path = True
		else:
			must_have_root_path = False
		tempdir = tempfile.mkdtemp()
		cmake = project.get('cmake')
		if cmake is None:
			project['cmake'] = {'build_folder': tempdir}
			print('CMakeBuilder: Temporary directory shall be "{}"'
				.format(tempdir))
			self.window.set_project_data(project)
			project = self.window.project_data()
			cmake = project['cmake']
		build_folder_before_expansion = cmake.get('build_folder')
		if build_folder_before_expansion is None:
			cmake['build_folder'] = tempdir
			print('CMakeBuilder: Temporary directory shall be "{}"'
				.format(tempdir))
			project['cmake'] = cmake
			self.window.set_project_data(project)
			project = self.window.project_data()
			cmake = project['cmake']
		cmake = sublime.expand_variables(cmake, self.window.extract_variables())
		# Guaranteed to exist at this point.
		build_folder = cmake.get('build_folder')
		build_folder = os.path.realpath(build_folder)
		generator = cmake.get('generator')
		overrides = cmake.get('command_line_overrides')
		filters = cmake.get('filter_targets')
		if build_folder is None:
			sublime.error_message(
				'No "cmake: build_folder" variable found in {}.'.format(
					project_path))
			return
		os.makedirs(build_folder, exist_ok=True)
		try: 
			os.remove(os.path.join(build_folder, 'CMakeCache.txt'))
		except FileNotFoundError as e: 
			pass
		root_folder = cmake.get('root_folder')
		if root_folder:
			root_folder = os.path.realpath(root_folder)
		elif must_have_root_path:
			sublime.error_message(
				'No "CMakeLists.txt" file in the project folder is present and \
				no "root_folder" specified in the "cmake" dictionary of the \
				sublime-project file.')
		cmd = 'cmake "{}"'.format(
			root_folder if root_folder else project_path)
		if generator:
			cmd += ' -G "{}"'.format(generator)
		try:
			for key, value in overrides.items():
				if type(value) is bool:
					cmd += ' -D{}={}'.format(key, 'ON' if value else 'OFF')
				else:
					cmd += ' -D{}={}'.format(key, str(value))
		except AttributeError as e:
			pass
		except ValueError as e:
			pass
		super().run(shell_cmd=cmd, working_dir=build_folder)
	
	def on_finished(self, proc):
		super().on_finished(proc)
		if self.write_build_targets:
			sublime.set_timeout(
				functools.partial(
					self.window.run_command, 
					'cmake_write_build_targets'), 0)
