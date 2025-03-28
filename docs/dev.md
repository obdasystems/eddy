# Setting up a development environment

This guide will help you in setting up a development environment
to work on Eddy.

At a minimum, you need to have [git](http://git-scm.com/), [Python 3.9](https://www.python.org) or later
and a Java Development Kit (JDK) 11 or later installed on your system.

For the JDK, you can either use the system-wide installation, or directly unpack
a copy inside Eddy's repository checkout.

The recommended way to set up a development environment for Eddy is to use an isolated
[virtual environment](https://docs.python.org/3/tutorial/venv.html). This makes
sure that only the required dependencies are installed, avoiding possible conflicts that can be
caused with packages managed by the system-wide Python installation.
This also allows for easy testing with different versions of the Python interpreter
and PyQt5 dependencies, without having to break your system installation.

## On Windows

Install [Python 3.9](https://www.python.org/downloads/release/) or later, [Git](https://git-scm.com/downloads),
and a JDK 11 or later. We recommend downloading the latest OpenJDK 11 build from [Adoptium] or the latest
JDK 11 from Oracle. Make sure the corresponding executables can be found in your `PATH`.

Make sure to set the `JAVA_HOME` environment variable to point to the location where the JDK is installed.

#### Install a C compiler (optional)
If you wish to build all dependencies from source, you will need to install a C compiler.
If you are ok with using prebuilt wheels from PyPI, you can safely ignore this step.

Download and install [Visual C++ Build Tools v14.0](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
Make sure to select `VC++ 2015.3 v14.00 toolset for Desktop` from the individual components tab in the installer menu.

Once the installation is complete, you can easily access a command prompt that has
everything configured to use the C compiler by using the Visual Studio 2015 Native
Tools Command Prompt corresponding to your OS architecture,
e.g. for x64 Windows it is located in:

    Start -> Visual Studio 2015 -> Visual Studio Tools -> Windows Desktop Command Prompts -> VS2015 x64 Native Tools Command Prompt

#### Creating installers (optional)
If you wish to build an installer executable for Windows, you will also need to
install [InnoSetup](http://www.jrsoftware.org/isinfo.php).

#### Creating a virtual environment

Choose a directory where to store your virtualenvs. In this guide, we assume
to use the user's home directory.

Switch to the user home directory (replace with your selected folder):

    C:\> cd %USERPROFILE%

Create a new virtual environment with the `venv` module, using the command:

    C:\> python -m venv eddy-venv

Activate the virtual environment with:

    C:\> eddy-venv\Scripts\activate.bat

Clone Eddy using your preferred IDE, or by running the command:

    C:\> git clone -b develop https://github.com/obdasystems/eddy.git

Update `pip` and synchronize the required Python dependencies from PyPI:

    C:\> cd eddy
    C:\> pip install -U pip setuptools wheel pip-tools
    C:\> pip-sync requirements\out\requirements-<python_version>-winnt.txt

where `<python_version>` corresponds to the venv python version (e.g. `py39` for Python 3.9.x).

If you wish to work on the latest development snapshot, you can switch to
the `develop` branch:

    C:\> git checkout develop

If you prefer to use a local copy of the JDK, simply download one and unpack it
inside the `eddy/resources/java` folder (you will have to create it).
If you prefer to use the system-wide Java installation instead, you only need to set the
`JAVA_HOME` environment variable for your user to point to the JDK installation directory,
although the runtime will try to detect one if this is not set, but it can sometimes fail.

To start Eddy, simply *cd* to the root of the repository, and execute the command:

    C:\> python run.py

## On macOS

Make sure Xcode command line tools are installed. From a terminal window, type:

    $ xcode-select --install

Install [Homebrew](http://brew.sh/).

Install [Python 3.9](https://www.python.org/downloads/release/) or later using your
preferred method. In this guide we'll show how to install a Python interpreter by
compiling it from sources using [pyenv](https://github.com/pyenv/pyenv).

###### Via Homebrew

Install the latest `python` formula from Homebrew:

    $ brew install python

###### Using the official installer:

Download the latest installer from [python.org](https://www.python.org/downloads/release),
execute it, and follow the installation instructions.

###### Using pyenv

Install `pyenv` formula via Homebrew or by cloning the [repository](https://github.com/pyenv/pyenv):

    $ brew install pyenv
    $ pyenv init
    $ # compile and install a python version, e.g. 3.9.20
    $ env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.9.20

**NOTE**: Make sure to add the `PYTHON_CONFIGURE_OPTS="--enable-framework"` to the `pyenv` command
if you intend to use PyInstaller to build standalone releases.

Install a JDK 11 or later.
We recommend installing either the latest OpenJDK 11 or later LTS build from [Adoptium] using Homebrew cask:

    $ brew cask install temurin@11       # For JDK 11
    $ brew cask install temurin@17       # For JDK 17

Set the `JAVA_HOME` environment variable to point to the location where the JDK is installed.

    $ export JAVA_HOME="`/usr/libexec/java_home -v 11`" # For JDK 11
    $ export JAVA_HOME="`/usr/libexec/java_home -v 17`" # For JDK 17

Choose a location where to store the virtualenv and create it.
The following command creates a new virtualenv inside `$HOME/eddy-venv`:

    $ PYENV_VERSION=3.9.20 pyenv exec python -m venv $HOME/eddy-venv

You can change the `PYENV_VERSION` variable to match the python version you want to use.

Activate the virtual environment with:

    $ source $HOME/eddy-venv/bin/activate

Clone Eddy repository using your favorite IDE, or from the terminal by running the command:

    $ git clone https://github.com/obdasystems/eddy.git

Update `pip` and install required Python dependencies from PyPI:

    $ cd eddy
    $ pip install -U pip setuptools wheel pip-tools
    $ pip-sync requirements/out/requirements-<python_version>-macos.txt

where `<python_version>` corresponds to the venv python version (e.g. `py39` for Python 3.9.x).

If you prefer to use a local copy of the JDK, simply download one and unpack it
inside the `eddy/resources/java` folder (you will have to create it).
If you prefer to use the system-wide Java installation instead, you only need to set the
`JAVA_HOME` environment variable for your user to point to the JDK installation directory.
If you don't set it, Eddy will automatically attempt to locate an appropriate JDK installed
on you system.

To start Eddy, `cd` to the root of the repository and execute:

    $ python run.py

## On GNU/Linux

Most GNU/Linux distributions come with Python 3 already preinstalled, if that's not the case
you can use your package manager to install it for all users, or use [pyenv](https://github.com/pyenv/pyenv)
to compile and install it from sources for you local user. You will also need to have
[Git](https://git-scm.org) installed to clone the repository, and a JDK 11 or later.

#### Installing Python using the package manager
Here are the commands to install Python3 via the package manager for some of the most common Linux distros.

###### On Debian, Ubuntu, and derivatives
    $ sudo apt-get install python3

###### On Fedora / CentOS 8 / RHEL 8
    $ sudo dnf install python3

###### On ArchLinux / Manjaro
    $ sudo pacman -Sy python

#### Installing Python using pyenv (optional)
If your system does not provide a recent enough version of Python, or you wish
to use a more recent one, you can install python by compiling it from sources
using *pyenv*.

You will need to install `gcc`, `git` and a few compile dependencies:

###### On Debian, Ubuntu, and derivatives

    $ sudo apt-get install build-essential libsqlite3-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libffi-dev git

###### On Fedora / CentOS 8 / RHEL 8

    $ sudo dnf install gcc sqlite-devel openssl-devel zlib-devel bzip2-devel readline-devel libffi-devel git

###### On ArchLinux / Manjaro

    $ sudo pacman -Sy gcc git openssl zlib bzip2 readline libffi

Clone [pyenv](https://github.com/pyenv/pyenv) repository:

    $ git clone https://github.com/pyenv/pyenv ~/.pyenv

Compile and install a Python interpreter, e.g. 3.9.20:

    $ export PYENV_ROOT="$HOME/.pyenv"
    $ export PATH="$PYENV_ROOT/bin:$PATH"
    $ pyenv init
    $ env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.9.20

**NOTE**: Make sure to add the `PYTHON_CONFIGURE_OPTS="--enable-shared""` environment variable
 to the `pyenv` command if you intend to use PyInstaller to build standalone releases.

Choose a location for the virtualenv and create it. In what follows we show how to create it
in a directory named `eddy-venv` inside the user's home folder:

    $ PYENV_VERSION=3.9.20 pyenv exec python -m venv $HOME/eddy-venv

Activate the virtual environment:

    $ source $HOME/eddy-venv/bin/activate

Clone Eddy using your favorite IDE, or via the shell by running the command:

    $ git clone https://github.com/obdasystems/eddy.git

Update `pip` and install required Python dependencies from PyPI:

    $ cd eddy
    $ pip install -U pip setuptools wheel pip-tools
    $ pip-sync requirements/out/requirements-<python_version>-linux.txt

where `<python_version>` corresponds to the venv python version (e.g. `py39` for Python 3.9.x).

Install a JDK 11 or later. You can download a prebuilt one from [Adoptium], or use your distribution package
manager to install it. We recommend installing either a JDK 11 LTS, or any later LTS release:

###### On Debian, Ubuntu, and derivatives

    $ sudo apt-get install openjdk-11-jdk  # For JDK 11
    $ sudo apt-get install openjdk-17-jdk  # For JDK 17

###### On Fedora / CentOS 8 / RHEL 8

    $ sudo dnf install java-11-openjdk  # For JDK 11
    $ sudo dnf install java-17-openjdk  # For JDK 17

###### On ArchLinux / Manjaro

    $ sudo pacman -Sy jdk11-openjdk  # For JDK 11
    $ sudo pacman -Sy jdk17-openjdk  # For JDK 17

If you prefer to use a local copy of the JDK, simply download one and unpack it
inside the `eddy/resources/java` folder (you may have to create it).
If you prefer to use the system-wide Java installation instead, you only need to set the
`JAVA_HOME` environment variable for your user to point to the JDK installation directory.
If you don't set it, Eddy will automatically attempt to locate an appropriate JDK installed
on you system.

To start Eddy, *cd* into the repository, and run the command:

    $ python run.py

## Creating standalone releases

Standalone releases are built using [PyInstaller] for every Eddy release and published to [GitHub releases].
They are the simplest form of distribution, that includes the application
with all the required dependencies (including the Python interpreter and JVM).

Eddy is currently distributed in the following forms:
* `Windows amd64` installer (built with InnoSetup)
* `Windows x86` installer (built with InnoSetup)
* `Windows amd64` standalone package (.zip archive)
* `Windows x86` standalone package (.zip archive)
* `macOS x86_64` app bundle (distributed as .dmg)
* `Linux x86_64` AppImage (.AppImage file)
* `Linux x86_64` standalone package (.tar.gz archive)
* source package (.tar.gz or .zip archive)

### On Windows
To build a Windows binary installer, set up a development environment
as described in the previous section, then run the following command
from the root of the repository:

    $ python setup.py innosetup

To build a Windows standalone (.zip) release, run the command:

    $ python setup.py standalone

Once the building process is completed you will find the built
package(s) inside the *dist* directory.

### On macOS
To build a macOS disk image (.dmg) containing the app bundle,
set up a development environment as described in the previous section,
then run the following command from the root of the repository:

    $ python setup.py createdmg

Once the building process is completed you will find the built
package(s) inside the *dist* directory.

### On GNU/Linux

To build a Linux AppImage (.AppImage) release, you will need to set up
a development environment as described in the previous section,
download the [appimagetool] executable, then run the following
command from the root of the repository:

    $ python setup.py appimage

To build Linux standalone tarball (.tar.gz), run the following command:

    $ python setup.py standalone

Once the building process is completed you will find the built
package(s) inside the *dist* directory.


[Adoptium]: https://adoptium.net/
[GitHub releases]: https://github.com/obdasystems/eddy/releases
[PyInstaller]: https://www.pyinstaller.org/
[appimagetool]: https://appimage.github.io/appimagetool
