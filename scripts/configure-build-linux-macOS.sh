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


## CONFIGURATION
DOWNLOADS="~/Downloads"
JAVA_HOME="$(/usr/libexec/java_home -v 1.8)"
QT_HOME="~/Qt/5.7/clang_64"
VIRTUALENV="~/python34"

## CREATE THE VIRTUALENV
cd /usr/local/bin/
pyvenv-3.4 ${VIRTUALENV}
source "${VIRTUALENV}/bin/activate"
## BUILD AND INSTALL QT5
cd ${DOWNLOADS}
git clone git://code.qt.io/qt/qt5.git
cd "${DOWNLOADS}/qt5"
git checkout 5.7
./init-repository --module-subset=default,-qtwebkit,-qtwebkit-examples,-qtwebengine
./configure -prefix "${QT_HOME}" -opensource -nomake examples -nomake tests -release -confirm-license
make -j 5
make install
## INSTALL SIP
cd ${DOWNLOADS}
wget http://downloads.sourceforge.net/project/pyqt/sip/sip-4.18.1/sip-4.18.1.tar.gz
tar xf sip-4.18.1.tar.gz
cd sip-4.18.1
python configure.py
make
sudo make install
## INSTALL PYQT
cd ${DOWNLOADS}
wget http://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.7/PyQt5_gpl-5.7.tar.gz
tar xf PyQt5_gpl-5.7.tar.gz
cd PyQt5_gpl-5.7
python configure.py --qmake "${QT_HOME}/bin/qmake" --disable QtPositioning --no-qsci-api --no-designer-plugin --no-qml-plugin --confirm-license
make -j 5
sudo make install
## SOFTLINK QT5 LIB INSIDE PYTHON VIRTUAL ENVIRONMENT
cd "${VIRTUALENV}/lib"
ln -s "${QT_HOME}/lib/*" .
## INSTALL PYTHON DEPENDENCIES (FROM PYPI)
cd ${DOWNLOADS}
pip install -U pip
pip install -U cython
pip install -U verlib
pip install -U mockito-without-hardcoded-distribute-version
pip install -U mock
pip install -U nose
pip install -U nose-cov
pip install -U natsort
pip install -U coveralls
pip install -U pyyaml
pip install -U Pillow
pip install -U cx_Freeze
pip install --pre github3.py
## INSTALL PYTHON DEPENDENCIES (FROM GIT)
cd ${DOWNLOADS}
pip install -e git+https://github.com/danielepantaleone/pyjnius.git@i386#egg=pyjnius --exists-action i
## CLONE EDDY
cd ${DOWNLOADS}
rm -rf "${DOWNLOADS}/eddy"
git clone https://github.com/danielepantaleone/eddy.git
cd eddy
git submodule update --init --recursive
mkdir "${DOWNLOADS}/eddy/resources/java"
## ADD JRE 1.8
cp -R "${JAVA_HOME}/jre/" "${DOWNLOADS}/eddy/resources/java"
## CLEANUP
cd ${DOWNLOADS}
sudo rm -rf sip-4.18.1*
sudo rm -rf PyQt5_gpl-5.7*
sudo rm -rf qt5*