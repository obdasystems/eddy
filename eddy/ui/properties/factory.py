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


from PyQt5.QtCore import QObject

from eddy.core.datatypes import Item

from eddy.ui.properties.nodes import NodeProperty, EditableNodeProperty
from eddy.ui.properties.nodes import OrderedInputNodeProperty
from eddy.ui.properties.scene import SceneProperty


class PropertyFactory(QObject):
    """
    This class can be used to produce properties dialog windows.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: QObject
        """
        super().__init__(parent)

    @staticmethod
    def create(scene, node=None):
        """
        Build and return a property dialog according to the given parameters.
        :type scene: DiagramScene
        :type node: AbstractNode
        :rtype: QDialog
        """
        if not node:
            return SceneProperty(scene=scene)
        if node.isItem(Item.RoleChainNode, Item.PropertyAssertionNode):
            return OrderedInputNodeProperty(scene=scene, node=node)
        if node.predicate and node.label.editable:
            return EditableNodeProperty(scene=scene, node=node)
        return NodeProperty(scene=scene, node=node)


