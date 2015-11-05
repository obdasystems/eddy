# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from PyQt5.QtWidgets import QUndoCommand


class CommandComposeAsymmetricRole(QUndoCommand):
    """
    This command is used to compose an Asymmetric role starting from a Role node.
    """
    def __init__(self, scene, role, inverse, complement, edge1, edge2, edge3):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param role: the role node where to base the composition.
        :param inverse: the role inverse node to use in the axiom.
        :param complement: the complement node to use in the axiom.
        :param edge1: the input edge connecting role node to the role inverse node.
        :param edge2: the input edge connecting the role inverse node to the complement node.
        :param edge3: the inclusion edge connecting the role node to the complement node.
        """
        super().__init__('create asymmetric role axiom')
        self.scene = scene
        self.role = role
        self.inverse = inverse
        self.complement = complement
        self.edge1 = edge1
        self.edge2 = edge2
        self.edge3 = edge3

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in (self.inverse, self.complement, self.edge1, self.edge2, self.edge3):
            self.scene.addItem(item)
            # map edges over source and target nodes
        for edge in (self.edge1, self.edge2, self.edge3):
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove items from the scene
        for item in (self.inverse, self.complement, self.edge1, self.edge2, self.edge3):
            self.scene.removeItem(item)
        # remove edge mappings from source and target nodes
        for edge in (self.edge1, self.edge2, self.edge3):
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # emit updated signal
        self.scene.updated.emit()


class CommandComposeIrreflexiveRole(QUndoCommand):
    """
    This command is used to compose an Irreflexive role starting from a Role node.
    """
    def __init__(self, scene, role, restriction, complement, concept, edge1, edge2, edge3):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param role: the role node where to base the composition.
        :param restriction: the domain restriction node to use in the axiom.
        :param complement: the complement node to use in the axiom.
        :param concept: the special concept node (TOP) to use in the axiom.
        :param edge1: the input edge connecting role node to the domain restriction node.
        :param edge2: the input edge connecting the domain restriction node to the complement node.
        :param edge3: the inclusion edge connecting the special concept node to the complement node.
        """
        super().__init__('create irreflexive role axiom')
        self.scene = scene
        self.role = role
        self.restriction = restriction
        self.complement = complement
        self.concept = concept
        self.edge1 = edge1
        self.edge2 = edge2
        self.edge3 = edge3

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in (self.restriction, self.complement, self.concept, self.edge1, self.edge2, self.edge3):
            self.scene.addItem(item)
            # map edges over source and target nodes
        for edge in (self.edge1, self.edge2, self.edge3):
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove items from the scene
        for item in (self.restriction, self.complement, self.concept, self.edge1, self.edge2, self.edge3):
            self.scene.removeItem(item)
        # remove edge mappings from source and target nodes
        for edge in (self.edge1, self.edge2, self.edge3):
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # emit updated signal
        self.scene.updated.emit()


class CommandComposeReflexiveRole(QUndoCommand):
    """
    This command is used to compose a Reflexive role starting from a Role node.
    """
    def __init__(self, scene, role, restriction, concept, edge1, edge2):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param role: the role node where to base the composition.
        :param restriction: the domain restriction node to use in the axiom.
        :param concept: the special concept node (TOP) to use in the axiom.
        :param edge1: the input edge connecting role node to the domain restriction node.
        :param edge2: the inclusion edge connecting the special concept node to the domain restriction node.
        """
        super().__init__('create reflexive role axiom')
        self.scene = scene
        self.role = role
        self.restriction = restriction
        self.concept = concept
        self.edge1 = edge1
        self.edge2 = edge2

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in (self.restriction, self.concept, self.edge1, self.edge2):
            self.scene.addItem(item)
            # map edges over source and target nodes
        for edge in (self.edge1, self.edge2):
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove items from the scene
        for item in (self.restriction, self.concept, self.edge1, self.edge2):
            self.scene.removeItem(item)
        # remove edge mappings from source and target nodes
        for edge in (self.edge1, self.edge2):
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # emit updated signal
        self.scene.updated.emit()