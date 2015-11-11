#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


__author__ = 'Daniele Pantaleone'
__email__ = 'danielepantaleone@me.com'
__copyright__ = 'Copyright 2015, Daniele Pantaleone'
__organization__ = 'Sapienza - University Of Rome'
__appname__ = 'GrapholEd'
__version__ = '0.3.1'
__status__ = 'Development'
__license__ = 'GPL'


import os

from grapholed.functions import QSS, getPath, main_is_frozen
from grapholed.style import DefaultStyle
from grapholed.widgets.main import MainWindow
from grapholed.widgets.misc import SplashScreen

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication


class GrapholEd(QApplication):
    """
    This class implements the main Qt application.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize GrapholEd.
        """
        super().__init__(*args, **kwargs)
        self.mainwindow = None
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, __organization__, __appname__)

    def init(self):
        """
        Run initialization tasks for GrapholEd (i.e: initialize the Style, Settings, Main Window...).
        :return: the application MainWindow.
        :rtype: MainWindow
        """
        self.setStyle(DefaultStyle())
        self.setStyleSheet(QSS(getPath('@grapholed/stylesheets/default.qss')))

        if not self.settings.contains('document/recent_documents'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
            # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
            # container. So according to this we can't use an empty list as default value because PyQt5 needs
            # to know the type of the contents added to the collection: we avoid this problem by placing
            # the list of examples file in the recentDocumentList (only if there is no list defined already).
            root = getPath('@grapholed/')
            root = os.path.join(root, '..') if not main_is_frozen() else root
            self.settings.setValue('document/recent_documents', [
                os.path.join(root, 'examples', 'Family.graphol'),
                os.path.join(root, 'examples', 'Pizza.graphol')
            ])

        self.mainwindow = MainWindow()
        return self.mainwindow