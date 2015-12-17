# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout

from eddy import __version__, __appname__, __copyright__, __email__, __license__


class AboutDialog(QDialog):
    """
    This class is used to display the 'About' dialog.
    """

    def __init__(self, parent=None):
        """
        Initialize the form dialog.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        message = """
            {TITLE}<br/>
            <a href="mailto:{EMAIL}" {STYLE2}>{COPYRIGHT}</a><br/>
            <br/>
            Version: {VERSION}<br/>
            License: {LICENSE}<br/>
            <br />
            <a href="http://www.dis.uniroma1.it/~graphol/" {STYLE1}>Graphol</a> is developed by members of
            the DASI-lab group of the <a href="http://www.diag.uniroma1.it/en" {STYLE1}> Dipartimento di
            Ingegneria Informatica, Automatica e Gestionale "A.Ruberti"</a> at <a href="http://en.uniroma1.it/"
            {STYLE1}>Sapienza</a> University of Rome:<br/>
            <br/>
            <a href="mailto:lembo@dis.uniroma1.it" {STYLE2}>Domenico Lembo</a><br/>
            <a href="mailto:santarelli@dis.uniroma1.it" {STYLE2}>Valerio Santarelli</a><br/>
            <a href="mailto:savo@dis.uniroma1.it" {STYLE2}>Domenico Fabio Savo</a><br/>
            <a href="mailto:console@dis.uniroma1.it" {STYLE2}>Marco Console</a>
            """.format(TITLE=__appname__, EMAIL=__email__, VERSION=__version__,
                       LICENSE=__license__, COPYRIGHT=__copyright__, STYLE1='style="text-decoration:none;"',
                       STYLE2='style="text-decoration:none; color: #000000;"')

        self.icon = QLabel(self)
        self.icon.setPixmap(QPixmap(':/images/eddy'))

        self.text = QLabel(message, self)
        self.text.setWordWrap(True)
        self.text.setOpenExternalLinks(True)
        self.text.setAlignment(Qt.AlignHCenter)
        self.text.setFixedWidth(340)

        topLayout = QHBoxLayout()
        topLayout.addWidget(self.icon)
        topLayout.setAlignment(Qt.AlignTop)
        topLayout.setContentsMargins(105, 20, 0, 0)

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.text)
        bottomLayout.setAlignment(Qt.AlignTop)
        bottomLayout.setContentsMargins(0, 20, 0, 20)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addLayout(topLayout)
        self.mainLayout.addLayout(bottomLayout)

        self.setFixedWidth(360)
        self.setFixedHeight(self.sizeHint().height())
        self.setModal(True)
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle('About {}'.format(__appname__))