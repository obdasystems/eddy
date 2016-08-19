#!/usr/bin/env python3
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


import os
import sys
import jnius_config

from eddy.core.datatypes.system import Platform
from eddy.core.functions.path import expandPath


#############################################
# BEGIN JAVA VIRTUAL MACHINE SETUP
#################################

if os.path.isdir(expandPath('@resources/java/')):
    os.environ['JAVA_HOME'] = expandPath('@resources/java/')

if Platform.identify() is Platform.Windows:
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

#############################################
# END JAVA VIRTUAL MACHINE SETUP
#################################


from argparse import ArgumentParser

from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QT_VERSION_STR
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMessageBox, QApplication

from sip import SIP_VERSION_STR

from eddy import APPNAME, COPYRIGHT, VERSION, BUG_TRACKER
from eddy.core.application import Eddy
from eddy.core.functions.misc import format_exception
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

# noinspection PyUnresolvedReferences
from eddy.ui import images_rc


app = None
msgbox = None


LOGGER = getLogger(__name__)


def base_except_hook(exc_type, exc_value, exc_traceback):
    """
    Used to handle all uncaught exceptions.
    :type exc_type: class
    :type exc_value: Exception
    :type exc_traceback: Traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        app.quit()
    else:
        global msgbox
        if not msgbox:
            LOGGER.critical(format_exception(exc_value))
            msgbox = QMessageBox()
            msgbox.setIconPixmap(QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Fatal error!')
            msgbox.setText('This is embarrassing ...\n\n' \
            'A critical error has just occurred. {0} will continue to work, ' \
            'however a reboot is highly recommended.'.format(APPNAME))
            msgbox.setInformativeText('If the problem persists you can '
            '<a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setDetailedText(format_exception(exc_value))
            msgbox.setStandardButtons(QMessageBox.Close | QMessageBox.Ok)
            buttonOk = msgbox.button(QMessageBox.Ok)
            buttonOk.setText('Close')
            buttonQuit = msgbox.button(QMessageBox.Close)
            buttonQuit.setText('Quit {0}'.format(APPNAME))
            connect(buttonOk.clicked, msgbox.close)
            connect(buttonQuit.clicked, app.quit)
            # noinspection PyArgumentList
            QApplication.beep()
            msgbox.exec_()
            msgbox = None


def main():
    """
    Application entry point.
    """
    parser = ArgumentParser()
    parser.add_argument('--nosplash', dest='nosplash', action='store_true')
    parser.add_argument('--tests', dest='tests', action='store_true')
    parser.add_argument('--open', dest='open', default=None)

    sys.excepthook = base_except_hook

    options, _ = parser.parse_known_args(args=sys.argv)

    global app
    app = Eddy(options, sys.argv)
    if app.isAlreadyRunning():
        app.routePacket(sys.argv)
        sys.exit(0)

    LOGGER.separator(separator='-')
    LOGGER.frame('%s v%s', APPNAME, VERSION, separator='|')
    LOGGER.frame(COPYRIGHT, separator='|')
    LOGGER.separator(separator='-')
    LOGGER.frame('Qt version: %s', QT_VERSION_STR, separator='|')
    LOGGER.frame('PyQt version: %s', PYQT_VERSION_STR, separator='|')
    LOGGER.frame('SIP version: %s', SIP_VERSION_STR, separator='|')
    LOGGER.separator(separator='-')

    app.configure(options)
    app.start(options)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()