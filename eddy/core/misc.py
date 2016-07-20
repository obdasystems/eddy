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


from PyQt5.QtWidgets import QAction

from eddy.core.functions.misc import isEmpty
from eddy.core.output import getLogger


LOGGER = getLogger(__name__)


class HasActionSystem(object):
    """
    Mixin which adds the ability to store and retrieve actions from/to a QObject.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._actionsDict = {}
        self._actionsList = []

    def action(self, objectName):
        """
        Returns the reference to a QAction or to a QActionGroup given it's objectName.
        :type objectName: str
        :rtype: T <= QAction|QActionGroup
        """
        return self._actionsDict.get(objectName, None)

    def actions(self):
        """
        Returns the list of QAction.
        :rtype: list
        """
        return self._actionsList

    def addAction(self, action):
        """
        Add a QAction or a QActionGroup to the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        self._actionsList.append(action)
        self._actionsDict[action.objectName()] = action
        LOGGER.debug("Added %s(%s)", action.__class__.__name__, action.objectName())
        return action

    def addActions(self, actions):
        """
        Add the given group of QAction or a QActionGroup to the set.
        :type actions: T <= list|tuple
        """
        for action in actions:
            self.addAction(action)

    def insertAction(self, action, before):
        """
        Insert the given QAction or QActionGroup before the given one.
        :type action: T <= QAction|QActionGroup
        :type before: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        self._actionsList.insert(self._actionsList.index(before), action)
        self._actionsDict[action.objectName()] = action
        LOGGER.debug("Added %s(%s) before %s(%s)",
                     action.__class__.__name__, action.objectName(),
                     before.__class__.__name__, before.objectName())
        return action

    def insertActions(self, actions, before):
        """
        Insert the given group of QAction or QActionGroup before the given one.
        :type actions: T <= list|tuple
        :type before: T <= QAction|QActionGroup
        """
        for action in actions:
            self.insertAction(action, before)

    def removeAction(self, action):
        """
        Removes the given QAction or QActionGroup from the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        self._actionsList.remove(action)
        del self._actionsDict[action.objectName()]
        return action