#!/usr/bin/env python3
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


import sys
import traceback

from argparse import ArgumentParser

from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy, QMessageBox

from eddy import images_rc ## DO NOT REMOVE
from eddy import Eddy
from eddy.widgets.misc import SplashScreen


# main application reference
app = None


def base_except_hook(exc_type, exc_value, exc_traceback):
    """
    Used to handle all uncaught exceptions.
    :param exc_type: the type of the exception.
    :param exc_value: the exception value.
    :param exc_traceback: the exception traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        global app
        app.quit()
    else:
        box = QMessageBox()
        box.setIconPixmap(QPixmap(':/icons/error'))
        box.setWindowIcon(QIcon(':/images/eddy'))
        box.setWindowTitle('Unhandled exception!')
        box.setText('This is embarrassing :(<br /><br />'
                    'A critical error has just occurred. '
                    'Eddy will continue to work, however a reboot is highly recommended.')
        box.setInformativeText('Please <a href="https://github.com/danielepantaleone/eddy/issues">submit '
                               'a bug report</a> with detailed information')
        box.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        box.setStandardButtons(QMessageBox.Ok)
        L = box.layout()
        L.addItem(QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), L.rowCount(), 0, 1, L.columnCount())
        box.exec_()


def main():
    """
    Application entry point.
    """
    parser = ArgumentParser(description='parse Eddy\'s command line options')
    parser.add_argument('--nosplash', dest='nosplash', action='store_true')

    (options, args) = parser.parse_known_args()

    def init(application):
        """
        Initialize the application using the splash screen.
        :param application: the application to initialize.
        :return: the initialized main window instance.
        :rtype: MainWindow
        """
        with SplashScreen(min_splash_time=4):
            mainwindow = application.init()
        return mainwindow

    def init_no_splash(application):
        """
        Initialize the application WITHOUT using the splash screen.
        :param application: the application to initialize.
        :return: the initialized main window instance.
        :rtype: MainWindow
        """
        return application.init()

    global app
    sys.excepthook = base_except_hook
    app = Eddy(sys.argv)
    window = init_no_splash(app) if options.nosplash or sys.platform.startswith('linux') else init(app)
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()