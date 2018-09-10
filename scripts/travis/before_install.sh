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

# Terminate in case of errors
set -e

# Set Python version to use as an environment variable
PYTHON_VERSION=${PYTHON_VERSION:-"3.5.4"}
VENV_DIR="${VENV_DIR:-$HOME/eddy-venv}"

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
    # Update Homebrew first
    brew update

    # Recommended for installing Python from Homebrew
    brew outdated openssl || brew upgrade openssl
    brew outdated readline || brew upgrade readline

    # See https://docs.travis-ci.com/user/osx-ci-environment/#A-note-on-upgrading-packages.
    brew outdated pyenv || brew upgrade pyenv

    # Install Python
    pyenv install $PYTHON_VERSION

    # Manually set environment variables
    export PYENV_VERSION=$PYTHON_VERSION
    export PATH="$HOME/.pyenv/shims:${PATH}"

    # Create virtual environment
    pyenv exec python -m venv --copies "$VENV_DIR"

    # Install Oracle JDK 8 as latest Travis images seem to be switching to JDK 10
    brew outdated caskroom/cask/brew-cask || brew upgrade caskroom/cask/brew-cask

    # We must be able to get older Java versions than the latest.
    brew tap caskroom/versions
    sudo rm -rf /Library/Java/JavaVirtualMachines
    brew cask install caskroom/versions/java8

    # Fail unless we installed JDK 8 correctly.
    /usr/libexec/java_home --failfast --version 1.8
fi
