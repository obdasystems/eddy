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


import io
import csv

from operator import itemgetter

from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import Item
from eddy.core.exporters.common import AbstractExporter
from eddy.core.functions.fsystem import fwrite


class CsvExporter(AbstractExporter):
    """
    This class can be used to export Graphol projects into CSV format.
    """
    K_NAME = 'NAME'
    K_TYPE = 'TYPE'
    K_DESCRIPTION = 'DESCRIPTION'
    K_DIAGRAMS = 'DIAGRAMS'

    Types = [
        Item.AttributeNode,
        Item.ConceptNode,
        Item.RoleNode,
    ]

    def __init__(self, project, path, session=None):
        """
        Initialize the CSV exporter.
        :type project: Project
        :type path: str
        :type session: Session
        """
        super().__init__(session)
        self.project = project
        self.path = path

    def run(self):
        """
        Perform CSV file generation.
        """
        csvdata = {x: {} for x in self.Types}

        for node in self.project.predicates():
            if node.type() in csvdata:
                # If there is no data for this predicate node, create a new entry.
                if not node.text() in csvdata[node.type()]:
                    meta = self.project.meta(node.type(), node.text())
                    csvdata[node.type()][node.text()] = {
                        self.K_NAME: meta.predicate,
                        self.K_TYPE: meta.item.shortName,
                        self.K_DESCRIPTION: meta.description,
                        self.K_DIAGRAMS: DistinctList(),
                    }
                # Append the name of the diagram to the diagram list.
                csvdata[node.type()][node.text()][self.K_DIAGRAMS] += [node.diagram.name]

        # Collect data in a buffer.
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow((self.K_NAME, self.K_TYPE, self.K_DESCRIPTION, self.K_DIAGRAMS))
        for i, j in sorted(((v, k) for k in csvdata for v in csvdata[k]), key=itemgetter(0)):
            writer.writerow((
                csvdata[j][i][self.K_NAME],
                csvdata[j][i][self.K_TYPE],
                csvdata[j][i][self.K_DESCRIPTION],
                sorted(csvdata[j][i][self.K_DIAGRAMS]),
            ))

        # Write to disk.
        fwrite(buffer.getvalue(), self.path)