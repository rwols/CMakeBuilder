"""Defines TestCase"""
import unittesting
import os
import sublime
from CMakeBuilder import ServerManager


class TestCase(unittesting.helpers.TempDirectoryTestCase):
    """
    TempDirectoryTestCase is a subclass of DeferrableTestCase which creates and
    opens a temp directory before running the test case and close the window
    when the test case finishes running.

    See:
    https://github.com/divmain/GitSavvy/blob/master/tests/test_git/common.py
    https://github.com/randy3k/UnitTesting/blob/master/unittesting/helpers.py
    """

    @classmethod
    def setUpClass(cls):
        """Prepares a class for a test case involving project files."""
        yield from super(TestCase, cls).setUpClass()
        assert hasattr(cls, "cmake_settings")
        assert hasattr(cls, "files")
        assert hasattr(cls, "window")
        assert isinstance(cls.files, list)
        assert isinstance(cls.window, sublime.Window)
        data = cls.window.project_data()
        assert data["folders"][0]["path"] is not None
        data["settings"] = {}
        data["settings"]["cmake"] = cls.cmake_settings
        cls.window.set_project_data(data)
        for pair in cls.files:
            assert isinstance(pair, tuple)
            assert len(pair) == 2
            assert isinstance(pair[0], str)
            assert isinstance(pair[1], str)
            path = os.path.join(cls._temp_dir, pair[0])
            content = pair[1]
            with open(path, "w") as f:
                f.write(content)


class ServerTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        yield from super(ServerTestCase, cls).setUpClass()
        ServerManager.build_folder_pre_expansion = cls.cmake_settings["schemes"][0]["build_folder"]
        ServerManager.build_folder = sublime.expand_variables(ServerManager.build_folder_pre_expansion, cls.window.extract_variables())
        ServerManager.source_folder = cls.window.extract_variables()["folder"]
        ServerManager.command_line_overrides = {
            "CMAKE_EXPORT_COMPILE_COMMANDS": True
        }
        print(cls.window.extract_variables(),
              ServerManager.build_folder_pre_expansion,
              ServerManager.build_folder, ServerManager.source_folder)
        if sublime.platform() in ("osx", "linux"):
            ServerManager.generator = "Unix Makefiles"
        else:
            ServerManager.generator = "NMake Makefiles"
        # ServerManager._run_configure_with_new_settings()
        # assert ServerManager.get(cls.window) is not None

    @classmethod
    def tearDownClass(cls):
        server = ServerManager._servers.pop(cls.window.id(), None)
        assert server is not None
        super(ServerTestCase, cls).tearDownClass()

    @classmethod
    def get_server(cls):
        return ServerManager.get(cls.window)
