from CMakeBuilder.tests.fixtures import TestCase


class TestConfigure(TestCase):

    cmake_settings = r"""
        {
            "build_folder": "${project_path}/build"
        }
    """

    files = [
        ("CMakeLists.txt", r"""
            project(foo VERSION 0.1 LANGUAGES C)
            message(STATUS "okay")
            """)
    ]


    def test_configure(self):
        self.window.run_command("cmake_configure")
        self.assertTrue(True)
        self.assertTrue(True)
