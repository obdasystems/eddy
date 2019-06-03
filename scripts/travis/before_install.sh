#!/bin/bash
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


# Set Python version to use as an environment variable
PYTHON_VERSION=${PYTHON_VERSION:-"3.6.8"}
VENV_DIR="${VENV_DIR:-$HOME/eddy-venv}"

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
    # Xenial on Travis defaults to openjdk11 even tough openjdk8 is specified
    # as the build jdk since we are not doing a Java build.
    # We force the install of openjdk-8-jdk via the Travis apt addon and
    # then we set here the value of JAVA_HOME to point to the openjdk8 location.
    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
    # Also export JDK_HOME before building pyjnius which will otherwise not pick the JAVA_HOME
    export JDK_HOME="$JAVA_HOME"
fi

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
    # Use Travis Homebrew Addons to perform a `brew update`
    # See: https://docs.travis-ci.com/user/installing-dependencies/#installing-packages-on-macos

    # Install Python
    env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install --skip-existing $PYTHON_VERSION

    # Manually set environment variables
    export PYENV_VERSION=$PYTHON_VERSION
    export PATH="$HOME/.pyenv/shims:${PATH}"

    # Create virtual environment
    pyenv exec python -m venv --copies "$VENV_DIR"

    # Homebrew's java8 cask no longer exists since Java 8 is no longer
    # freely available from Oracle. The recommended solution is to use
    # adoptopenjdk8 builds now.
    # See: https://github.com/Homebrew/homebrew-cask-versions/issues/7253

    # Fail unless we installed JDK 8 correctly.
    export JAVA_HOME="`/usr/libexec/java_home --failfast --version 1.8`"
    # set JDK_HOME for pyjnius
    export JDK_HOME="$JAVA_HOME"

    # Activate virtualenv
    source "$VENV_DIR/bin/activate"
fi
