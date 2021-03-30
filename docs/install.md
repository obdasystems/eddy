# Installing Eddy

Eddy can be installed via one of the following methods:

* Downloading a standalone release from [GitHub releases].
* Installing from source using a release tarball or from the [GitHub repository].

Standalone releases come with all the required dependencies already bundled.
This is the simplest way to get up and running with Eddy.
However, if you prefer manually installing from source, then you will need to have
Python 3.5 or later, and Java 1.8 or later already installed on your system.

If you encounter issues with the installation, please report them using the [issue tracker].

## Using a standalone release

Using a standalone release is the simpler way to get Eddy up and running, as
it comes with its own copy of the Python interpreter and Java Virtual Machine.

### Windows

Simply download and run the latest installer from [GitHub releases].
You can choose between 32 and 64 bit versions, depending on your system.

If you do not have administrator privileges on your machine, you can download
the standalone version provided as a `.zip` archive, unpack it, and start Eddy
by double-clicking the `Eddy` executable.

### macOS

Download the latest prebuilt `.dmg` from [GitHub releases], open it, then
drag the Eddy application over the `Applications` folder.

### GNU/Linux

Download the latest AppImage from [GitHub releases].
To start Eddy, make the AppImage executable (via `chmod a+x`) and run it.

Alternatively, you can download the standalone version provided as a tarball
from [GitHub releases] and unpack it anywhere on your system.
You can start Eddy by running the `Eddy` executable.

## Installing from a source tarball

In order to install Eddy from a source tarball you will need to have Python 3.5 or later,
and a Java Runtime Environment 1.8 or later already installed on your system.

The following additional Python requirements are needed:
 * PyQt5 >= 5.8
 * jpype1 >= 0.7.1
 * rfc3987

 You can either choose to install Eddy as a system python module, or by using a
 virtual environment. The advantage is that using this method the application
 will be available to all users on the system, without having to activate
 the virtual environment first.
 The recommended option is to install using a virtual environment.

### Installing using a virtual environment

1. Choose a location where to install the virtualenv and use the `venv` python module to create it:
 ```bash
 $ python -m venv <path/to/venv>
 $ source <path/to/venv/bin/activate>
 ```
e.g. to create it inside a folder named `eddy-venv` in the current directory:
 ```bash
 $ python -m venv eddy-venv
 $ source eddy-venv/bin/activate
 ```
or, on Windows:
 ```cmd
 C:\> python -m venv eddy-venv
 C:\> eddy-venv\Scripts\activate.bat
 ```

2. Download a source tarball from [GitHub releases] and install Eddy:

 ```bash
 $ pip install PyQt5 >= 5.8 # Only if not already provided by the system installation
 $ pip install https://github.com/obdasystems/eddy/archive/<version>.tar.gz
 ```
e.g.:
```bash
 $ pip install https://github.com/obdasystems/eddy/archive/v1.2.0.tar.gz
```

To use a specific JRE installation, simply point the `JAVA_HOME` environment variable
to it before starting Eddy.

To start Eddy, an `eddy` script will be available inside the virtualenv.
Just type `eddy` in a terminal, or execute the *eddy* module
(make sure the virtualenv is active):
```bash
 $ python -m eddy
```
or simply
```bash
 $ eddy
```

To uninstall Eddy, just delete the virtualenv folder.

### Installing the latest snapshot from the repository

You can install Eddy directly by checking out the sources from the [GitHub repository].
You will need to have git installed on your system.

```bash
 $ pip install git+https://github.com/obdasystems/eddy.git@master
```

If you wish to install the latest development snapshot, simply install from the *develop*
branch:
```bash
 $ pip install git+https://github.com/obdasystems/eddy.git@develop
```

[GitHub repository]: https://github.com/obdasystems/eddy
[GitHub releases]: https://github.com/obdasystems/eddy/releases
[issue tracker]: https://github.com/obdasystems/eddy/issues
