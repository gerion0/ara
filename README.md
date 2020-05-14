ARA - Automatic Real-time System Analyzer
=========================================

Tool to automatically analyse real-time systems.
Currently capable of systems written with FreeRTOS and OSEK.

Building
--------

The following dependencies are needed:

- [meson](https://mesonbuild.com/) (>=0.52.0)
- [llvm](http://llvm.org/) (==9)
- [cython](https://cython.org/) (>=0.29.0)
- [python](https://www.python.org/) (>=3.6)

Getting packages in SRA lab:
```
echo addpackage llvm-9.0 >> ~/.bashrc
pip3 install --user meson
. ~/.profile
```


To build the program type:
```
meson build
cd build
ninja
```
(Note: `build` is actually a placeholder for an arbitrary path.)

Usage
-----

To run the program `ara.py` needs to be executed with the correct `PYTHONPATH`.
For convenience a small wrapper script is generated by meson that sets the correct environment variables. Run this with:
```
build/ara.sh -h
```

Note: The input of the program are some LLVM IR files. To compile a C/C++ application into IR files, invoke clang with the flags described in `appl/meson.build`.

Test Cases
----------

There are some predefined test cases. Run them with:
```
cd build
meson test
```

Architecture
------------

ARA is divided into steps that operate on the same system model. When starting the program the correct chain of steps is calculated and then executed. A listing of the steps can be retrieved by:
```
build/ara.sh -l
```
Steps can be written into Python (defined in `steps`) or in C++ (defined in `steps/native`).
The model is written in C++ with Python bindings (defined in `graph`).

Program configuration
---------------------

ARA con be configured in multiple ways:

1. Globally applied options: Normally specified options at the command line. See `build/ara.sh -h` for all available options.
2. Per step applied options: See the following text.

Steps can define their own options. See `build/ara.sh -l` for a list of steps and their options.
Step wise configuration can be configured with the `--step-settings` command line switch.

Input must be a JSON file with this syntax:
```
{
	"Stepname1": {
		"key1": "value",
		"key2": 45
	},
	"Stepname2": {
		"other_key1": "other_value",
	},
	...
}
```
Additionally to that with the step-settings file steps can be configured to run multiple times with different options. In this case the settings file get an additional entry `steps` that can be a list of steps that should be executed:
```
{
	"steps": ["MyStep1", "MyStep2", ...],
	"MyStep1": {
		"key": "value"
	}
}
```
or a list of step configurations or a mix of both:
```
{
	"steps": [
		"MyStep1",
		{
			"name": "MyStep2"
			"key": "value"
		}
		{
			"name": "MyStep2"
			"key": "value2"
		}
	],
	"MyStep1": {
		"key": "value"
	}
}
```
In this case *MyStep2* is executed two times with different options.

Applying of options goes from local to global. So a step get the configuration in `steps` first, then the per step configuration and then the global configuration.

Developing
----------
If you want to develop with ARA, some common actions are usual.

### Adding a new Python step

- Create the step in the `steps` directory. You can use `steps/dummy.py` as template.
- Add the step to `steps/__init__.py`.
  - Add to the `__all__`-attribute.
  - Add to the `provide_steps()` function.
- Create a test case for this step in the `test` directory. See the existing tests and `test/meson.build` for hints how to achieve this.

### Adding a new C++ step

- Create the step in the `steps/native` directory. You can use `steps/native/cdummy.{cpp,h,pxd}` as template.
- Add the step to `steps/native/meson.build` (both the `pxd` and the `cpp` file) to enable compilation.
- Add the step to `steps/native/native_step.pyx` to create a Python wrapper. Add an `cimport` and add the step to `provide_steps`.
- Create a test case for this step in the `test/native_step_test` directory. Usually, it is enough to add your test to `test/native_step_test/meson.build`.
  - C++ steps often need other C++ code to test it. For that add an extra test step in `steps/native/test.h` and `steps/native/test/` and call it from your test case.

### Autoformat

ARA uses `clang-format` as automatic formatting for its C++ sources.

One possibility to integrate this with git is a pre-commit hook like the following. Create a file `.git/hooks/pre-commit`:
```sh
#!/bin/sh

if git clang-format --diff $(git diff --name-only --cached 2>&1) 2>&1 | grep diff 2>&1 >/dev/null; then
	echo "ERROR: clang-format has changes."
	exit 1
fi
exit 0
```
And then manually invoke `git clang-format`.

Troubleshooting
---------------

### LLVM is not found
Sometime Meson is unable to find the correct LLVM libraries because detection of the `llvm-config` file fails.
In this case, add a file `native.txt` with this content:
```
[binaries]
llvm-config = '/path/to/llvm-config'
```
Then configure your build directory with:
```
meson build --native-file native.txt
```

### meson directory is really/too big
This is because of precompiled headers. They fasten the build a little bit but need a lot of disk space. You can deactivate precompiled headers with:
```
meson configure -Db_pch=false
```
