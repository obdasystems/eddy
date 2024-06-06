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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

from PyQt5 import (
    QtCore,
    QtGui,
)

from eddy.core.functions.signals import connect, disconnect
from eddy.core.metadata import K_REPO_MONITOR
from eddy.core.output import getLogger
from eddy.core.plugin import AbstractPlugin
from eddy.ui.dock import DockWidget
from .widgets import MetadataImporterWidget  # noqa

LOGGER = getLogger()


class MetadataImporterPlugin(AbstractPlugin):
    """
    Search and import ontology metadata from an external service.
    """
    sgnProjectChanged = QtCore.pyqtSignal(str)
    sgnUpdateState = QtCore.pyqtSignal()

    def __init__(self, spec, session):
        """
        Initialises a new instance of the metadata importer plugin.
        :type spec: PluginSpec
        :type session: Session
        """
        super().__init__(spec, session)

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Filters events if this object has been installed as an event filter for the watched object.
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        widget = self.widget('metadata_importer')  # type: MetadataImporterWidget
        # CONNECT TO PROJECT SPECIFIC SIGNALS
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnPrefixAdded, widget.onPrefixChanged)
        connect(self.project.sgnPrefixModified, widget.onPrefixChanged)
        connect(self.project.sgnPrefixRemoved, widget.onPrefixChanged)
        connect(K_REPO_MONITOR.sgnUpdated, widget.doUpdateState)
        widget.onPrefixChanged()
        widget.doUpdateState()

    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Executed when the plugin session updates its state.
        """
        pass

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        widget = self.widget('metadata_importer')  # type: MetadataImporterWidget
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnPrefixAdded, widget.onPrefixChanged)
        disconnect(self.project.sgnPrefixModified, widget.onPrefixChanged)
        disconnect(self.project.sgnPrefixRemoved, widget.onPrefixChanged)
        disconnect(K_REPO_MONITOR.sgnUpdated, widget.doUpdateState)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.sgnUpdateState, self.doUpdateState)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Starting Metadata Importer plugin')
        widget = MetadataImporterWidget(self)
        widget.setObjectName('metadata_importer')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Metadata Importer', QtGui.QIcon(':icons/18/ic_explore_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea
            | QtCore.Qt.RightDockWidgetArea
            | QtCore.Qt.BottomDockWidgetArea
        )
        widget.setObjectName('metadata_importer_dock')
        widget.setWidget(self.widget('metadata_importer'))
        self.addWidget(widget)

        # CREATE SHORTCUTS
        action = widget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+8'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('metadata_importer_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(
            QtCore.Qt.LeftDockWidgetArea,
            self.widget('metadata_importer_dock'),
        )

        # CONFIGURE SIGNAL/SLOTS
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.sgnUpdateState, self.doUpdateState)
