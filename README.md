# CMakeBuilder

Configure, build and test a CMake project right from within Sublime Text 3.

## Installation

Run the command

    Package Control: Install Package

and look for CMakeBuilder.

## TL;DR

1. Open a `.sublime-project`.

2. Add this to the project file in your `"settings"`:

    ```json
    "cmake":
    {
       "build_folder": "${project_path}/build"
    }
    ```

3. Save your project. This will trigger CMakeBuilder to configure your project.
   If nothing happens, you can also run the command "CMakeBuilder: Configure"
   from the command palette.

4. Check out your new build system in your `.sublime-project`. If no new build
   system was created, you can also run the command "CMakeBuilder: Write Build 
   Targets to Sublime Project File" from the command palette.

5. Press <kbd>CTRL</kbd> + <kbd>B</kbd> or <kbd>⌘</kbd> + <kbd>B</kbd>.

6. Hit <kbd>F4</kbd> to jump to errors and/or warnings. Now you're programming
   with CMakeBuilder 🕺.

## Reference

### The CMake Dictionary

By "CMake dictionary" we mean the JSON dictionary that you define in your 
`"settings"` of your sublime project file with key `"cmake"`. The CMake 
dictionary accepts the following keys:

* `build_folder` [required]

  A string pointing to the directory where you want to build the project. A
  good first choice is `${project_path}/build`.

* `command_line_overrides` [optional]

  A dictionary where each value is either a string or a boolean. The key-value
  pairs are passed to the CMake invocation when you run `cmake_configure` as
  `-D` options. For example, if you have the key-value pair `"MY_VAR": "BLOB"`
  in the dictionary, the CMake invocation will contain `-DMY_VAR=BLOB`. Boolean
  values are converted to `ON` or `OFF`. For instance, if you have the key-value
  pair `"BUILD_SHARED_LIBS": true`in the dictionary, the CMake invocation will
  contain `-DBUILD_SHARED_LIBS=ON`.

* `filter_targets` [optional]

  A JSON list consisting of strings. Each build target is tested against all of
  the items in this list. If any of the strings in this list is in the string
  representation of the target, the target will be added to the sublime build
  system.

* `generator` [optional]

  A JSON string specifying the CMake generator. 

  * Available generators for osx: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with brew.

  * Available generators for linux: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with apt.

  * Available generators for windows: "Ninja", "NMake Makefiles" and 
    "Visual Studio".

    If no generator is specified on windows, "Visual Studio" is the default
    generator. For both "Visual Studio" and "NMake Makefiles", you need
    Microsoft Visual Studio C++. The latest version of Visual Studio is searched
    for.

    **Note**: If you find that the output of the NMake generator is garbled with
    color escape codes, you can try to use `"CMAKE_COLOR_MAKEFILE": false` in 
    your `command_line_overrides` dictionary.

* `root_folder` [optional]

  The directory where the root CMakeLists.txt file resides. If this key is not
  present, the directory where the sublime project file is located is assumed to
  have the root CMakeLists.txt file.

* `env` [optional]

  This is a dict of key-value pairs of strings. Place your environment 
  variables at configure time in here. For example, to select clang as 
  your compiler if you have gcc set as default, you can use

      "env": { "CC": "clang", "CXX": "clang++" }

* `configurations` [optional] [ONLY FOR WINDOWS]

  This key is only relevant for the Visual Studio generator (see `generator`).
  This shall be a JSON list of strings defining the desired  configurations. For
  instance, `"Debug"` and `"Release"`. If omitted, the  default target is built,
  which would be Debug.

* `target_architecture` [optional] [ONLY FOR WINDOWS]

  This must be a string with any one of these three values: `"x86"`, `"amd64"`
  or `"arm"`. What this does is it will call the `vcvarsall.bat` file in the
  correct places. What this means in practise is that if you want to build 64
  bit binaries, you have to set this value to `"amd64"`. For 32 bit binaries,
  you can omit this key altogether. Note for advanced users: CMakeBuilder will
  automatically translate the given argument to the correct argument for
  `vcvarsall.bat`.
  **Note**: If you're using the "NMake Makefiles" generator, you're out of luck.
  This generator refuses to build for anything other than x86 it seems. Consider
  switching to Ninja if you want a fast bare-bones build system.

* `visual_studio_versions` [optional] [ONLY FOR WINDOWS]

  This must be a list of numbers specifying the preferred versions of Visual
  Studio to look for. For instance, setting this to `[ 15, 14 ]`, CMakeBuilder
  will first look for Visual Studio 15 2017, and if that can't be found, it will
  look for Visual Studio 14 2015. Obviously, this is only applicable when your
  generator is equal to `"Visual Studio"`.

Any key may be overridden by a platform-specific override. The platform keys
are one of `"linux"`, `"osx"` or `"windows"`. For an example on how this works,
see below.

## Example Project File

Here is an example Sublime project to get you started.

```json
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
            "build_folder": "${project_path}/build",
            "command_line_overrides":
            {
                "BUILD_SHARED_LIBS": true,
                "CMAKE_BUILD_TYPE": "Debug",
                "CMAKE_EXPORT_COMPILE_COMMANDS": true
            },
            "generator": "Unix Makefiles",
            "windows":
            {
                "generator": "Visual Studio",
                "configurations":
                [
                    "Debug"
                ]
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
* `cmake_run_ctest`, arguments: `{ test_framework : str }`
* `cmake_write_build_targets`, arguments: `None`.
* `cmake_new_project`, argumets: `None`.

### Available Commands in the Command Palette

* `CMakeBuilder: Browse Build Folder...`
* `CMakeBuilder: Clear Cache`
* `CMakeBuilder: Configure`
* `CMakeBuilder: Diagnose (What Should I Do?)`
* `CMakeBuilder: Run CTest`
* `CMakeBuilder: Write Build Targets To Sublime Project File`
* `CMakeBuilder: New Project`

All commands are accessible via both the command palette as well as the tools
menu at the top of the window.

### Available Settings

* `configure_on_save` : JSON bool

  If true, will run the `cmake_configure` command whenever you save a 
  CMakeLists.txt file or CMakeCache.txt file.

* `write_build_targets_after_successful_configure` : JSON bool

  If true, will run
  the command `cmake_write_build_targets` after the command `cmake_configure`
  finishes with exit status 0.

* `silence_developer_warnings` : JSON bool

  If true, will add the option `-Wno-dev` to the CMake invocation of the 
  `cmake_configure` command.

* `always_clear_cache_before_configure` : JSON bool

  If true, always clears the CMake cache before the `cmake_configure` command is
  run.

* `ctest_command_line_args` : JSON string

  Command line arguments passed to the CTest invocation when you run 
  `cmake_run_ctest`.

* `generated_name_for_build_system` : JSON string

  The name for the generated build system when you run
  `cmake_write_build_targets`. Can have arbitrary snippet-like variables.

## How Do I Manage Cross-Platform Project Files?

By default, the name of the generated build system is the name of your project,
followed by the platform in parentheses. Thus, multiple build systems may
coexist in a single project file.

## Keybindings

There are no default keybindings. You can create them yourself. The relevant
commands are

* `cmake_configure`,
* `cmake_write_build_targets` and
* `cmake_run_ctest`.

## Extra Goodies

### Project Template
You can run the command

    CMakeBuilder: New Project

from the tools menu or from the command palette to create a new template
project.

### Clearing the cache
To force CMake files re-generation run

    CMakeBuilder: Clear Cache

and then run

    CMakeBuilder: Configure

or you can do both in one go with

    CMakeBuilder: Clear Cache and Configure

but be aware that this does not ask for confirmation for the deletion of the
cache files.

### Diagnostics/Help
If you get stuck and don't know what to do, try running

    CMakeBuilder: Diagnose (What Should I Do?)

### Tools Menu
All commands are also visible in the Tools menu under "CMakeBuilder".

![11][11] <!-- Screenshot #11 -->

### Running unit tests with CTest
If you have unit tests configured with the [add_test][2] function of CMake, then
you can run those with the command

    CMakeBuilder: Run CTest

By default, this command will not output what your unit test outputs, unless the
test fails. This gives you a clean overview of what runs correctly and what is
failing and why.

### Syntax highlighting for CMakeCache.txt and the output panel
There is syntax highlighting for the CMakeCache.txt file, for the configure
step, and for the CTest output. You can press F4 to go to the error message in
the configuration step and the CTest output. Goto error in the CTest output
only works if you're using something that outputs error messages in the form
of the boost unit test framework.

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

## Contributing

See [CONTRIBUTING.md][1]

[1]: CONTRIBUTING.md
[2]: https://cmake.org/cmake/help/latest/command/add_test.html
[9]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/9.png
[10]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/10.png
[11]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/11.png
[12]: https://raw.githubusercontent.com/rwols/CMakeBuilder/screenshots/screenshots/12.png
