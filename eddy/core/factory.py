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


from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMenu

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.misc import first

from eddy.ui.properties import DiagramProperty
from eddy.ui.properties import FacetNodeProperty
from eddy.ui.properties import NodeProperty
from eddy.ui.properties import OrderedInputNodeProperty
from eddy.ui.properties import PredicateNodeProperty
from eddy.ui.properties import ValueDomainNodeProperty
from eddy.ui.properties import ValueNodeProperty


class MenuFactory(QObject):
    """
    This class can be used to produce diagram items contextual menus.
    """

    def __init__(self, session):
        """
        Initialize the factory.
        :type session: Session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the active session (alias for MenuFactory.session.project).
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the currently active session (alias for MenuFactory.parent()).
        :return: Session
        """
        return self.parent()

    #############################################
    #   DIAGRAM
    #################################

    def buildDiagramMenu(self, diagram):
        """
        Build and return a QMenu instance for the given diagram.
        :type diagram: Diagram
        :rtype: QMenu
        """
        menu = QMenu()
        if not self.session.clipboard.empty():
            menu.addAction(self.session.action('paste'))
        menu.addAction(self.session.action('select_all'))
        menu.addSeparator()
        menu.addAction(self.session.action('diagram_properties'))
        self.session.action('diagram_properties').setData(diagram)
        return menu

    #############################################
    #   COMPOUND
    #################################

    def buildCompoundItemMenu(self, diagram, items):
        """
        Build and return a QMenu instance for the selection of items.
        :type diagram: Diagram
        :type items: T <= list|tuple
        :rtype: QMenu
        """
        menu = QMenu()
        menu.addAction(self.session.action('delete'))
        menu.addAction(self.session.action('purge'))
        if any([x.isNode() for x in items]):
            menu.addSeparator()
            menu.addAction(self.session.action('bring_to_front'))
            menu.addAction(self.session.action('send_to_back'))
            menu.addSeparator()
            menu.addAction(self.session.action('cut'))
            menu.addAction(self.session.action('copy'))
        return menu

    #############################################
    #   EDGES
    #################################

    def buildGenericEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for a generic edge.
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.actions('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
            menu.addAction(self.session.action('purge'))
            menu.addAction(self.session.action('swap_edge'))
            self.session.action('swap_edge').setVisible(edge.isSwapAllowed())
        return menu

    def buildInclusionEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for Inclusion edges.
        :type diagram: Diagram
        :type edge: InclusionEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.actions('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
            menu.addAction(self.session.action('swap_edge'))
            menu.addSeparator()
            menu.addAction(self.session.action('toggle_edge_equivalence'))
            self.session.action('toggle_edge_equivalence').setVisible(edge.isEquivalenceAllowed())
            self.session.action('swap_edge').setVisible(edge.isSwapAllowed())
        return menu

    def buildInputEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for Input edges.
        :type diagram: Diagram
        :type edge: InputEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.actions('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
            menu.addAction(self.session.action('swap_edge'))
            self.session.action('swap_edge').setVisible(edge.isSwapAllowed())
        return menu

    def buildMembershipEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for InstanceOf edges.
        :type diagram: Diagram
        :type edge: InstanceOfEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.actions('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
        return menu

    #############################################
    #   NODES
    #################################

    def buildGenericNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for a generic node.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QMenu
        """
        menu = QMenu()
        menu.addAction(self.session.action('delete'))
        menu.addAction(self.session.action('purge'))
        menu.addSeparator()
        menu.addAction(self.session.action('cut'))
        menu.addAction(self.session.action('copy'))
        menu.addAction(self.session.action('paste'))
        menu.addSeparator()
        menu.addAction(self.session.action('bring_to_front'))
        menu.addAction(self.session.action('send_to_back'))
        menu.addSeparator()
        menu.addAction(self.session.action('node_properties'))
        return menu

    def buildAttributeNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for attribute nodes.
        :type diagram: Diagram
        :type node: AttributeNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('compose'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special is None)
        return menu

    def buildComplementNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for complement nodes.
        :type diagram: Diagram
        :type node: ComplementNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            switch = {
                Identity.Attribute: {Item.ComplementNode},
                Identity.Concept: {Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode},
                Identity.Role: {Item.ComplementNode, Item.RoleChainNode, Item.RoleInverseNode},
                Identity.ValueDomain: {Item.ComplementNode, Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode},
                Identity.Unknown: {Item.ComplementNode},
                Identity.Neutral: {
                    Item.ComplementNode,
                    Item.DisjointUnionNode,
                    Item.EnumerationNode,
                    Item.IntersectionNode,
                    Item.RoleChainNode,
                    Item.RoleInverseNode,
                    Item.UnionNode,
                },
            }
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch[node.identity()])
        return menu

    def buildConceptNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for concept nodes.
        :type diagram: Diagram
        :type node: ConceptNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special is None)
        return menu

    def buildDatatypeRestrictionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for datatype restriction nodes.
        :type diagram: Diagram
        :type node: DatatypeRestrictionNode
        :rtype: QMenu
        """
        return self.buildOperatorNodeMenu(diagram, node)

    def buildDisjointUnionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for disjoint union nodes.
        :type diagram: Diagram
        :type node: DisjointUnionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch)
        return menu

    def buildDomainRestrictionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for domain restriction nodes.
        :type diagram: Diagram
        :type node: DomainRestrictionNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.addSeparator()
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_restriction'))
        for action in self.session.action('switch_restriction').actions():
            action.setChecked(node.type() is action.data())
            action.setVisible(True)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('property_restriction'))
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is Identity.Attribute
        qualified = node.isQualifiedRestriction()
        attribute = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        for action in self.session.action('restriction').actions():
            action.setChecked(node.restriction is action.data())
            action.setVisible(action.data() is not Restriction.Self or not qualified and not attribute)
        menu.insertSeparator(self.session.action('node_properties'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        return menu

    def buildEnumerationNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for enumeration nodes.
        :type diagram: Diagram
        :type node: EnumerationNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            if node.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge):
                # If we have input edges targeting the node keep only the Enumeration
                # action active: individuals can be connected only to Enumeration nodes
                # and Property Assertion ones, so switching to another operator is an error.
                for action in self.session.action('switch_operator').actions():
                    action.setVisible(action.data() is Item.EnumerationNode)
            elif node.outgoingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge):
                # We have inclusion edges attached to this edge but no input => allow
                # switching to operators whose identities set intersects the one of this node.
                switch = {Item.DisjointUnionNode, Item.EnumerationNode, Item.IntersectionNode, Item.UnionNode}
                for action in self.session.action('switch_operator').actions():
                    action.setVisible(action.data() in switch)
        return menu

    def buildFacetNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for facet nodes.
        :type diagram: Diagram
        :type node: FacetNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('facet'))
        menu.insertSeparator(self.session.action('node_properties'))

        #############################################
        # BEGIN CONSTRAIN FACET SWITCH
        #################################

        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        facet = node.facet
        admissible = [x for x in Facet]
        restriction = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if restriction:
            valuedomain = first(restriction.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if valuedomain:
                admissible = Facet.forDatatype(valuedomain.datatype)
        for action in self.session.action('facet').actions():
            action.setChecked(action.data() is facet)
            action.setVisible(action.data() in admissible)

        #############################################
        # END CONSTRAIN FACET SWITCH
        #################################

        return menu

    def buildIndividualNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for individual nodes.
        :type diagram: Diagram
        :type node: IndividualNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_individual'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))

        #############################################
        # BEGIN CONSTRAIN IDENTITY SWITCH
        #################################

        instance = True
        value = True

        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.EnumerationNode
        f3 = lambda x: x.type() is Item.IndividualNode
        f4 = lambda x: x.type() is Item.PropertyAssertionNode
        f5 = lambda x: x.type() is Item.MembershipEdge
        f6 = lambda x: x.identity() in {Identity.Attribute, Identity.Role}

        enumeration = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if enumeration:
            num = len(enumeration.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            instance = enumeration.identity() is Identity.Concept or num < 2
            value = enumeration.identity() is Identity.ValueDomain or num < 2

        assertion = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f4))
        if assertion:
            operand = first(assertion.outgoingNodes(filter_on_edges=f5, filter_on_nodes=f6))
            if operand:
                if operand.identity() is Identity.Role:
                    value = False
                elif operand.identity() is Identity.Attribute:
                    num = len(assertion.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                    instance = instance and (node.identity() is Identity.Individual or num < 2)
                    value = value and (node.identity() is Identity.Value or num < 2)

        for a in self.session.action('switch_individual').actions():
            a.setChecked(a.data() is node.identity())
            a.setVisible(a.data() is Identity.Individual and instance or a.data() is Identity.Value and value)

        #############################################
        # END CONSTRAIN IDENTITY SWITCH
        #################################

        return menu

    def buildIntersectionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for intersection nodes.
        :type diagram: Diagram
        :type node: IntersectionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch)
        return menu

    def buildOperatorNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for operator nodes.
        :type diagram: Diagram
        :type node: OperatorNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_operator'))
        menu.insertSeparator(self.session.action('node_properties'))
        for action in self.session.action('switch_operator').actions():
            action.setChecked(node.type() is action.data())
            action.setVisible(True)
        return menu

    def buildPropertyAssertionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for property assertion nodes.
        :type diagram: Diagram
        :type node: PropertyAssertionNode
        :rtype: QMenu
        """
        return self.buildGenericNodeMenu(diagram, node)

    def buildRangeRestrictionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for range restriction nodes.
        :type diagram: Diagram
        :type node: RangeRestrictionNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.addSeparator()
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_restriction'))
        for action in self.session.action('switch_restriction').actions():
            action.setChecked(node.type() is action.data())
            action.setVisible(True)
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is Identity.Attribute
        if not first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)):
            qualified = node.isQualifiedRestriction()
            menu.insertMenu(self.session.action('node_properties'), self.session.menu('property_restriction'))
            for action in self.session.action('restriction').actions():
                action.setChecked(node.restriction is action.data())
                action.setVisible(action.data() is not Restriction.Self or not qualified)
        menu.insertSeparator(self.session.action('node_properties'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        return menu

    def buildRoleNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for role nodes.
        :type diagram: Diagram
        :type node: RoleNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('compose'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        menu.insertAction(self.session.action('node_properties'), self.session.action('invert_role'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special is None)
        return menu

    def buildRoleInverseNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for role inverse nodes.
        :type diagram: Diagram
        :type node: RoleInverseNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            switch = {Item.ComplementNode, Item.RoleChainNode, Item.RoleInverseNode}
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch)
        return menu

    def buildRoleChainNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for role chain nodes.
        :type diagram: Diagram
        :type node: RoleChainNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            f1 = lambda x: x.type() is Item.InputEdge
            switch = {Item.ComplementNode, Item.RoleChainNode, Item.RoleInverseNode}
            if len(node.incomingNodes(filter_on_edges=f1)) > 1:
                switch = {Item.RoleChainNode}
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch)
        return menu

    def buildUnionNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for union nodes.
        :type diagram: Diagram
        :type node: UnionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(diagram, node)
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() in switch)
        return menu

    def buildValueDomainNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for value domain nodes.
        :type diagram: Diagram
        :type node: ValueDomainNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('datatype'))
        menu.insertSeparator(self.session.action('node_properties'))
        for action in self.session.action('datatype').actions():
            action.setChecked(node.datatype == action.data())
        return menu

    #############################################
    #   LABEL
    #################################

    def insertLabelActions(self, menu, node):
        """
        Insert label specific actions in the given menu.
        :type menu: QMenu
        :type node: AbstractNode
        """
        if node.label.isMovable() and node.label.isMoved():
            menu.insertAction(self.session.action('node_properties'), self.session.action('relocate_label'))

    #############################################
    #   FACTORY
    #################################

    def create(self, diagram, items, pos=None):
        """
        Build and return a QMenu instance according to the given parameters.
        :type diagram: Diagram
        :type items: T <= list|tuple
        :type pos: QPointF
        :rtype: QMenu
        """
        ## NO ITEM
        if not items:
            return self.buildDiagramMenu(diagram)

        ## MULTIPLE ITEMS
        if len(items) > 1:
            return self.buildCompoundItemMenu(diagram, items)

        item = first(items)

        ## NODES
        if item.type() is Item.AttributeNode:
            return self.buildAttributeNodeMenu(diagram, item)
        if item.type() is Item.ComplementNode:
            return self.buildComplementNodeMenu(diagram, item)
        if item.type() is Item.ConceptNode:
            return self.buildConceptNodeMenu(diagram, item)
        if item.type() is Item.DatatypeRestrictionNode:
            return self.buildDatatypeRestrictionNodeMenu(diagram, item)
        if item.type() is Item.DisjointUnionNode:
            return self.buildDisjointUnionNodeMenu(diagram, item)
        if item.type() is Item.DomainRestrictionNode:
            return self.buildDomainRestrictionNodeMenu(diagram, item)
        if item.type() is Item.EnumerationNode:
            return self.buildEnumerationNodeMenu(diagram, item)
        if item.type() is Item.IndividualNode:
            return self.buildIndividualNodeMenu(diagram, item)
        if item.type() is Item.FacetNode:
            return self.buildFacetNodeMenu(diagram, item)
        if item.type() is Item.IntersectionNode:
            return self.buildIntersectionNodeMenu(diagram, item)
        if item.type() is Item.PropertyAssertionNode:
            return self.buildPropertyAssertionNodeMenu(diagram, item)
        if item.type() is Item.RangeRestrictionNode:
            return self.buildRangeRestrictionNodeMenu(diagram, item)
        if item.type() is Item.RoleNode:
            return self.buildRoleNodeMenu(diagram, item)
        if item.type() is Item.RoleInverseNode:
            return self.buildRoleInverseNodeMenu(diagram, item)
        if item.type() is Item.RoleChainNode:
            return self.buildRoleChainNodeMenu(diagram, item)
        if item.type() is Item.UnionNode:
            return self.buildUnionNodeMenu(diagram, item)
        if item.type() is Item.ValueDomainNode:
            return self.buildValueDomainNodeMenu(diagram, item)

        ## EDGES
        if item.type() is Item.InclusionEdge:
            return self.buildInclusionEdgeMenu(diagram, item, pos)
        if item.type() is Item.InputEdge:
            return self.buildInputEdgeMenu(diagram, item, pos)
        if item.type() is Item.MembershipEdge:
            return self.buildMembershipEdgeMenu(diagram, item, pos)

        ## GENERIC
        if item.isNode():
            return self.buildGenericNodeMenu(diagram, item)
        if item.isEdge():
            return self.buildGenericEdgeMenu(diagram, item, pos)

        raise RuntimeError('could not create menu for {0}'.format(item))


class PropertyFactory(QObject):
    """
    This class can be used to produce properties dialog windows.
    """
    def __init__(self, session):
        """
        Initialize the factory.
        :type session: Session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the project loaded in the active session (alias for PropertyFactory.session.project).
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the active session (alias for PropertyFactory.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def create(self, diagram, node=None):
        """
        Build and return a property dialog according to the given parameters.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QDialog
        """
        if not node:
            properties = DiagramProperty(diagram, self.session)
        else:
            if node.type() is Item.AttributeNode:
                properties = PredicateNodeProperty(diagram, node, self.session)
            elif node.type() is Item.ConceptNode:
                properties = PredicateNodeProperty(diagram, node, self.session)
            elif node.type() is Item.RoleNode:
                properties = PredicateNodeProperty(diagram, node, self.session)
            elif node.type() is Item.ValueDomainNode:
                properties = ValueDomainNodeProperty(diagram, node, self.session)
            elif node.type() is Item.IndividualNode:
                if node.identity() is Identity.Individual:
                    properties = PredicateNodeProperty(diagram, node, self.session)
                else:
                    properties = ValueNodeProperty(diagram, node, self.session)
            elif node.type() is Item.PropertyAssertionNode:
                properties = OrderedInputNodeProperty(diagram, node, self.session)
            elif node.type() is Item.RoleChainNode:
                properties = OrderedInputNodeProperty(diagram, node, self.session)
            elif node.type() is Item.FacetNode:
                properties = FacetNodeProperty(diagram, node, self.session)
            else:
                properties = NodeProperty(diagram, node, self.session)
        properties.setFixedSize(properties.sizeHint())
        return properties