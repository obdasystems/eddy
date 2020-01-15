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

set -e # Stop on any error

if [[ ! -z "$TOXENV" ]]; then
    # Additional test arguments
    args=()

    # No Xvfb on macOS
    [[ $TRAVIS_OS_NAME == osx ]] && args+=('--no-xvfb')

    # Run tests with tox
    tox -- "${args[@]}"
else
    # Make sure that JAVA_HOME is set
    if [[ -z "$JAVA_HOME" ]]; then
        echo "JAVA_HOME is not set"
        exit 1
    fi

    # Copy the jre into the application folder
    mkdir -p resources/java
    cp -R "$JAVA_HOME/jre" resources/java/jre
    # Remove unneeded files from the jre
    ./scripts/prepare_jre.sh

    # Additional test arguments
    args=()

    # No Xvfb on macOS
    [[ $TRAVIS_OS_NAME == osx ]] && args+=('--no-xvfb')

    # Run tests with coverage
    python -bb -m pytest --cov=eddy --cov-report=term-missing --cov-config=.coveragerc "${args[@]}"

    # Try to build a distribution package
    args=()
    [[ "$TRAVIS_OS_NAME" == "linux" ]] && args+=('standalone' '--format=gztar')
    [[ "$TRAVIS_OS_NAME" == "osx" ]] && args+=('createdmg')
    python setup.py "${args[@]}"
fi


