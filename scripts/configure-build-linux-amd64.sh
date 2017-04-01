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
QT_HOME="~/Qt/5.7/gcc_64"
VIRTUALENV="~/python34"

## INSTALL DEPENDENCIES
sudo apt-get install -y build-essential libgl1-mesa-dev libx11-dev libxext-dev libxfixes-dev libxi-dev
sudo apt-get install -y libxrender-dev libxcb1-dev libx11-xcb-dev libxcb-glx0-dev libfontconfig1-dev
sudo apt-get install -y libfreetype6-dev libglu1-mesa-dev libssl-dev libcups2-dev python3-pip git mercurial
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
sudo apt-get install -y oracle-java8-installer oracle-java8-set-default
## INSTALL PYTHON
cd ${DOWNLOADS}
wget https://www.python.org/ftp/python/3.4.4/Python-3.4.4.tar.xz
tar xf Python-3.4.4.tar.xz
cd Python-3.4.4
./configure
sudo make altinstall
## CREATE THE VIRTUALENV
sudo pip3 install virtualenv
virtualenv -p /usr/local/bin/python3.4 ${VIRTUALENV}
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
pip install --pre github3.py
## INSTALL PYTHON DEPENDENCIES (FROM MERCURIAL AND GIT)
cd ${DOWNLOADS}
pip install -e hg+https://danielepantaleone@bitbucket.org/danielepantaleone/cx_freeze/@ubuntu#egg=cx_Freeze
pip install -e git+https://github.com/danielepantaleone/pyjnius.git@i386#egg=pyjnius --exists-action i
## CLONE EDDY
cd ${DOWNLOADS}
rm -rf "${DOWNLOADS}/eddy"
git clone https://github.com/danielepantaleone/eddy.git
mkdir "${DOWNLOADS}/eddy/resources/java"
## ADD JRE 1.8
wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u102-b14/jdk-8u102-linux-x64.tar.gz
tar xf jdk-8u102-linux-x64.tar.gz
rm -rf jdk1.8.0_102/jre/plugin
mv jdk1.8.0_102/jre/ "${DOWNLOADS}/eddy/resources/java"
mv jdk1.8.0_102/COPYRIGHT "${DOWNLOADS}/eddy/resources/java"
mv jdk1.8.0_102/LICENSE "${DOWNLOADS}/eddy/resources/java"
## CLEANUP
cd ${DOWNLOADS}
sudo rm -rf sip-4.18.1*
sudo rm -rf PyQt5_gpl-5.7*
sudo rm -rf jdk*
sudo rm -rf qt5*