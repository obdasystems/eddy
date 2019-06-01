# Eddy packaging documentation

Eddy is distributed as different packages:

* `Windows x64` installer (built with InnoSetup)
* `Windows x86` installer (built with InnoSetup)
* `Windows x64` standalone package (.zip archive)
* `Windows x86` standalone package (.zip archive)
* `macOS (Intel)` app bundle (distributed as .dmg)
* `Linux x86_64` standalone package (.tar.gz archive)
* `Linux i686` standalone package (.tar.gz archive)

To create distribution packages you need to have installed [Python 3.6](https://www.python.org) on your system. 
You also need to have installed [Git](http://git-scm.com/) on your system and make sure that the `git` command
is in your `PATH` environment variable.

# Packaging

The recommended way to package Eddy is from an isolated [virtual environment](https://docs.python.org/3/tutorial/venv.html). This makes 
sure that only the required dependencies are installed, avoiding possible conflicts that can be
caused with packages managed by the system-wide Python installation.

**NOTE**: When installing dependencies make sure to select the correct architecture corresponding
to your OS architecture, as cross-compiling to other architectures is untested and generally not supported
in the packaging process.

## On Windows

Install [Python 3.6](https://www.python.org/downloads/release/python-368/).  
Install [Git](https://git-scm.com/downloads).  
Install [Visual C++ Build Tools v14.0](https://visualstudio.microsoft.com/visual-cpp-build-tools/).  Make sure to select
`VC++ 2015.3 v14.00 toolset for Desktop` from the individual components tab in the installer menu.  
Install [Oracle JDK 1.8](https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html).  
Install [InnoSetup](http://www.jrsoftware.org/isinfo.php) (optional if you don't wish to generate the binary installer).  
Set the `JAVA_HOME` environment variable to point to the location where the JDK is installed.

Open Visual Studio 2015 Native Tools Command Prompt corresponding to your OS architecture,
e.g. for x64 Windows it is located in:

    Start -> Visual Studio 2015 -> Visual Studio Tools -> Windows Desktop Command Prompts -> VS2015 x64 Native Tools Command Prompt 

Switch to the user home directory:

    C:\> cd %USERPROFILE%
    
Create a new virtual environment using the command:

    C:\> python -m venv --copies eddy-venv-py36
    
Activate the virtual environment with:

    C:\> eddy-venv-py36\Scripts\activate.bat

Clone Eddy repository by running the command:

    C:\> git clone --recursive https://github.com/obdasystems/eddy.git
    
Update `pip` and install required Python dependencies from PyPI:
    
    C:\> cd eddy
    C:\> pip install -U pip setuptools wheel
    C:\> pip install -U -r requirements\cython.in
    C:\> pip install -U -r requirements\pyqt5.in
    C:\> pip install -U -r requirements\base.in
    C:\> pip install -U -r requirements\packaging.in

Make sure to copy the Oracle JRE 1.8 `jre` directory in `eddy/resources/java`.  
You can copy it directly from the JDK installation directory or download the JRE tarball
from the [Oracle JRE 1.8](https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) 
download page:

    C:\> md resources\java
    C:\> robocopy /s "%JAVA_HOME%\jre" resources\java\jre
    
To build a Windows binary installer, run the command:

    $ python setup.py innosetup

To build a Windows standalone (.zip) distribution, run the command:

    $ python setup.py bdist_archive --format=zip
    
Once the building process is completed you will find the built 
package(s) inside the *dist* directory. 

## On macOS

Make sure Xcode command line tools are installed. From a terminal window, type:

    $ xcode-select --install
 
Install [Homebrew](http://brew.sh/).  
Install [Python 3.6](https://www.python.org/downloads/release/python-368/) and [pyenv](https://github.com/pyenv/pyenv) using Homebrew
(alternatively, you can install Python 3.6 from the official binary installer):

    $ brew install pyenv
    $ pyenv init
    $ env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.6.8

**NOTE**: Make sure to to add the `PYTHON_CONFIGURE_OPTS` to the `pyenv` command
since it is required for PyInstaller to work on macOS.
    
Install [Oracle JDK 1.8](https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html).
Set the `JAVA_HOME` environment variable to point to the location where the JDK is installed.

    $ export JAVA_HOME="`/usr/libexec/java_home -v 1.8`"

Create a new virtual environment with:

    $ PYENV_VERSION=3.6.8 pyenv exec python -m venv --copies eddy-venv-py36
    
Activate the virtual environment with:

    $ source ./eddy-venv-py36/bin/activate
    
Clone Eddy repository by running the command:

    $ git clone --recursive https://github.com/obdasystems/eddy.git
    
Update `pip` and install required Python dependencies from PyPI:
    
    $ cd eddy
    $ pip install -U pip setuptools
    $ pip install -U -r requirements/cython.in
    $ pip install -U -r requirements/pyqt5.in
    $ pip install -U -r requirements/base.in
    $ pip install -U -r requirements/packaging.in

Make sure to copy the Oracle JRE 1.8 `jre` directory in `eddy/resources/java`.  
You can copy it directly from the JDK installation directory or download the JRE tarball
from the [Oracle JRE 1.8](https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) 
download page:
    
    $ mkdir resources/java
    $ cp -R "`/usr/libexec/java_home -v 1.8`/jre" resources/java/jre
    
Alternatively, you can make use of the `configure-virtualenv.sh` script 
located in the `scripts` directory to set up a customized virtual environment.
Invoke the script with the `--help` argument to get a list of the available options.

To build a macOS disk image (.dmg) containing the app bundle, run the command:

    $ python setup.py bdist_dmg

Once the building process is completed you will find the built 
package(s) inside the *dist* directory. 

## On GNU/Linux 

**NOTE**: In order to build distribution packages for 32 bit Linux distros it is required 
to build Qt5 and PyQt5 from source, as binary wheels from PyPI are not available. 

### Installing dependencies

In order to setup the virtual environment you will have to install Python 3.6, Git, and a JDK 1.8:

##### On Ubuntu / Debian / Mint

    $ sudo apt-get install build-essential libsqlite3-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev openjdk-8-jdk git

##### On Fedora

    $ sudo dnf install gcc sqlite-devel openssl-devel zlib-devel bzip2-devel readline-devel java-8-openjdk git

Clone [pyenv](https://github.com/pyenv/pyenv) repository:

    $ git clone https://github.com/pyenv/pyenv ~/.pyenv
    
Install Python 3.6:

    $ export PYENV_ROOT="$HOME/.pyenv"
    $ export PATH="$PYENV_ROOT/bin:$PATH"
    $ pyenv init
    $ env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.6.8

**NOTE**: Make sure to add the `PYTHON_CONFIGURE_OPTS` environment variable to the `pyenv`
command since it is required for PyInstaller to work.
    
Create a new virtual environment:

    $ PYENV_VERSION=3.6.8 pyenv exec python -m venv --copies eddy-venv-py36
    
Activate the virtual environment:

    $ source ~/eddy-venv-py36/bin/activate
    
Clone Eddy repository by running the command:

    $ git clone --recursive https://github.com/obdasystems/eddy.git
    
Update `pip` and install required Python dependencies from PyPI:
    
    $ cd eddy
    $ pip install -U pip setuptools
    $ pip install -U -r requirements/cython.in
    $ pip install -U -r requirements/pyqt5.in
    $ pip install -U -r requirements/base.in
    $ pip install -U -r requirements/packaging.in

Make sure to copy the Oracle JRE 1.8 `jre` directory in `eddy/resources/java`.  
You can download the JRE tarball from the [Oracle JRE 1.8](https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) 
download page:

    $ mkdir resources/java
    $ tar xzf jre-8*.tar.gz
    $ mv jre1.8.0* resources/java/jre
    
Alternatively, you can make use of the `configure-virtualenv.sh` script 
located in the `scripts` directory to set up a customized virtual environment.
Invoke the script with the `--help` argument to get a list of the available options.

To build Linux distribution packages, run the command:

    $ python setup.py bdist_archive --format=gztar

Once the building process is completed you will find the built 
package(s) inside the *dist* directory. 
