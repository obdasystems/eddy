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


from PyQt5 import QtCore, QtXml

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.fsystem import fwrite


class GraphReferencesProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export the list of references (diagram, coordinates, size)
    for class, object property, and data property nodes in the project into an XML file.
    """
    def __init__(self, project, session):
        """
        Initialize the GraphReferencesProjectExporter
        :type project: Project
        :type session: Session
        """
        super().__init__(project, session)
        self.document = None
        self.missing = {Item.FacetNode, Item.PropertyAssertionNode}

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.GraphReferences

    def run(self, path):
        """
        Perform graph references document generation.
        :type path: str
        """
        # CREATE THE DOCUMENT
        self.document = QtXml.QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8" standalone="no"')
        self.document.appendChild(instruction)

        # CREATE ROOT ELEMENT
        root = self.document.createElement('graphReferences')

        # GENERATE NODES
        for diagram in self.project.diagrams():
            for node in diagram.nodes():
                QtCore.QCoreApplication.processEvents()
                if node.isMeta():
                    iri = self.project.get_full_IRI(
                        self.project.get_iri_of_node(node), None, node.remaining_characters)
                    diagramElement = self.document.createElement('diagramName')
                    diagramElement.appendChild(self.document.createTextNode(diagram.name))
                    xElement = self.document.createElement('x')
                    xElement.appendChild(self.document.createTextNode(str(int(node.x()))))
                    yElement = self.document.createElement('y')
                    yElement.appendChild(self.document.createTextNode(str(int(node.y()))))
                    wElement = self.document.createElement('w')
                    wElement.appendChild(self.document.createTextNode(str(int(node.width()))))
                    hElement = self.document.createElement('h')
                    hElement.appendChild(self.document.createTextNode(str(int(node.height()))))
                    nodeElement = self.document.createElement(node.type().realName.replace(' node', ''))
                    nodeElement.setAttribute('name', iri)
                    nodeElement.appendChild(diagramElement)
                    nodeElement.appendChild(xElement)
                    nodeElement.appendChild(yElement)
                    nodeElement.appendChild(wElement)
                    nodeElement.appendChild(hElement)
                    root.appendChild(nodeElement)

        # APPEND THE GRAPH TO THE DOCUMENT
        self.document.appendChild(root)

        # GENERATE THE FILE
        fwrite(self.document.toString(2), path)