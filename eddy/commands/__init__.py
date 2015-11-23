# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from eddy.commands.nodes import CommandNodeAdd
from eddy.commands.nodes import CommandNodeSetZValue
from eddy.commands.nodes import CommandNodeRezize
from eddy.commands.nodes import CommandNodeMove
from eddy.commands.nodes import CommandNodeLabelMove
from eddy.commands.nodes import CommandNodeLabelEdit
from eddy.commands.nodes import CommandNodeValueDomainSelectDatatype
from eddy.commands.nodes import CommandNodeHexagonSwitchTo
from eddy.commands.nodes import CommandNodeSquareChangeRestriction
from eddy.commands.nodes import CommandNodeSetURL
from eddy.commands.nodes import CommandNodeSetDescription
from eddy.commands.nodes import CommandConceptNodeSetSpecial
from eddy.commands.nodes import CommandNodeChangeInputOrder
from eddy.commands.nodes import CommandNodeChangeBrush

from eddy.commands.edges import CommandEdgeAdd
from eddy.commands.edges import CommandEdgeAnchorMove
from eddy.commands.edges import CommandEdgeBreakpointAdd
from eddy.commands.edges import CommandEdgeBreakpointMove
from eddy.commands.edges import CommandEdgeBreakpointDel
from eddy.commands.edges import CommandEdgeInclusionToggleComplete
from eddy.commands.edges import CommandEdgeInputToggleFunctional
from eddy.commands.edges import CommandEdgeSwap

from eddy.commands.common import CommandComposeAxiom
from eddy.commands.common import CommandItemsMultiAdd
from eddy.commands.common import CommandItemsMultiRemove

from eddy.commands.scene import CommandSceneResize


__all__ = [
    'CommandComposeAxiom',
    'CommandNodeAdd',
    'CommandNodeSetZValue',
    'CommandNodeRezize',
    'CommandNodeMove',
    'CommandNodeLabelMove',
    'CommandNodeLabelEdit',
    'CommandNodeValueDomainSelectDatatype',
    'CommandNodeHexagonSwitchTo',
    'CommandNodeSquareChangeRestriction',
    'CommandNodeSetURL',
    'CommandNodeSetDescription',
    'CommandConceptNodeSetSpecial',
    'CommandNodeChangeInputOrder',
    'CommandNodeChangeBrush',
    'CommandEdgeAdd',
    'CommandEdgeAnchorMove',
    'CommandEdgeBreakpointAdd',
    'CommandEdgeBreakpointMove',
    'CommandEdgeBreakpointDel',
    'CommandEdgeInclusionToggleComplete',
    'CommandEdgeInputToggleFunctional',
    'CommandEdgeSwap',
    'CommandItemsMultiAdd',
    'CommandItemsMultiRemove',
    'CommandSceneResize',
]