# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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


class CommandComposeAxiom(QUndoCommand):
    """
    This command is used to compose an axioms.
    """
    def __init__(self, name, scene, source, nodes, edges):
        """
        Initialize the command.
        :param name: the name of the undo command
        :param scene: the graphic scene where this command is being performed.
        :param source: the source node of the composition
        :param nodes: a set of nodes to be used in the composition.
        :param edges: a set of edges to be used in the composition.
        """
        super().__init__(name)
        self.scene = scene
        self.source = source
        self.nodes = nodes
        self.edges = edges

    def redo(self):
        """redo the command"""
        # add items to the scene
        for item in self.nodes | self.edges:
            self.scene.addItem(item)
        # map edges over source and target nodes
        for edge in self.edges:
            edge.source.addEdge(edge)
            edge.target.addEdge(edge)
            edge.updateEdge()
        # emit updated signal
        self.scene.updated.emit()

    def undo(self):
        """undo the command"""
        # remove items from the scene
        for item in self.nodes | self.edges:
            self.scene.removeItem(item)
        # remove edge mappings from source and target nodes
        for edge in self.edges:
            edge.source.removeEdge(edge)
            edge.target.removeEdge(edge)
        # emit updated signal
        self.scene.updated.emit()