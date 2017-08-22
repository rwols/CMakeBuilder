from CMakeBuilder.tests.fixtures import TestCase


class TestConfigure(TestCase):

    cmake_settings = {
        "build_folder": "$folder/build"
    }

    files = [
        ("CMakeLists.txt", r"""
cmake_minimum_required(VERSION 2.8 FATAL_ERROR)
project(foo)
message(STATUS "okay")
""")
    ]

    def test_configure(self):
        self.window.run_command("cmake_configure")
        self.assertTrue(True)
