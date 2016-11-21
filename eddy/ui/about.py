# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


import sys

from PyQt5 import QtCore

from eddy.ui.splash import Splash


_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')


class AboutDialog(Splash):
    """
    This class is used to display the 'About' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the dialog.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setSpaceX(8 if _MACOS else 0)
        self.setSpaceY(12 if _MACOS else 0)
        self.setWindowFlags(QtCore.Qt.Popup)

    def exec_(self):
        """
        Alias AboutDialog.show() so that the screen can be shown using Session.doOpenDialog.
        """
        self.show()