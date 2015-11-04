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
    This command is used to compose an AsymmetricRole starting from a Role node.
    """
    def __init__(self, scene, role, inverse, complement, input1, input2, inclusion):
        """
        Initialize the command.
        :param scene: the graphic scene where this command is being performed.
        :param role: the role node where to base the composition.
        """
        super().__init__('create asymmetric role axiom')
        self.scene = scene
        self.role = role
        self.inverse = inverse
        self.complement = complement
        self.input1 = input1
        self.input2 = input2
        self.inclusion = inclusion

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in (self.inverse, self.complement, self.input1, self.input2, self.inclusion):
            self.scene.addItem(item)
            # map edges over source and target nodes
        for edge in (self.input1, self.input2, self.inclusion):
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove items from the scene
        for item in (self.inverse, self.complement, self.input1, self.input2, self.inclusion):
            self.scene.removeItem(item)
        # remove edge mappings from source and target nodes
        for edge in (self.input1, self.input2, self.inclusion):
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # emit updated signal
        self.scene.updated.emit()