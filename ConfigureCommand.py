import sublime, sublime_plugin, os, functools, Default.exec

class CmakeConfigureCommand(Default.exec.ExecCommand):

	def run(self, write_build_targets=False):
		self.writeBuildTargets = write_build_targets
		project = self.window.project_data()
		if project is None:
			sublime.error_message('No sublime-project file found.')
			return
		projectPath = os.path.dirname(self.window.project_file_name())
		if not os.path.isfile(os.path.join(projectPath, 'CMakeLists.txt')):
			sublime.error_message('No "CMakeLists.txt" file present in "{}"'.format(projectPath))
			return
		cmakeDict = project.get('cmake')
		if cmakeDict is None:
			project['cmake'] = {'build_folder': '$\{project_path\}/build'}
			self.window.set_project_data(project)
			project = self.window.project_data()
			cmakeDict = project['cmake']
		buildFolderBeforeExpansion = cmakeDict.get('build_folder')
		if buildFolderBeforeExpansion is None:
			cmakeDict['build_folder'] = '$\{project_path\}/build'
			project['cmake'] = cmakeDict
			self.window.set_project_data(project)
			project = self.window.project_data()
			cmakeDict = project['cmake']
		cmakeDict = sublime.expand_variables(cmakeDict, self.window.extract_variables())
		buildFolder = cmakeDict.get('build_folder')
		buildFolder = os.path.realpath(buildFolder)
		generator = cmakeDict.get('generator')
		cmdLineOverrides = cmakeDict.get('command_line_overrides')
		filterTargets = cmakeDict.get('filter_targets')
		if buildFolder is None:
			sublime.error_message('No "cmake: build_folder" variable found in {}.'.format(projectPath))
			return
		os.makedirs(buildFolder, exist_ok=True)
		try: 
			os.remove(os.path.join(buildFolder, 'CMakeCache.txt'))
		except FileNotFoundError as e: 
			pass
		rootFolder = cmakeDict.get('root_folder')
		if rootFolder:
			rootFolder = os.path.realpath(rootFolder)
		shellCmd = 'cmake "{}"'.format(rootFolder if rootFolder else projectPath)
		if generator:
			shellCmd += ' -G "{}"'.format(generator)
		try:
			for key, value in cmdLineOverrides.items():
				if type(value) is bool:
					shellCmd += ' -D{}={}'.format(key, 'ON' if value else 'OFF')
				else:
					shellCmd += ' -D{}={}'.format(key, str(value))
		except AttributeError as e:
			pass
		except ValueError as e:
			pass
		super().run(shell_cmd=shellCmd, working_dir=buildFolder)
	
	def on_finished(self, proc):
		super().on_finished(proc)
		if self.writeBuildTargets:
			sublime.set_timeout(functools.partial(self.window.run_command, 'cmake_write_build_targets'), 0)
