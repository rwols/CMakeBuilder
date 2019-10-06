# CMakeBuilder

Configure, build and test a CMake project right from within Sublime Text 3.

## Installation

Run the command

    Package Control: Install Package

and look for CMakeBuilder.

Version 1.0.1 and lower do not have server functionality. What follows is the
documentation for version 1.0.1 and lower.

## TL;DR

1. Open a `.sublime-project`.

2. Add this to the project file in your `"settings"`:

    ```javascript
    "cmake":
    {
       "build_folder": "$folder/build"
    }
    ```

3. Run the command "CMakeBuilder: Configure" from the command palette.

4. Check out your new build system in your `.sublime-project`.

5. Press <kbd>CTRL</kbd> + <kbd>B</kbd> or <kbd>⌘</kbd> + <kbd>B</kbd>.

6. Hit <kbd>F4</kbd> to jump to errors and/or warnings.

See the example project below for more options.

## Reference

### The CMake Dictionary

By "CMake dictionary" we mean the JSON dictionary that you define in your
`"settings"` of your sublime project file with key `"cmake"`. The CMake
dictionary accepts the following keys:

* `build_folder` [required string]

  A string pointing to the directory where you want to build the project. A
  good first choice is `$folder/build`.

* `command_line_overrides` [optional dictionary]

  A dictionary where each value is either a string or a boolean. The key-value
  pairs are passed to the CMake invocation when you run `cmake_configure` as
  `-D` options. For example, if you have the key-value pair `"MY_VAR": "BLOB"`
  in the dictionary, the CMake invocation will contain `-D MY_VAR=BLOB`. Boolean
  values are converted to `ON` or `OFF`. For instance, if you have the key-value
  pair `"BUILD_SHARED_LIBS": true`in the dictionary, the CMake invocation will
  contain `-D BUILD_SHARED_LIBS=ON`.

* `generator` [optional string]

  A JSON string specifying the CMake generator.

  * Available generators for osx: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with brew.

  * Available generators for linux: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with apt.

  * Available generators for windows: "Ninja" and "Visual Studio".

    If no generator is specified on windows, "Visual Studio" is the default
    generator. You need Microsoft Visual Studio C++ in order to configure your
    project wether you're using Ninja or Visual Studio.


* `root_folder` [optional string]

  The directory where the root CMakeLists.txt file resides. If this key is not
  present, the directory where the sublime project file is located is assumed to
  have the root CMakeLists.txt file.

* `env` [optional dictionary]

  This is a dict of key-value pairs of strings. Place your environment
  variables at configure time in here. For example, to select clang as
  your compiler if you have gcc set as default, you can use

      "env": { "CC": "clang", "CXX": "clang++" }

* `platform` [optional string]

  For generators that support a platform argument. In the case of this plugin
  that would be Visual Studio. In practise, set this to "x64" to build 64-bit
  binaries instead of the default 32-bit. This is the `-A` argument passed to
  CMake.

* `toolset` [optional dictionary]

  For generators that support a toolset argument. In the case of this plugin
  that would be Visual Studio. In practise, set this to `{ "host": "x64" }` to
  use the 64-bit compiler instead of the 32-bit compiler. This is the `-T`
  argument passed to CMake. As in the case of `command_line_overrides`, the
  dictionary is converted into a string as in `key1=value1;key2=value2`.

Any key may be overridden by a platform-specific override. The platform keys
are one of `"linux"`, `"osx"` or `"windows"`. For an example on how this works,
see below.

## Example Project File

Here is an example Sublime project to get you started.

```javascript
{
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {
        "cmake":
        {
            "build_folder": "$folder/build",
            "command_line_overrides":
            {
                "BUILD_SHARED_LIBS": true,
                "CMAKE_BUILD_TYPE": "Debug",
                "CMAKE_EXPORT_COMPILE_COMMANDS": true
            },
            "generator": "Unix Makefiles",
            "windows":
            {
                "generator": "Visual Studio 15 2017",
                "platform": "x64",
                "toolset": { "host": "x64" }
            }
        }
    }
}

```


### Available Scripting Commands

* `cmake_clear_cache`, arguments: `{ with_confirmation : bool }`.
* `cmake_configure`, arguments: `None`.
* `cmake_diagnose`, arguments: `None`.
* `cmake_open_build_folder`, arguments: `None`.

### Available Commands in the Command Palette

* `CMakeBuilder: Clear Cache`
* `CMakeBuilder: Configure`
* `CMakeBuilder: Diagnose`
* `CMakeBuilder: Browse Build Folder...`

All commands are accessible via both the command palette as well as the tools
menu at the top of the window.

### Available Settings

* `silence_developer_warnings` : JSON bool

  If true, will add the option `-Wno-dev` to the CMake invocation of the
  `cmake_configure` command.

* `always_clear_cache_before_configure` : JSON bool

  If true, always clears the CMake cache before the `cmake_configure` command is
  run.

* `ctest_command_line_args` : JSON string

  Command line arguments passed to the CTest invocation when you run
  `cmake_run_ctest`.

### Clearing the cache
To force CMake files re-generation run

    CMakeBuilder: Clear Cache

and then run

    CMakeBuilder: Configure

### Diagnostics/Help
If you get stuck and don't know what to do, try running

    CMakeBuilder: Diagnose

### Tools Menu
All commands are also visible in the Tools menu under "CMakeBuilder".

![11][11] <!-- Screenshot #11 -->

### Running unit tests with CTest
If you have unit tests configured with the [add_test][2] function of CMake, then
you can run those with the "ctest" build variant.

### Syntax highlighting for various generators
There is syntax highlighting when building a target, and a suitable line regex
is set up for each generator so that you can press F4 to go to an error.

![9][9]   <!-- Screenshot #9  -->
![10][10] <!-- Screenshot #10 -->
![12][12] <!-- Screenshot #12 -->

### List of Valid Variable Substitutions
This is a reference list for the valid variable substitutions for your
`.sublime-project` file.

* packages
* platform
* file
* file\_path
* file\_name
* file\_base\_name
* file\_extension
* folder
* project
* project\_path
* project\_name
* project\_base\_name
* project\_extension

[2]: https://cmake.org/cmake/help/latest/command/add_test.html
[9]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/9.png
[10]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/10.png
[11]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/11.png
[12]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/12.png
