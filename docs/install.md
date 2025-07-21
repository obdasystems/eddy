# Installing Eddy

Eddy can be installed via one of the following methods:

* From [PyPI](https://pypi.org/project/Eddy/) releases.
* Downloading a standalone release from [GitHub releases].
* Installing from source using a release tarball or from the [GitHub repository].

Standalone releases come with all the required dependencies already bundled.
This is the simplest way to get up and running with Eddy.
However, if you prefer manually installing from PyPI or from source, then you will need to have
Python 3.9 or later, and Java 11 or later already installed on your system.

If you encounter issues with the installation, please report them using the [issue tracker].

## Using a PyPI release

You would need to have a Java Runtime Environment 11 or later installed on your system,
then install PyQt5 and Eddy from the PyPI repository (we recommend setting up a virtual environment
to not mess up with the system Python packages):

    $ pip install PyQt5>=5.15 Eddy

Then you can later start Eddy by running the `eddy` command or by running the `eddy` module:

    $ eddy
    $ # or
    $ python3 -m eddy

If you have Java installed in a non-standard location, simply point the `JAVA_HOME` environment
variable to the location where the JVM is stored.

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

**NOTE**: standalone tarball releases have been deprecated and will be removed in future versions of Eddy.
It is recommended to switch AppImage builds as these work more reliably between the different distros,
or simply resort to installation from the [PyPI](https://pypi.org/project/Eddy/)repository.

## Installing from a source tarball

In order to install Eddy from a source tarball you will need to have Python 3.9 or later,
and a Java Runtime Environment 11 or later already installed on your system.

The following additional Python requirements are needed:
 * PyQt5 >= 5.15
 * jpype1 >= 1.4.1
 * rdflib >= 6.2.0
 * openpyxl
 * rfc3987

You can either choose to install Eddy as a system python module, or by using a
virtual environment. The advantage of installing as a system python module is
that using this method the application will be available to all users on the system,
without having to activate the virtual environment first, however this can cause issues
if your system provides conflicting versions of the python dependencies.
Hence, the recommended option is to install using a virtual environment.

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
 $ pip install "PyQt5>=5.15" # Only if not already provided by the system installation
 $ pip install https://github.com/obdasystems/eddy/archive/<version>.tar.gz
 ```
e.g.:
```bash
 $ pip install https://github.com/obdasystems/eddy/archive/v3.6.tar.gz
```

**NOTE**: Depending on your platform, you may encounter an issue during the installation of PyQt5 where
the corresponding command gets stuck indefinitely. This seems to be related with `pip` failing to detect
a prebuilt wheel for your platform, and trying to compile the PyQt5 module from sources which then gets stuck
at the license agreement prompt.

If you happen to stumble upon this issue, first try to update the pip module and repeat the PyQt5 installation step:
```bash
$ python -m pip install --upgrade pip
```
If this does not solve the issue (e.g. if there are really no prebuilt wheels available for your platform
from [PyPI], such as is the case for aarch64 Linux hosts), you can try to get past the PyQt5 license agreement
prompt by running the following command:
```bash
$ pip install pyqt5 --config-settings --confirm-license= --verbose
```
GNU/Linux users can also use the version of PyQt5 provided by their distribution by creating the virtual environment
with the `--system-site-packages` option.
Note that compiling PyQt5 from sources can potentially take a long time.
More details on the issue are available [here](https://stackoverflow.com/questions/66546886/pip-install-stuck-on-preparing-wheel-metadata-when-trying-to-install-pyqt5).

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
[PyPI]: https://pypi.org
