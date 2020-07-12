# Installing Eddy

Eddy can be installed via one of the following methods:

* Downloading a standalone package from [GitHub releases].
* Using one of the prebuilt Python wheels or source package from [GitHub releases].
* Installing the latest snapshot from the sources in this [GitHub repository].

Standalone packages come with all the required dependencies already bundled.
This is the simplest way to get up and running with Eddy if you're on Windows or macOS.
However, if you prefer manually installing a prebuilt wheel or a source package,
then you will need to have Python 3.5 or later, and Java 1.8.0 or later already
installed on your system.

If you encounter issues with the installation, please report them using the [issue tracker].

### Using a standalone package

Using a standalone package is the simpler way to get Eddy up and running, as
it comes with its own copy of the Python interpreter and Java Virtual Machine.
Windows and macOS users will most likely want to choose this option.
GNU/Linux users can also find standalone packages for older versions of Eddy,
however, starting from version 3.0 we do not support this form of distribution
for any Linux distro, and instead recommend to use the prebuilt Python wheels,
or a source package.

#### Windows

Simply download and install the latest executable from [GitHub releases].
You can choose between 32 and 64 bit versions, depending on your system.
If you do not have administrator privileges on your machine, you can download
a standalone package provided as a `.zip` archive, unpack it, and start Eddy
by double-clicking the `Eddy` executable.

#### macOS

Download the latest prebuilt `.dmg` from [GitHub releases], open it, then
drag the Eddy application over the `Applications` folder.

#### GNU/Linux (deprecated)

Simply download the tarball from [GitHub releases] and unpack it anywhere on your system.
You can start Eddy by running the `Eddy` executable.

### Installing from a source package or prebuilt wheel

In order to install Eddy from a source package or prebuilt wheel you will need to have
Python 3.5 or later, and a Java Runtime Environment 1.8 or later already installed on
your system. If you do not have administrator privileges on the machine, you can install
Eddy in a virtual environment to keep it separate from the system installation of Python.
As of version 3.0, this is the recommended method of installing Eddy on GNU/Linux.

The following additional Python requirements are needed:
 * PyQt5 >= 5.8
 * jpype1 >= 0.7.1
 * rfc3987

 You can either choose to install Eddy as a system python module, or by using a
 virtual environment. The advantage is that using this method the application
 will be available to all users on the system, without having to activate
 the virtual environment first.
 The recommended option is to install using a virtual environment.

##### Installing using a virtual environment

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

2. Download a prebuilt wheel from [GitHub releases] and install Eddy:

 ```bash
 $ pip install PyQt5 >= 5.8 # Only if not already provided by the system installation
 $ pip install Eddy-<version>-py3-none-any.whl
 ```
e.g., for v1.2.0:
```bash
 $ pip install Eddy-1.2.0-py3-none-any.whl
```
or, when using a source package:
 ```bash
 $ pip install PyQt5 >= 5.8 # Only if not already provided by the system installation
 $ pip install https://github.com/obdasystems/eddy/archive/<version>.tar.gz
 ```
e.g.:
```bash
 $ pip install https://github.com/obdasystems/eddy/archive/v1.2.0.tar.gz
```

If you prefer to use a local copy of the JDK, simply download one and and unpack it
inside the `eddy/resources/java` folder (you will have to create it).
If you prefer to use the system-wide Java installation instead, you only need to set the
`JAVA_HOME` environment variable for your user to point to the JDK installation directory.

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

#### Installing as system Python module (NOT RECOMMENDED)

If you want to use the system Python installation on Linux, it is recommended to use your
distribution package manager to install the additional dependencies as installing
them from PyPI will most-likely cause dependency issues with existing applications:

###### On Debian, Ubuntu, and derivatives
```bash
 $ sudo apt-get install python3-pyqt5 python3-jpype python3-rfc3987
```

###### On Fedora / CentOS 8 / RHEL 8
```bash
 $ sudo dnf install python3-qt5 python3-jpype python3-rfc3987
```

###### On ArchLinux / Manjaro
```bash
 $ sudo pacman -S python-pyqt5 python-rfc3987
 $ sudo yaourt -S python-jpype # From AUR
```

Download a prebuilt wheel from [GitHub releases] and install Eddy, you will need
administrator privileges:

 ```bash
 $ sudo pip install Eddy-<version>-py3-none-any.whl
 ```
e.g., for v1.2.0:
```bash
 $ sudo pip install Eddy-1.2.0-py3-none-any.whl
```
or, when using a source package:
 ```bash
 $ sudo pip install https://github.com/obdasystems/eddy/archive/<version>.tar.gz
 ```
e.g.:
```bash
 $ sudo pip install https://github.com/obdasystems/eddy/archive/v1.2.0.tar.gz
```

Once the installation is completed, you will be able to start Eddy by running
the `eddy` command in a terminal, or by executing the `eddy` python module:
```bash
 $ python -m eddy
```
or, simply:
```bash
 $ eddy
```

To uninstall Eddy, simply use `pip` like any other python package:
```bash
 $ sudo pip uninstall eddy
```

#### Installing the latest snapshot from the repository

You can install Eddy directly by checking out the sources from the [GitHub repository]
using Git. Just install the additional dependencies as described above,
then install Eddy using the repository URL:
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
