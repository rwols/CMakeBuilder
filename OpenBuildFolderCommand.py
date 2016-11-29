import sublime, sublime_plugin, os

class CmakeOpenBuildFolderCommand(sublime_plugin.WindowCommand):

	def run(self):
		project = self.window.project_data()
		if project is None:
			sublime.error_message('No sublime-project file found.')
			return
		cmakeDict = project.get('cmake')
		if cmakeDict is None:
			sublime.error_message('No \"cmake\" dictionary in sublime-project file found.')
			return
		cmakeDict = sublime.expand_variables(cmakeDict, self.window.extract_variables())
		buildFolder = cmakeDict.get('build_folder')
		if buildFolder:
			return self.window.run_command('open_dir', args={'dir': os.path.realpath(buildFolder)})
		else:
			sublime.error_message('No \"build_folder\" string specified in \"cmake\" dictionary in sublime-project file.')
			return