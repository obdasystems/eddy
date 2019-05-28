#!/usr/bin/env bash

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

set -e # Terminate the script in case an error occurs

usage() {
    echo "usage: $0 [options]"
    echo
    echo "supported options:"
    echo "    --branch=<branch>                - checkout given Eddy branch instead of master"
    echo "    --build-qt                       - build Qt5 libraries from source"
    echo "    --build-pyqt5                    - build PyQt5 libraries from source"
    echo "    --build-python                   - build Python interpreter from source"
    echo "    --help                           - display this message and exit"
    echo "    --keep-temp                      - keep temporary generated files"
    echo "    --skip-dependencies              - skip installing build dependencies"
    echo "    --skip-jre-download              - skip downloading a copy of the Java Runtime Environment"
    echo "    --with-build-dir=<build-dir>     - use the given directory as the build directory"
    echo "    --with-pyenv=<pyenv-exec>        - use the specified pyenv executable"
    echo "    --with-pyenv-dir=<pyenv-dir>     - the directory to install pyenv to"
    echo "    --with-python=<python-exec>      - use the given Python interpreter instead of building one"
    echo "    --with-python-version=<version>  - use the given Python version (implies --build-python)"
    echo "    --with-qmake=<qmake-exec>        - use the given qmake executable"
    echo "    --with-qt-version=<version>      - use the given Qt5 version (implies --build-qt)"
    echo "    --with-qt-prefix=<qt-prefix-dir> - directory to install Qt5 libraries (implies --build-qt)"
    echo "    --with-pyqt5-version=<version>   - use the given PyQt5 version (implies --build-pyqt5)"
    echo "    --with-sip-version=<version>     - use the given SIP version (implies --build-pyqt5)"
    echo "    --with-venv-dir=<venv-dir>       - directory to install the virtualenv to"
    exit 1
}

heading() {
    echo
    echo "############################################################"
    printf "# %-56.56s #\n" "$@"
    echo "############################################################"
    echo
}

abspath() {
    abspath=$1
    case "`uname -s`" in
        Linux) abspath="`readlink -f $1`";;
        Darwin) abspath="`perl -MCwd -e 'print Cwd::realpath($ARGV[0])' $1`";;
        *) abspath="$1";;
    esac
    echo "$abspath"
}

download_resource() {
    if [ -x "`which wget`" ]; then
        wget "$@"
        return $?
    elif [ -x "`which curl`" ]; then
        curl --location -O "$@"
        return $?
    else
       echo "Unable to download resource, no wget or curl executable found in PATH"
       return 1
    fi
}

install_dependencies() {
    case "$1" in
    Linux) # Distro specific dependencies
        # Extract distribution name from systemd configuration
        #local distro="$(cat /etc/os-release | gawk 'match($0, /^NAME=(.+?)$/, capt) { print capt[1] }')"
        echo "Installing compile requirements (requires administrator privileges)"
        if [ -x "`which apt-get`" ]; then ## Assuming a Debian-based distro
            sudo apt-get update
            sudo apt-get install -y build-essential libgl1-mesa-dev libx11-dev libxext-dev libxfixes-dev libxi-dev \
                                    libxrender-dev libxcb1-dev libx11-xcb-dev libxcb-glx0-dev libfontconfig1-dev \
                                    libpcre2-dev libfreetype6-dev libglu1-mesa-dev libssl-dev libcups2-dev libbz2-dev \
                                    zlib1g-dev libsqlite3-dev libreadline-dev openjdk-8-jdk wget git
        elif [ -x "`which yum`" ]; then ## Assuming RH-based distro
            sudo yum install -y gcc gcc-c++ libxcb libxcb-devel xcb-util xcb-util-devel xcb-util-*-devel \
                                libX11-devel libXrender-devel mesa-libGL-devel libXi-devel fontconfig-devel \
                                openssl-devel bzip2-devel cups-devel pcre2-devel freetype-devel readline-devel \
                                zlib-devel sqlite-devel java-8-openjdk perl-version git wget
        else
            echo "Unsupported distro, please install requirements manually"
            echo "then re-run the script with the --skip-dependecies option."
            echo "See https://wiki.qt.io/Building_Qt_5_from_Git for a complete list"
            echo "of compile-time dependencies"
            exit 1
        fi
        ;;
    Darwin)
        ## Check that command line tools are installed
        ## They are required at least to compile pyjnius extension
        if ! xcode-select -p >/dev/null 2>&1; then
            echo "Xcode Command Line Tools are required to compile dependencies"
            while true; do
                read -p "Do you want to install them (requires administrator privileges)?" yn
                case $yn in
                [Yy]*)
                    echo "Requesting install..."
                    xcode-select --install
                    break;;
                [Nn]*)
                    echo "Could not identify command line tools location, exiting..."
                    exit 1
                    ;;
                * ) echo "Please answer yes or no.";;
                esac
            done
        fi
        echo "Using developer tools from $(xcode-select -p)"

        ## Check that Homebrew is available to install additional dependencies
        #if [ ! -x "`which wget`" ]; then
        #    if [ ! -x "`which brew`" ]; then
        #        echo "Unable to locate Homebrew installation..."
        #        echo "Homebrew is required to install additional dependencies on macOS"
        #        echo "For instructions on how to install Homebrew see https://brew.sh"
        #        exit 1
        #    else
        #        echo "Using Homebrew from $(brew --prefix)"
        #        # Install wget as it is required to fetch dependencies
        #        brew install wget
        #    fi
        #fi

        ## Check that a JDK 1.8 is installed as it is required to compile pyjnius extension
        if /usr/libexec/java_home -v 1.8 >/dev/null 2>&1; then
            echo "Using JDK from `/usr/libexec/java_home -v 1.8`"
        else
            echo "Unable to locate a suitable Java Development Kit (JDK)"
            echo "In order to complete the configuration please download"
            echo "and install a JDK 8 from:"
            echo "http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html"
            exit 1
        fi
        ;;
    *)
        echo "Unable to install compile dependencies for platform $1"
        exit 1
        ;;
    esac
}

#################################################
## Start of build configuration script
#################################################

## Parse command line arguments
PARAMS=""
while (( "$#" )); do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case "$PARAM" in
    # Python options
    --build-python)
        BUILD_PYTHON=1
        ;;
    --with-python)
        BUILD_PYTHON=0
        PYTHON_EXEC="$VALUE"
        ;;
    --with-python-version)
        BUILD_PYTHON=1
        PYTHON_VERSION="$VALUE"
        ;;
    --with-venv-dir)
        VIRTUALENV_DIR="`abspath $VALUE`"
        ;;
    --with-pyenv)
        PYENV_EXEC="$VALUE"
        ;;
    --with-pyenv-dir)
        PYENV_ROOT="$VALUE"
        ;;
    # Qt options
    --build-qt)
        BUILD_QT=1
        ;;
    --with-qt-version)
        BUILD_QT=1
        echo $VALUE
        QT_VERSION="$VALUE"
        ;;
    --with-qt-prefix)
        BUILD_QT=1
        QT_PREFIX="$VALUE"
        ;;
    # PyQt5 options
    --build-pyqt5)
        BUILD_PYQT5=1
        ;;
    --with-qmake)
        QMAKE_EXEC="$VALUE"
        ;;
    --with-sip-version)
        BUILD_PYQT5=1
        SIP_VERSION="$VALUE"
        ;;
    --with-pyqt5-version)
        BUILD_PYQT5=1
        PYQT_VERSION="$VALUE"
        ;;
    # Global options
    --with-build-dir)
        BUILD_DIR="`abspath $VALUE`"
        ;;
    --branch)
        BRANCH="$VALUE"
        ;;
    --skip-dependencies)
        SKIP_DEPENDENCIES=1
        ;;
    --skip-jre-download)
        SKIP_JRE_DOWNLOAD=1
        ;;
    --keep-temp)
        KEEP_TEMP=1
        ;;
    --help)
        usage
        exit 0
        ;;
    --) # end argument parsing
        break
        ;;
    -*|--*=) # unsupported options
        echo "Error: Unsupported option $1" 2>&1
        usage
        exit 1
        ;;
    *) # preserve positional arguments
        PARAMS="$PARAMS $PARAM"
        ;;
    esac
    shift
done
eval set -- "$PARAMS"

############################################################
## Configuration parameters
############################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH="`uname -m`"
PLATFORM="`uname -s`"

# Force PyQt5 compilation as a binary wheel is not available for i686 linux platforms
if [ "$PLATFORM" = "Linux" -a "$ARCH" = "i686" -a "$PYTHON_EXEC" = "" ]; then
    echo "WARNING: Forcing PyQt5 compilation for architecture $ARCH"
    BUILD_QT=1
    BUILD_PYQT5=1
fi

BRANCH="${BRANCH:-master}"
BUILD_DIR="${BUILD_DIR:-"$(abspath `mktemp -d ${PWD}/eddy-build.XXXX`)"}"
BUILD_PYTHON="${BUILD_PYTHON:-1}"
BUILD_QT="${BUILD_QT:-0}"
BUILD_PYQT5="${BUILD_PYQT5:-0}"
PYTHON_VERSION="${PYTHON_VERSION:-3.6.8}"
QT_VERSION="${QT_VERSION:-5.10}"
SIP_VERSION="${SIP_VERSION:-4.19.8}"
PYQT_VERSION="${PYQT_VERSION:-5.10.1}"
PYENV_ROOT="${PYENV_ROOT:-"${HOME}/.pyenv"}"
VIRTUALENV_DIR="${VIRTUALENV_DIR:-$HOME/.virtualenvs/eddy-venv-py36}"
QT_PREFIX="${QT_PREFIX:-"$VIRTUALENV_DIR"}"
PYTHON_EXEC="${PYTHON_EXEC:-"${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python"}"
PYENV_EXEC="${PYENV_EXEC:-"${PYENV_ROOT}/bin/pyenv"}"
QMAKE_EXEC="${QMAKE_EXEC:-"${QT_PREFIX}/bin/qmake"}"
SKIP_DEPENDENCIES="${SKIP_DEPENDENCIES:-0}"
SKIP_JRE_DOWNLOAD="${SKIP_JRE_DOWNLOAD:-0}"
KEEP_TEMP="${KEEP_TEMP:-0}"
NPROC=$([ -x /usr/bin/nproc ] && nproc || sysctl -n hw.ncpu)

## JVM Configuration
case "${ARCH}" in
    i686) JRE_ARCH="i586";;
    x86_64) JRE_ARCH="x64";;
    *) echo "Unsupported architecture $ARCH"; exit 1;;
esac

case "$PLATFORM" in
    Linux) JRE_PLATFORM="linux";;
    Darwin) JRE_PLATFORM="macosx";;
    *) echo "Unsupported platform: $PLATFORM"; exit 1;;
esac

############################################################
## Configuration summary
############################################################
heading "Build configuration"
echo "BUILD_DIR      = $BUILD_DIR"
echo "BUILD_PYTHON   = $BUILD_PYTHON"
echo "BUILD_QT       = $BUILD_QT"
echo "BUILD_PYQT5    = $BUILD_PYQT5"
echo "QT_PREFIX      = $QT_PREFIX"
echo "QT_VERSION     = $QT_VERSION"
echo "QMAKE_EXEC     = $QMAKE_EXEC"
echo "SIP_VERSION    = $SIP_VERSION"
echo "PYQT_VERSION   = $PYQT_VERSION"
echo "PYENV_ROOT     = $PYENV_ROOT"
echo "PYENV_EXEC     = $PYENV_EXEC"
echo "PYTHON_VERSION = $PYTHON_VERSION"
echo "PYTHON_EXEC    = $PYTHON_EXEC"
echo "VIRTUALENV_DIR = $VIRTUALENV_DIR"
echo "BRANCH         = $BRANCH"
echo "ARCH           = $ARCH"
echo "PLATFORM       = $PLATFORM"
echo "JRE_ARCH       = $JRE_ARCH"
echo "JRE_PLATFORM   = $JRE_PLATFORM"

############################################################
## Create build directory if it doesn't exist
############################################################
mkdir -p "${BUILD_DIR}"

############################################################
## Install dependencies
############################################################
if [ "$SKIP_DEPENDENCIES" != "1" ]; then
    install_dependencies "$PLATFORM"
fi

############################################################
## Install pyenv
############################################################
if [ "$BUILD_PYTHON" = "1" ]; then
    heading "Installing pyenv..."
    if [ ! -x "${PYENV_EXEC}" ]; then
        git clone https://github.com/pyenv/pyenv.git "${PYENV_ROOT}"
    fi

    ## INSTALL PYTHON FROM PYENV
    heading "Installing Python ${PYTHON_VERSION}..."
    PYENV_ROOT="$PYENV_ROOT" "${PYENV_EXEC}" install --skip-existing "${PYTHON_VERSION}"
fi

############################################################
## Create the virtualenv
############################################################
"${PYTHON_EXEC}" -m venv --copies "${VIRTUALENV_DIR}"
source "${VIRTUALENV_DIR}/bin/activate"

############################################################
## Build and install Qt5 (if requested)
############################################################
if [ "$BUILD_QT" = "1" ]; then
    heading "Installing Qt5 libraries (this may require a long time)..."
    cd "${BUILD_DIR}"
    git clone git://code.qt.io/qt/qt5.git
    cd "${BUILD_DIR}/qt5"
    git checkout "${QT_VERSION}"
    ./init-repository --module-subset=default,-qtwebkit,-qtwebkit-examples,-qtwebengine
    ./configure -prefix "${QT_PREFIX}" -opensource -nomake examples -nomake tests -release -confirm-license
    make -j "$NPROC"
    make install
fi

if [ "$BUILD_PYQT5" = "1" ]; then
    heading "Compiling PyQt5 libraries..."
    ## INSTALL SIP
    cd "${BUILD_DIR}"
    download_resource "http://downloads.sourceforge.net/project/pyqt/sip/sip-${SIP_VERSION}/sip-${SIP_VERSION}.tar.gz"
    tar xf "sip-${SIP_VERSION}.tar.gz"
    cd "sip-${SIP_VERSION}"
    python configure.py
    make -j "$NPROC"
    make install

    ## INSTALL PYQT
    cd "${BUILD_DIR}"
    download_resource "http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-${PYQT_VERSION}/PyQt5_gpl-${PYQT_VERSION}.tar.gz"
    tar xf "PyQt5_gpl-${PYQT_VERSION}.tar.gz"
    cd "PyQt5_gpl-${PYQT_VERSION}"
    python configure.py --qmake "${QMAKE_EXEC}" --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
    make -j "$NPROC"
    make install
fi

############################################################
## Install Python dependencies (from PYPI)
############################################################
heading "Installing Eddy dependencies..."
cd "${SCRIPT_DIR}/.."
pip install -r requirements/cython.in
if [ "$BUILD_PYQT5" = "0" ]; then
    pip install -r requirements/pyqt5.in
fi
pip install -r requirements/packaging.in
pip install -r requirements/tests.in

############################################################
## Bundle Java Runtime Environment
############################################################
if [ "$SKIP_JRE_DOWNLOAD" != "1" ]; then
    heading "Bundling Java Runtime Environment..."
    cd "${BUILD_DIR}"
    download_resource --header "Cookie: oraclelicense=accept-securebackup-cookie" \
         http://download.oracle.com/otn-pub/java/jdk/8u181-b13/96a7b8442fe848ef90c96a2fad6ed6d1/jre-8u181-"${JRE_PLATFORM}"-"${JRE_ARCH}".tar.gz
    tar xf jre-8u181-"${JRE_PLATFORM}"-"${JRE_ARCH}".tar.gz*
    mkdir -p "${BUILD_DIR}/eddy/resources/java"

    if [ "$PLATFORM" = "Linux" ]; then
        rm -rf jre1.8.0_181/plugin
        mv jre1.8.0_181 "${BUILD_DIR}/eddy/resources/java/jre"
    elif [ "$PLATFORM" = "Darwin" ]; then
        mv jre1.8.0_181.jre/Contents/Home "${BUILD_DIR}/eddy/resources/java/jre"
    fi
fi

############################################################
## Cleanup
############################################################
if [ "$KEEP_TEMP" != "1" ]; then
    heading "Cleaning up build directory..."
    cd "${BUILD_DIR}"
    rm -rf sip-*
    rm -rf PyQt5_gpl*
    rm -rf jre*
    rm -rf qt5*
fi

############################################################
## Setup completed
############################################################
echo
echo "Setup completed. You can activate the virtualenv with:"
echo "source ${VIRTUALENV_DIR}/bin/activate"

exit 0
