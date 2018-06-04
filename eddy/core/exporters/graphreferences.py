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

from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.functions.fsystem import fwrite


class GraphReferences(AbstractDiagramExporter):

    def __init__(self, diagram, session):

        super().__init__(diagram, session)
        self.document = None
        self.missing = {Item.FacetNode, Item.PropertyAssertionNode}

        self.success = False

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Xml

    def run(self,path):

        project = self.diagram.project

        # 1) CREATE THE DOCUMENT
        self.document = QtXml.QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8" standalone="no"')
        self.document.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.document.createElement('graphReferences')

        node_diagrams_dict = dict()

        for diagram in project.diagrams():
            for node in diagram.nodes():
                if node.isMeta():#if node.type() not in self.missing:

                    full_IRI = project.get_full_IRI(project.get_iri_of_node(node), None, node.remaining_characters)

                    if full_IRI not in node_diagrams_dict.keys():
                        node_diagrams_dict[full_IRI] = []

                        node_diagrams_dict[full_IRI].append(node.type().realName.replace(' node',''))

                    node_diagrams_dict[full_IRI].append(diagram.name)
                    node_diagrams_dict[full_IRI].append(str(int(node.pos().x())))
                    node_diagrams_dict[full_IRI].append(str(int(node.pos().y())))
                    node_diagrams_dict[full_IRI].append(str(int(node.width())))
                    node_diagrams_dict[full_IRI].append(str(int(node.height())))

        # 3) GENERATE NODES
        for node_full_text in node_diagrams_dict.keys():

            value = node_diagrams_dict[node_full_text]

            for i in range(1,len(value)-4,5):

                diag = value[i]
                x = value[i+1]
                y = value[i+2]
                w = value[i+3]
                h = value[i+4]

                diag_to_append = self.document.createElement('diagramName')
                diag_to_append.appendChild(self.document.createTextNode(diag))

                x_to_append = self.document.createElement('x')
                x_to_append.appendChild(self.document.createTextNode(x))

                y_to_append = self.document.createElement('y')
                y_to_append.appendChild(self.document.createTextNode(y))

                w_to_append = self.document.createElement('w')
                w_to_append.appendChild(self.document.createTextNode(w))

                h_to_append = self.document.createElement('h')
                h_to_append.appendChild(self.document.createTextNode(h))

                node_to_append = self.document.createElement(value[0])
                node_to_append.setAttribute('name', node_full_text)

                node_to_append.appendChild(diag_to_append)
                node_to_append.appendChild(x_to_append)
                node_to_append.appendChild(y_to_append)
                node_to_append.appendChild(w_to_append)
                node_to_append.appendChild(h_to_append)

                root.appendChild(node_to_append)

        # 4) APPEND THE GRAPH TO THE DOCUMENT
        self.document.appendChild(root)

        # 5) GENERATE THE FILE
        fwrite(self.document.toString(2), path)

        self.success = True

