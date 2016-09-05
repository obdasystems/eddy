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


from PyQt5.QtGui import QBrush, QColor

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.items.nodes.common.restriction import RestrictionNode


class RangeRestrictionNode(RestrictionNode):
    """
    This class implements the 'Range Restriction' node.
    """
    Identities = {Identity.Concept, Identity.ValueDomain, Identity.Neutral}
    Type = Item.RangeRestrictionNode

    def __init__(self, brush=None, **kwargs):
        """
        Initialize the node.
        :type brush: QBrush
        """
        super(RangeRestrictionNode, self).__init__(brush=QBrush(QColor(0, 0, 0, 255)), **kwargs)

    #############################################
    #   INTERFACE
    #################################

    def setText(self, text):
        """
        Set the label text making sure not to have 'self' as range.
        :type text: str
        """
        restriction = Restriction.forLabel(text)
        if not restriction:
            text = Restriction.Exists.toString()
        self.label.setText(text)