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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import traceback

from PyQt5.QtCore import Qt, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QProgressBar, QVBoxLayout, QApplication
from PyQt5.QtWidgets import QMessageBox


from eddy.core.functions import connect


class BusyLoaderDialog(QDialog):
    """
    This class implements a loader showing a BusyProgressBar indicator.
    """
    def __init__(self, worker, parent=None):
        """
        Initialize the form dialog.
        :type worker: Loader
        :type parent: QWidget
        """
        super().__init__(parent)

        self.worker = worker
        self.workerThread = None

        self.progressBar = QProgressBar(self)
        self.progressBar.setAlignment(Qt.AlignHCenter)
        self.progressBar.setRange(-1, -1)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addWidget(self.progressBar)

        self.setWindowTitle('Loading ...')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(300, 100)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def showEvent(self, event):
        """
        Executed when the dialog is shown
        :type event: QShowEvent
        """
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)

        connect(self.worker.completed, self.completed)
        connect(self.worker.errored, self.errored)
        connect(self.workerThread.started, self.worker.work)

        self.workerThread.start()

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(Exception)
    def errored(self, err):
        """
        Executed whenever the translation errors.
        :type err: Exception
        """
        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(QPixmap(':/icons/error'))
        msgbox.setWindowIcon(QIcon(':/images/eddy'))
        msgbox.setWindowTitle('Load failed!')
        msgbox.setStandardButtons(QMessageBox.Close)
        msgbox.setText('Failed to load {}!'.format(os.path.basename(self.worker.filepath)))
        msgbox.setDetailedText(''.join(traceback.format_exception(type(err), err, err.__traceback__)))
        msgbox.exec_()
        self.workerThread.quit()
        self.reject()

    @pyqtSlot()
    def completed(self):
        """
        Executed whenever the translation completes.
        """
        self.workerThread.quit()
        self.worker.moveToThread(QApplication.instance().thread())
        self.accept()