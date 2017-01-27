import sublime, sublime_plugin, os

class CmakeOpenBuildFolderCommand(sublime_plugin.WindowCommand):
	"""Opens the build folder."""

	def is_enabled(self):
		project = self.window.project_data()
		if project is None:
			return False
		project_file_name = self.window.project_file_name()
		if not project_file_name:
			return False
		cmake = project.get('cmake')
		if not cmake:
			return False
		cmake = sublime.expand_variables(cmake, self.window.extract_variables())
		build_folder = cmake.get('build_folder')
		if not build_folder:
			return False
		if os.path.exists(build_folder):
			return True
		else:
			return False

	def description(self):
		return 'Browse Build Folder…'

	def run(self):
		project = self.window.project_data()
		cmake = project.get('cmake')
		cmake = sublime.expand_variables(cmake, self.window.extract_variables())
		build_folder = cmake.get('build_folder')
		self.window.run_command(
			'open_dir', args={'dir': os.path.realpath(build_folder)})
