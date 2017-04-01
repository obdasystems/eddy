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


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "${SCRIPT_DIR}")"
BUILDS_DIR="${PARENT_DIR}/builds"

cd ~
mkdir "${BUILDS_DIR}"

# Install Qt5
sudo apt-add-repository ppa:beineri/opt-qt571-trusty -y
sudo apt-get update
sudo apt-get install qt-latest
sudo apt-get install mercurial
source /opt/qt57/bin/qt57-env.sh

# Install OracleJDK8
#sudo add-apt-repository ppa:webupd8team/java -y
#sudo apt-get update
#sudo apt-get install oracle-java8-installer -y
#sudo apt-get install oracle-java8-set-default -y

# Install Sip
curl -L -o "${BUILDS_DIR}/sip.tar.gz" "https://downloads.sourceforge.net/project/pyqt/sip/sip-4.19.2/sip-4.19.2.tar.gz"
tar xzf "${BUILDS_DIR}/sip.tar.gz" -C "${BUILDS_DIR}" --keep-newer-files
cd "${BUILDS_DIR}/sip-4.19.2"
python configure.py
make
sudo make install

# Install PyQt5
curl -L -o "${BUILDS_DIR}/pyqt.tar.gz" "https://downloads.sourceforge.net/project/pyqt/PyQt5/PyQt-5.7.1/PyQt5_gpl-5.7.1.tar.gz?"
tar xzf "${BUILDS_DIR}/pyqt.tar.gz" -C "${BUILDS_DIR}" --keep-newer-files
cd "${BUILDS_DIR}/PyQt5_gpl-5.7.1"
python configure.py --confirm-license --no-designer-plugin -e QtCore -e QtGui -e QtWidgets -e QtPrintSupport -e QtXml -e QtTest -e QtNetwork
make
sudo make install

# Install PIP packages
pip install -U pip
pip install -U cython==0.23.4
pip install -U verlib==0.1
pip install -U mockito-without-hardcoded-distribute-version==0.5.4
pip install -U mock==2.0.0
pip install -U nose==1.3.7
pip install -U nose-cov==1.6
pip install -U natsort==5.0.1
pip install -U coveralls
pip install -e hg+https://danielepantaleone@bitbucket.org/danielepantaleone/cx_freeze/@ubuntu#egg=cx_Freeze
pip install -e git+https://github.com/danielepantaleone/pyjnius.git@i386#egg=pyjnius --exists-action i
pip install --pre github3.py

cd ~
rm -rf "${BUILDS_DIR}"
