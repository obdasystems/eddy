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


import os
import jnius_config

from PyQt5.QtCore import QSettings, QEvent
from PyQt5.QtWidgets import QApplication

from eddy.core.datatypes import Platform
from eddy.core.functions import isEmpty, expandPath


########################################################
##         BEGIN JAVA VIRTUAL MACHINE SETUP           ##
########################################################

if os.path.isdir(expandPath('@resources/java/')):
    # If we are shipping the jvm then set the JAVA_HOME.
    os.environ['JAVA_HOME'] = expandPath('@resources/java/')

if Platform.identify() is Platform.Windows:
    # On windows we must add the jvm.dll to system path.
    path = os.getenv('Path', '')
    path = path.split(os.pathsep)
    path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'bin', 'client'))
    os.environ['Path'] = os.pathsep.join(path)

classpath = []
resources = expandPath('@resources/lib/')
for name in os.listdir(resources):
    path = os.path.join(resources, name)
    if os.path.isfile(path):
        classpath.append(path)

jnius_config.add_options('-ea', '-Xmx512m')
jnius_config.set_classpath(*classpath)

########################################################
##          END JAVA VIRTUAL MACHINE SETUP            ##
########################################################


from eddy.ui.mainwindow import MainWindow
from eddy.ui.splash import SplashScreen
from eddy.ui.styles import Style


class Eddy(QApplication):
    """
    This class implements the main Qt application.
    """
    def __init__(self, argv):
        """
        Initialize Eddy.
        :type argv: list
        """
        super().__init__(argv)

        with SplashScreen(min_splash_time=2):

            # Initialize application settings.
            self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)

            # Setup layout.
            style = Style.forName(self.settings.value('appearance/style', 'light', str))
            self.setStyle(style)
            self.setStyleSheet(style.qss())

            # Initialize recent documents.
            if not self.settings.contains('document/recent_documents'):
                # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
                # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
                # container. So according to this we can't use an empty list as default value because PyQt5 needs
                # to know the type of the contents added to the collection: we avoid this problem by placing
                # the list of examples file in the recentDocumentList (only if there is no list defined already).
                self.settings.setValue('document/recent_documents', [
                    expandPath('@examples/Animals.graphol'),
                    expandPath('@examples/Diet.graphol'),
                    expandPath('@examples/Family.graphol'),
                    expandPath('@examples/Pizza.graphol'),
                ])

            # Create the main window.
            self.mainwindow = MainWindow()

        # Display the mainwindow.
        self.mainwindow.show()

        if Platform.identify() is not Platform.Darwin:
            # Perform document opening if files have been added to sys.argv. This is not
            # executed on Mac OS since this is already handled as a QFileOpenEvent instance.
            for filepath in [x for x in argv if os.path.isfile(x)]:
                self.mainwindow.openFile(filepath)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def event(self, event):
        """
        Executed when an event is received.
        :type event: T <= QEvent | QFileOpenEvent
        """
        if event.type() == QEvent.FileOpen:
            filepath = event.file()
            if not isEmpty(filepath) and os.path.isfile(filepath):
                self.mainwindow.openFile(path)
                return True

        return super().event(event)