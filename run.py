#!/usr/bin/env python3
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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import sys

from argparse import ArgumentParser

from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMessageBox, QApplication

from eddy import APPNAME, BUG_TRACKER
from eddy.core.application import Eddy
from eddy.core.functions.misc import format_exception
from eddy.core.functions.signals import connect

from eddy.lang import gettext as _

# noinspection PyUnresolvedReferences
from eddy.ui import images_rc


app = None
msgbox = None


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
            msgbox = QMessageBox()
            msgbox.setIconPixmap(QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Fatal error!')
            msgbox.setText(_('EXCEPT_HOOK_MESSAGE', APPNAME))
            msgbox.setInformativeText(_('EXCEPT_HOOK_INFORMATIVE_MESSAGE', BUG_TRACKER))
            msgbox.setDetailedText(format_exception(exc_value))
            msgbox.setStandardButtons(QMessageBox.Close|QMessageBox.Ok)
            buttonOk = msgbox.button(QMessageBox.Ok)
            buttonOk.setText(_('EXCEPT_HOOK_BTN_CLOSE'))
            buttonQuit = msgbox.button(QMessageBox.Close)
            buttonQuit.setText(_('EXCEPT_HOOK_BTN_QUIT', APPNAME))
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
    if app.running:
        app.routePacket(sys.argv)
        sys.exit(0)

    app.configure(options)
    app.start(options)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()