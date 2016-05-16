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


from PyQt5.QtCore import Qt, QSettings, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QDialogButtonBox, QTabWidget, QFormLayout

from eddy import ORGANIZATION, APPNAME
from eddy.core.datatypes.system import Language
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect
from eddy.core.qt import Font

from eddy.lang import gettext as _

from eddy.ui.fields import SpinBox, ComboBox


class PreferencesDialog(QDialog):
    """
    This class implements the 'Preferences' dialog.
    """
    def __init__(self, parent=None):
        """
        Initialize the Preferences dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        arial12r = Font('Arial', 12)
        settings = QSettings(ORGANIZATION, APPNAME)

        #############################################
        # GENERAL TAB
        #################################

        self.languageLabel = QLabel(self)
        self.languageLabel.setFont(arial12r)
        self.languageLabel.setText(_('PREFERENCES_LABEL_LANGUAGE'))
        self.languageField = ComboBox(self)
        self.languageField.setFixedWidth(200)
        self.languageField.setFocusPolicy(Qt.StrongFocus)
        self.languageField.setFont(arial12r)
        for language in Language:
            self.languageField.addItem(language.name, language.value)
        language = settings.value('general/language', 'en', str)
        for i in range(self.languageField.count()):
            if self.languageField.itemData(i) == language:
                self.languageField.setCurrentIndex(i)
                break

        self.generalWidget = QWidget()
        self.generalLayout = QFormLayout(self.generalWidget)
        self.generalLayout.addRow(self.languageLabel, self.languageField)

        #############################################
        # EDITOR TAB
        #################################

        self.diagramSizeLabel = QLabel(self)
        self.diagramSizeLabel.setFont(arial12r)
        self.diagramSizeLabel.setText(_('PREFERENCES_LABEL_DIAGRAM_SIZE'))
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setFont(arial12r)
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setValue(settings.value('diagram/size', 5000, int))

        self.editorWidget = QWidget()
        self.editorLayout = QFormLayout(self.editorWidget)
        self.editorLayout.addRow(self.diagramSizeLabel, self.diagramSizeField)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # MAIN WIDGET
        #################################

        self.mainWidget = QTabWidget(self)
        self.mainWidget.addTab(self.generalWidget, _('PREFERENCES_TAB_GENERAL'))
        self.mainWidget.addTab(self.editorWidget, _('PREFERENCES_TAB_EDITOR'))
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setWindowTitle(_('PREFERENCES_WINDOW_TITLE'))

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        settings = QSettings(ORGANIZATION, APPNAME)
        settings.setValue('general/language', self.languageField.currentData())
        settings.setValue('diagram/size', self.diagramSizeField.value())
        settings.sync()
        super().accept()