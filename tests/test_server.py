from CMakeBuilder.tests.fixtures import ServerTestCase
import CMakeBuilder
import sublime


if CMakeBuilder.support.capabilities("serverMode"):

    class TestServer(ServerTestCase):

        cmake_settings = {
            "schemes": [
                {
                    "name": "Debug",
                    "build_folder": "${folder}/build"
                }
            ]
        }

        files = [
            ("CMakeLists.txt", r"""
    cmake_minimum_required(VERSION 2.8 FATAL_ERROR)
    project(foo)
    message(STATUS "okay")
""")
        ]

        # def test_server(self):
        #     server = self.get_server()
        #     self.assertTrue(server is not None)
