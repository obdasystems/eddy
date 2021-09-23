# -*- coding: utf-8 -*-

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


import platform
import textwrap

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy import COPYRIGHT
from eddy.core.functions.signals import connect


class AboutDialog(QtWidgets.QDialog):
    """
    This class is used to display the 'About' dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the dialog.
        """
        super().__init__(parent)
        self.iconLabel = QtWidgets.QLabel(self)
        self.iconLabel.setContentsMargins(20, 0, 40, 0)
        self.iconLabel.setPixmap(QtGui.QPixmap(':/images/eddy-smile'))
        self.infoLabel = QtWidgets.QLabel(self)
        self.infoLabel.setText(textwrap.dedent("""
        <h3>{} {}</h3>
        An editor for the specification and visualization<br/>
        of Graphol ontologies.<br/><br/>
        Runtime: {} {}<br/>
        PyQt: {}<br/>
        Qt: {}<br/><br/>
        {}<br/><br/>
        Licensed under the GNU General Public License v3<br/>""".format(
            QtWidgets.qApp.applicationDisplayName(),
            QtWidgets.qApp.applicationVersion(),
            platform.python_implementation(),
            platform.python_version(),
            QtCore.PYQT_VERSION_STR,
            QtCore.QT_VERSION_STR,
            COPYRIGHT,
        )))
        self.confirmation = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok, self)
        connect(self.confirmation.accepted, self.accept)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.iconLabel, 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.infoLabel)
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout(layout)
        mainLayout.addWidget(self.confirmation)
        self.setWindowTitle('About {}'.format(QtWidgets.qApp.applicationDisplayName()))
