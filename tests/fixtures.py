"""Defines TestCase"""
import unittesting
import os
import sublime


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
