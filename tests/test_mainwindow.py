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


from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from eddy.ui.mdi import MdiSubWindow
from eddy.ui.scene import DiagramScene
from eddy.ui.view import MainView

from tests import EddyTestCase


class Test_MainWindow(EddyTestCase):

    def test_new_document_from_toolbar(self):
        # WHEN
        QTest.mouseClick(self.mainwindow.toolbar.widgetForAction(self.mainwindow.actionNewDocument), Qt.LeftButton)
        # THEN
        self.assertEqual(1, len(self.mainwindow.mdi.subWindowList()))
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0], MdiSubWindow)
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0].widget(), MainView)
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0].widget().scene(), DiagramScene)
        self.assertFalse(self.mainwindow.actionSaveDocument.isEnabled())
        self.assertFalse(self.mainwindow.actionCut.isEnabled())
        self.assertFalse(self.mainwindow.actionCopy.isEnabled())
        self.assertFalse(self.mainwindow.actionPaste.isEnabled())
        self.assertFalse(self.mainwindow.actionDelete.isEnabled())
        self.assertFalse(self.mainwindow.actionBringToFront.isEnabled())
        self.assertFalse(self.mainwindow.actionSendToBack.isEnabled())
        self.assertFalse(self.mainwindow.changeNodeBrushButton.isEnabled())
        self.assertFalse(self.mainwindow.undogroup.canRedo())
        self.assertFalse(self.mainwindow.undogroup.canUndo())
        self.assertTrue(self.mainwindow.undogroup.isClean())

    def test_new_document_from_keyboard_shortcut(self):
        # WHEN
        QTest.keyClick(self.mainwindow, 'n', Qt.ControlModifier)
        # THEN
        self.assertEqual(1, len(self.mainwindow.mdi.subWindowList()))
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0], MdiSubWindow)
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0].widget(), MainView)
        self.assertIsInstance(self.mainwindow.mdi.subWindowList()[0].widget().scene(), DiagramScene)
        self.assertFalse(self.mainwindow.actionSaveDocument.isEnabled())
        self.assertFalse(self.mainwindow.actionCut.isEnabled())
        self.assertFalse(self.mainwindow.actionCopy.isEnabled())
        self.assertFalse(self.mainwindow.actionPaste.isEnabled())
        self.assertFalse(self.mainwindow.actionDelete.isEnabled())
        self.assertFalse(self.mainwindow.actionBringToFront.isEnabled())
        self.assertFalse(self.mainwindow.actionSendToBack.isEnabled())
        self.assertFalse(self.mainwindow.changeNodeBrushButton.isEnabled())
        self.assertFalse(self.mainwindow.undogroup.canRedo())
        self.assertFalse(self.mainwindow.undogroup.canUndo())
        self.assertTrue(self.mainwindow.undogroup.isClean())