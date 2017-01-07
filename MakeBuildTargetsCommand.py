import sublime, sublime_plugin, os, Default.exec, multiprocessing

class CmakeWriteBuildTargetsCommand(Default.exec.ExecCommand):
	"""Writes a build system to the sublime project file. This only works
	when a cmake project has been configured."""

	def run(self):
		self.variants = []
		self.isNinja = False
		self.isMake = False
		project = self.window.project_data()
		if project is None:
			sublime.error_message('No sublime-project file found.')
			return
		projectPath = os.path.dirname(self.window.project_file_name())
		if not os.path.isfile(os.path.join(projectPath, 'CMakeLists.txt')):
			sublime.error_message(
				'No "CMakeLists.txt" file present in "{}"'
				.format(projectPath))
			return
		cmakeDict = project.get('cmake')
		if cmakeDict is None:
			sublime.error_message(
				'No "cmake" object found in {}.'.format(projectPath))
		self.buildFolderBeforeExpansion = cmakeDict.get('build_folder')
		cmakeDict = sublime.expand_variables(cmakeDict, 
			self.window.extract_variables())
		self.buildFolder = cmakeDict.get('build_folder')
		self.filterTargets = cmakeDict.get('filter_targets')
		generator = cmakeDict.get('generator')
		if generator:
			self.isNinja = generator == 'Ninja'
			self.isMake = generator == 'Unix Makefiles'
		if self.buildFolder is None:
			sublime.error_message(
				'No "cmake_build_folder" variable found in {}.'
				.format(projectPath))
			return
		shellCmd = 'cmake --build . --target help'
		super().run(shell_cmd=shellCmd, working_dir=self.buildFolder)
		
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
			'.dll',
			'.a']

		try:
			data = data.decode(self.encoding)
			if 'are some of the valid targets for this Makefile:' in data:
				self.isMake = True
			elif 'All primary targets available:' in data:
				self.isNinja = True
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
				if (self.filterTargets and 
					not any(f in name for f in self.filterTargets)):
					continue
				shellCmd = None
				if self.isMake:
					shellCmd = 'make {} -j{}'.format(
						target, str(multiprocessing.cpu_count()))
				else:
					shellCmd = 'cmake --build . --target {}'.format(target)
				self.variants.append({'name': name, 'shell_cmd': shellCmd})
		except Exception as e:
			print(e)
			sublime.error_message(str(e))

	def on_finished(self, proc):
		super().on_finished(proc)

		REGEX = '^(/.[^:]*):(\\d+):(\\d+): (?:fatal )?(?:error|warning): (.*)$'

		project = self.window.project_data()
		name = os.path.splitext(
			os.path.basename(self.window.project_file_name()))[0]
		project['build_systems'] = [
			{'name': name,
			'shell_cmd': 'cmake --build .',
			'working_dir': self.buildFolderBeforeExpansion,
			'file_regex': REGEX,
			'variants': self.variants}]
		self.window.set_project_data(project)
