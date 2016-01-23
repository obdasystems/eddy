# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


__appname__ = 'Eddy'
__author__ = 'Daniele Pantaleone'
__copyright__ = 'Copyright © 2015 Daniele Pantaleone'
__email__ = 'danielepantaleone@me.com'
__license__ = 'GPL'
__organization__ = 'Sapienza - University Of Rome'
__status__ = 'Development'
__version__ = '0.6'


# Define some extra constants
BUG_TRACKER = 'https://github.com/danielepantaleone/eddy/issues'
PROJECT_HOME = 'https://github.com/danielepantaleone/eddy'
GRAPHOL_HOME = 'http://www.dis.uniroma1.it/~graphol/'


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from verlib import NormalizedVersion

from eddy.core.exceptions import JVMNotSupportedException
from eddy.core.functions.fsystem import expandPath
from eddy.core.functions.misc import QSS
from eddy.core.functions.signals import connect
from eddy.core.utils.java import JVM
from eddy.ui.mainwindow import MainWindow
from eddy.ui.styles import Style


class Eddy(QApplication):
    """
    This class implements the main Qt application.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize Eddy.
        """
        super().__init__(*args, **kwargs)
        self.jvm = None
        self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)

    def init(self):
        """
        Run initialization tasks for Eddy.
        :raise JVMNotFoundException: if the JVM could not be found on the system.
        :raise JVMNotSupportedException: if the JVM found in the system is not supported.
        :rtype: MainWindow
        """
        # SETUP LAYOUT

        style = Style.forName(self.settings.value('appearance/style', 'light', str))

        self.setStyle(style)
        self.setStyleSheet(style.qss())

        # INITIALIZE RECENT DOCUMENTS

        if not self.settings.contains('document/recent_documents'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
            # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
            # container. So according to this we can't use an empty list as default value because PyQt5 needs
            # to know the type of the contents added to the collection: we avoid this problem by placing
            # the list of examples file in the recentDocumentList (only if there is no list defined already).
            self.settings.setValue('document/recent_documents', [
                expandPath('@examples/Animals.graphol'),
                expandPath('@examples/Family.graphol'),
                expandPath('@examples/Pizza.graphol'),
            ])

        # STARTUP THE JAVA VIRTUAL MACHINE

        self.jvm = JVM()
        self.jvm.startup()

        # Check for correct JVM version.
        if self.jvm.version < NormalizedVersion('1.8.0'):
            raise JVMNotSupportedException('JVM v{} is not supported'.format(str(self.jvm.version)))

        connect(self.aboutToQuit, self.jvm.shutdown)

        # CREATE THE MAIN WINDOW

        return MainWindow()