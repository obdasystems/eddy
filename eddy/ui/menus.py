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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMenu

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.datatypes.owl import Facet
from eddy.core.functions.misc import first


class MenuFactory(QObject):
    """
    This class can be used to produce diagram items contextual menus.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: QObject
        """
        super().__init__(parent)

    #############################################
    #   DIAGRAM
    #################################

    @staticmethod
    def buildDiagramMenu(mainwindow, diagram):
        """
        Build and return a QMenu instance for the given diagram.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :rtype: QMenu
        """
        menu = QMenu()
        if not mainwindow.clipboard.empty():
            menu.addAction(mainwindow.actionPaste)
        menu.addAction(mainwindow.actionSelectAll)
        menu.addSeparator()
        menu.addAction(mainwindow.actionDiagramProperties)
        return menu

    #############################################
    #   EDGES
    #################################

    @staticmethod
    def buildGenericEdgeMenu(mainwindow, diagram, edge, pos):
        """
        Build and return a QMenu instance for a generic edge.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type edge: AbstractEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakpointAt(pos)
        if breakpoint is not None:
            action = mainwindow.actionRemoveEdgeBreakpoint
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(mainwindow.actionDelete)
            menu.addAction(mainwindow.actionSwapEdge)
        return menu

    @staticmethod
    def buildInclusionEdgeMenu(mainwindow, diagram, edge, pos):
        """
        Build and return a QMenu instance for Inclusion edges.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type edge: InclusionEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakpointAt(pos)
        if breakpoint is not None:
            action = mainwindow.actionRemoveEdgeBreakpoint
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            # BUILD THE MENU
            menu.addAction(mainwindow.actionDelete)
            menu.addAction(mainwindow.actionSwapEdge)
            menu.addSeparator()
            menu.addAction(mainwindow.actionToggleEdgeComplete)
            # SETUP ACTIONS STATE
            validate = diagram.project.validator.validate
            result = validate(edge.target, edge, edge.source)
            mainwindow.actionSwapEdge.setVisible(result.valid)
            mainwindow.actionToggleEdgeComplete.setChecked(edge.complete)
        return menu

    @staticmethod
    def buildInputEdgeMenu(mainwindow, diagram, edge, pos):
        """
        Build and return a QMenu instance for Input edges.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type edge: InputEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakpointAt(pos)
        if breakpoint is not None:
            action = mainwindow.actionRemoveEdgeBreakpoint
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            # BUILD THE MENU
            menu.addAction(mainwindow.actionDelete)
            menu.addAction(mainwindow.actionSwapEdge)
            menu.addSeparator()
            # SETUP ACTIONS STATE
            validate = diagram.project.validator.validate
            result = validate(edge.target, edge, edge.source)
            mainwindow.actionSwapEdge.setVisible(result.valid)
        return menu

    @staticmethod
    def buildMembershipEdgeMenu(mainwindow, diagram, edge, pos):
        """
        Build and return a QMenu instance for InstanceOf edges.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type edge: InstanceOfEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakpointAt(pos)
        if breakpoint is not None:
            action = mainwindow.actionRemoveEdgeBreakpoint
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(mainwindow.actionDelete)
        return menu

    #############################################
    #   NODES
    #################################

    @staticmethod
    def buildGenericNodeMenu(mainwindow, diagram, node):
        """
        Build and return a QMenu instance for a generic node.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QMenu
        """
        menu = QMenu()
        menu.addAction(mainwindow.actionDelete)
        menu.addSeparator()
        menu.addAction(mainwindow.actionCut)
        menu.addAction(mainwindow.actionCopy)
        menu.addAction(mainwindow.actionPaste)
        menu.addSeparator()
        menu.addAction(mainwindow.actionBringToFront)
        menu.addAction(mainwindow.actionSendToBack)
        menu.addSeparator()
        menu.addAction(mainwindow.actionNodeProperties)
        return menu

    def buildAttributeNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for attribute nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: AttributeNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuRefactor)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetBrush)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuCompose)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetSpecial)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # SETUP ACTIONS STATE
        for action in mainwindow.actionsSetSpecial:
            action.setChecked(node.special is action.data())
        mainwindow.actionRefactorName.setEnabled(node.special is None)
        return menu

    def buildComplementNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for complement nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: ComplementNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
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
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch[node.identity])
        return menu

    def buildConceptNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for concept nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: ConceptNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuRefactor)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetBrush)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetSpecial)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # SETUP ACTIONS STATE
        for action in mainwindow.actionsSetSpecial:
            action.setChecked(node.special is action.data())
        mainwindow.actionRefactorName.setEnabled(node.special is None)
        return menu

    def buildDatatypeRestrictionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for datatype restriction nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: DatatypeRestrictionNode
        :rtype: QMenu
        """
        return self.buildOperatorNodeMenu(mainwindow, diagram, node)

    def buildDisjointUnionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for disjoint union nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: DisjointUnionNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch)
        return menu

    def buildDomainRestrictionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for domain restriction nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: DomainRestrictionNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.addSeparator()
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetPropertyRestriction)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # SETUP ACTIONS STATE
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity is Identity.Attribute
        qualified = node.qualified
        attribute = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        for action in mainwindow.actionsSetPropertyRestriction:
            action.setChecked(node.restriction is action.data())
            action.setVisible(action.data() is not Restriction.Self or not qualified and not attribute)
        return menu

    def buildEnumerationNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for enumeration nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: EnumerationNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            if node.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge):
                # If we have input edges targeting the node keep only the Enumeration
                # action active: individuals can be connected only to Enumeration nodes
                # and Property Assertion ones, so switching to another operator is an error.
                for action in mainwindow.actionsSwitchOperator:
                    action.setVisible(action.data() is Item.EnumerationNode)
            elif node.outgoingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge):
                # We have inclusion edges attached to this edge but no input => allow
                # switching to operators whose identities set intersects the one of this node.
                switch = {Item.DisjointUnionNode, Item.EnumerationNode, Item.IntersectionNode, Item.UnionNode}
                for action in mainwindow.actionsSwitchOperator:
                    action.setVisible(action.data() in switch)
        return menu

    def buildFacetNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for facet nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: FacetNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetFacet)
        menu.insertSeparator(mainwindow.actionNodeProperties)

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
        for action in mainwindow.actionsSetFacet:
            action.setChecked(action.data() is facet)
            action.setVisible(action.data() in admissible)

        #############################################
        # END CONSTRAIN FACET SWITCH
        #################################

        return menu

    def buildIndividualNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for individual nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: IndividualNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuRefactor)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetBrush)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetIndividualAs)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)

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
        f6 = lambda x: x.identity in {Identity.Attribute, Identity.Role}

        enumeration = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if enumeration:
            num = len(enumeration.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            instance = enumeration.identity is Identity.Concept or num < 2
            value = enumeration.identity is Identity.ValueDomain or num < 2

        assertion = first(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f4))
        if assertion:
            operand = first(assertion.outgoingNodes(filter_on_edges=f5, filter_on_nodes=f6))
            if operand:
                if operand.identity is Identity.Role:
                    value = False
                elif operand.identity is Identity.Attribute:
                    num = len(assertion.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                    instance = instance and (node.identity is Identity.Instance or num < 2)
                    value = value and (node.identity is Identity.Value or num < 2)

        for a in mainwindow.actionsSetIndividualAs:
            a.setVisible(a.data() is Identity.Instance and instance or a.data() is Identity.Value and value)

        #############################################
        # END CONSTRAIN IDENTITY SWITCH
        #################################

        return menu

    def buildIntersectionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for intersection nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: IntersectionNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch)
        return menu

    def buildOperatorNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for operator nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: OperatorNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSwitchOperator)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # RESET ACTIONS STATE
        for action in mainwindow.actionsSwitchOperator:
            action.setChecked(node.type() is action.data())
            action.setVisible(True)
        return menu

    def buildPropertyAssertionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for property assertion nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: PropertyAssertionNode
        :rtype: QMenu
        """
        return self.buildGenericNodeMenu(mainwindow, diagram, node)

    def buildRangeRestrictionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for range restriction nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: RangeRestrictionNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity is Identity.Attribute
        if not first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)):
            menu.addSeparator()
            menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetPropertyRestriction)
            # SETUP ACTIONS STATE
            for action in mainwindow.actionsSetPropertyRestriction:
                action.setChecked(node.restriction is action.data())
                action.setVisible(action.data() is not Restriction.Self)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        return menu

    def buildRoleNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for role nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: RoleNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuRefactor)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetBrush)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuCompose)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetSpecial)
        self.insertLabelSpecificActions(menu, mainwindow, node)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # SETUP ACTIONS STATE
        for action in mainwindow.actionsSetSpecial:
            action.setChecked(node.special is action.data())
        mainwindow.actionRefactorName.setEnabled(node.special is None)
        return menu

    def buildRoleInverseNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for role inverse nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: RoleInverseNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            switch = {Item.ComplementNode, Item.RoleChainNode, Item.RoleInverseNode}
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch)
        return menu

    def buildRoleChainNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for role chain nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: RoleChainNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            f1 = lambda x: x.type() is Item.InputEdge
            switch = {Item.ComplementNode, Item.RoleChainNode, Item.RoleInverseNode}
            if len(node.incomingNodes(filter_on_edges=f1)) > 1:
                switch = {Item.RoleChainNode}
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch)
        return menu

    def buildUnionNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for union nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: UnionNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildOperatorNodeMenu(mainwindow, diagram, node)
        # SETUP ACTIONS STATE
        if node.edges:
            switch = {Item.DisjointUnionNode, Item.IntersectionNode, Item.UnionNode}
            for action in mainwindow.actionsSwitchOperator:
                action.setVisible(action.data() in switch)
        return menu

    def buildValueDomainNodeMenu(self, mainwindow, diagram, node):
        """
        Build and return a QMenu instance for value domain nodes.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type node: ValueDomainNode
        :rtype: QMenu
        """
        # BUILD THE MENU
        menu = self.buildGenericNodeMenu(mainwindow, diagram, node)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetBrush)
        menu.insertMenu(mainwindow.actionNodeProperties, mainwindow.menuSetDatatype)
        menu.insertSeparator(mainwindow.actionNodeProperties)
        # SETUP ACTIONS STATE
        for action in mainwindow.actionsSetDatatype:
            action.setChecked(node.datatype == action.data())
        return menu

    #############################################
    #   LABEL
    #################################

    @staticmethod
    def insertLabelSpecificActions(menu, mainwindow, node):
        """
        Insert label specific actions in the given menu.
        :type menu: QMenu
        :type mainwindow: MainWindow
        :type node: AbstractNode
        """
        if node.label.isMovable() and node.label.isMoved():
            menu.insertSeparator(mainwindow.actionNodeProperties)
            menu.insertAction(mainwindow.actionNodeProperties, mainwindow.actionRelocateLabel)

    #############################################
    #   FACTORY
    #################################

    def create(self, mainwindow, diagram, item, pos=None):
        """
        Build and return a QMenu instance according to the given parameters.
        :type mainwindow: MainWindow
        :type diagram: Diagram
        :type item: AbstractItem
        :type pos: QPointF
        :rtype: QMenu
        """
        if not item:
            return self.buildDiagramMenu(mainwindow, diagram)

        ## NODES
        if item.type() is Item.AttributeNode:
            return self.buildAttributeNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.ComplementNode:
            return self.buildComplementNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.ConceptNode:
            return self.buildConceptNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.DatatypeRestrictionNode:
            return self.buildDatatypeRestrictionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.DisjointUnionNode:
            return self.buildDisjointUnionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.DomainRestrictionNode:
            return self.buildDomainRestrictionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.EnumerationNode:
            return self.buildEnumerationNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.IndividualNode:
            return self.buildIndividualNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.FacetNode:
            return self.buildFacetNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.IntersectionNode:
            return self.buildIntersectionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.PropertyAssertionNode:
            return self.buildPropertyAssertionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.RangeRestrictionNode:
            return self.buildRangeRestrictionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.RoleNode:
            return self.buildRoleNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.RoleInverseNode:
            return self.buildRoleInverseNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.RoleChainNode:
            return self.buildRoleChainNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.UnionNode:
            return self.buildUnionNodeMenu(mainwindow, diagram, item)
        if item.type() is Item.ValueDomainNode:
            return self.buildValueDomainNodeMenu(mainwindow, diagram, item)

        ## EDGES
        if item.type() is Item.InclusionEdge:
            return self.buildInclusionEdgeMenu(mainwindow, diagram, item, pos)
        if item.type() is Item.InputEdge:
            return self.buildInputEdgeMenu(mainwindow, diagram, item, pos)
        if item.type() is Item.MembershipEdge:
            return self.buildMembershipEdgeMenu(mainwindow, diagram, item, pos)

        ## GENERIC
        if item.isNode():
            return self.buildGenericNodeMenu(mainwindow, diagram, item)
        if item.isEdge():
            return self.buildGenericEdgeMenu(mainwindow, diagram, item, pos)

        raise RuntimeError('could not create menu for {0}'.format(item))