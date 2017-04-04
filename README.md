# CMakeBuilder

Configure, build and test a CMake project right from within Sublime Text 3.

## Installation

Run the command

    Package Control: Install Package

and look for CMakeBuilder.

## TL;DR

1. Open a `.sublime-project`.

2. Add this to the project file on the same level as `"folders"`, `"settings"`:

    ```json
    "cmake":
    {
       "build_folder": "${project_path}/build"
    }
    ```

3. Run the command

    ```
    CMakeBuilder: Configure
    ```

   from the command palette; wait for it to finish.

4. Run the command

    ```
    CMakeBuilder: Write Build Targets to Sublime Project File
    ```

5. Check out your new build system in your `.sublime-project`.

6. Press <kbd>CTRL</kbd> + <kbd>B</kbd> or <kbd>⌘</kbd> + <kbd>B</kbd>.

7. Hit <kbd>F4</kbd> to jump to errors and/or warnings.

## Reference

### The CMake Dictionary

By "CMake dictionary" we mean the JSON dictionary that you define at the top
level of your sublime project file with key "cmake". The CMake dictionary
accepts the following keys:

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

* `configurations` [optional]

  This key is only relevant for the Visual Studio generator (see `generator` 
  down below). This shall be a JSON list of strings defining the desired 
  configurations. For instance, `"Debug"` and `"Release"`. If omitted, the 
  default target is built, which would be Debug.

* `filter_targets` [optional]

  A JSON list consisting of strings. Each build target is tested against all of
  the items in this list. If any of the strings in this list is in the string
  representation of the target, the target will be added to the sublime build
  system.

* `generator` [optional]

  A JSON string specifying the CMake generator. 

  - Available generators for osx: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with brew.

  - Available generators for linux: "Ninja" and "Unix Makefiles".

    If no generator is specified on osx, "Unix Makefiles" is the default
    generator. For "Ninja", you must have ninja installed. Install it with apt.

  - Available generators for windows: "NMake Makefiles" and "Visual Studio".

    If no generator is specified on windows, "Visual Studio" is the default
    generator. For both "Visual Studio" and "NMake Makefiles", you need
    Microsoft Visual Studio C++. The latest version of Visual Studio is searched
    for. There is no support for 64-bit building as of this writing.

* `root_folder` [optional]

  The directory where the root CMakeLists.txt file resides. If this key is not
  present, the directory where the sublime project file is located is assumed to
  have the root CMakeLists.txt file.

### Available Scripting Commands

* `cmake_clear_cache_and_configure`, arguments: `None`.
* `cmake_clear_cache`, arguments: `{ with_confirmation : bool }`.
* `cmake_configure`, arguments: `None`.
* `cmake_diagnose`, arguments: `None`.
* `cmake_open_build_folder`, arguments: `None`.
* `cmake_run_ctest`, arguments: `{ test_framework : str }`
* `cmake_write_build_targets`, arguments: `None`.

### Available Commands in the Command Palette

* `CMakeBuilder: Browse Build Folder...`
* `CMakeBuilder: Clear Cache`
* `CMakeBuilder: Configure`
* `CMakeBuilder: Diagnose (What Should I Do?)`
* `CMakeBuilder: Run CTest`
* `CMakeBuilder: Write Build Targets To Sublime Project File`

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

## Example Project File

Here is an example Sublime project to get you started.

```json
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
    },
    "folders":
    [
        {
            "path": "."
        }
    ],
    "settings":
    {

    }
}

```

## How Do I Manage Cross-Platform Project Files?

I played around with platform-specific overrides in the build system, but it
looks like the `variants` key does not respond to platform overrides. In
conclusion I believe the best way to have your project be cross-platform for
Sublime Text is to write a `.sublime-project` file for each platform. For
example, you'd have three files named `myproject (OSX).sublime-project`, 
`myproject (Linux).sublime-project` and `myproject (Windows).sublime-project`.
Each one then has its own CMake dictionary with relevant settings and build
systems.

## Keybindings

There are no default keybindings. You can create them yourself. The relevant
commands are

* `cmake_configure`,
* `cmake_write_build_targets` and
* `cmake_run_ctest`.

## Extra Goodies

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
of the boost unit test framework right now, but I'll look into the google test
framework in the future.

![9][9]   <!-- Screenshot #9  -->
![10][10] <!-- Screenshot #10 -->
![12][12] <!-- Screenshot #12 -->

## List of Valid Variable Substitutions
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
