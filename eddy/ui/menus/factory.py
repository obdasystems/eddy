# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMenu

from eddy.core.datatypes import Item, Identity, Restriction
from eddy.core.items import EnumerationNode, DisjointUnionNode, IntersectionNode
from eddy.core.items import RoleChainNode, RoleInverseNode, UnionNode, ComplementNode


class MenuFactory(QObject):
    """
    This class can be used to produce DiagramScene items menus.
    """
    def __init__(self, parent=None):
        """
        Initialize the factory.
        :type parent: QObject
        """
        super().__init__(parent)

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def buildDiagramSceneMenu(mainwindow, scene):
        """
        Build and return a QMenu instance for the DiagramScene.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :rtype: QMenu
        """
        menu = QMenu()
        if not mainwindow.clipboard.empty():
            menu.addAction(mainwindow.actionPaste)
        menu.addAction(mainwindow.actionSelectAll)
        menu.addSeparator()
        menu.addAction(mainwindow.actionOpenSceneProperties)
        return menu

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def buildGenericEdgeMenu(mainwindow, scene, edge, pos):
        """
        Build and return a QMenu instance for a generic edge.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
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
    def buildInclusionEdgeMenu(mainwindow, scene, edge, pos):
        """
        Build and return a QMenu instance for Inclusion edges.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
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
            menu.addAction(mainwindow.actionDelete)
            menu.addAction(mainwindow.actionSwapEdge)
            menu.addSeparator()
            menu.addAction(mainwindow.actionToggleEdgeComplete)
            mainwindow.actionSwapEdge.setVisible(scene.validator.valid(edge.target, edge, edge.source))
            mainwindow.actionToggleEdgeComplete.setChecked(edge.complete)
        return menu

    @staticmethod
    def buildInputEdgeMenu(mainwindow, scene, edge, pos):
        """
        Build and return a QMenu instance for Input edges.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
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
            menu.addAction(mainwindow.actionDelete)
            menu.addAction(mainwindow.actionSwapEdge)
            menu.addSeparator()
            menu.addAction(mainwindow.actionToggleEdgeFunctional)
            mainwindow.actionSwapEdge.setVisible(scene.validator.valid(edge.target, edge, edge.source))
            mainwindow.actionToggleEdgeFunctional.setChecked(edge.functional)
        return menu

    @staticmethod
    def buildInstanceOfEdgeMenu(mainwindow, scene, edge, pos):
        """
        Build and return a QMenu instance for InstanceOf edges.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type edge: InstanceOfEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = edge.breakpointAt(pos)
        mainwindow = scene.mainwindow
        if breakpoint is not None:
            action = mainwindow.actionRemoveEdgeBreakpoint
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(mainwindow.actionDelete)
        return menu

    ####################################################################################################################
    #                                                                                                                  #
    #   NODES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def buildGenericNodeMenu( mainwindow, scene, node):
        """
        Build and return a QMenu instance for a generic node.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
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
        menu.addAction(mainwindow.actionOpenNodeProperties)
        return menu

    def buildAttributeNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for attribute nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: AttributeNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeRefactor)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeCompose)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeSpecial)

        for action in mainwindow.actionsNodeSetSpecial:
            action.setChecked(node.special is action.data())

        mainwindow.actionRefactorName.setEnabled(node.special is None)
        mainwindow.actionComposeInverseFunctional.setEnabled(False)

        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildComplementNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for complement nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: ComplementNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)

        if node.edges:

            switch = {ComplementNode}
            if self.identity is Identity.Role:
                switch |= {RoleChainNode, RoleInverseNode}
            else:
                switch |= {DisjointUnionNode, IntersectionNode, UnionNode}

            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in switch)

        return menu

    def buildConceptNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for concept nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: ConceptNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeRefactor)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeSpecial)

        # Switch the check on the currently active special.
        for action in mainwindow.actionsNodeSetSpecial:
            action.setChecked(node.special is action.data())

        # Disable refactor name if special type is set.
        mainwindow.actionRefactorName.setEnabled(node.special is None)

        # Append label specific actions.
        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildDatatypeRestrictionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for datatype restriction nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: DatatypeRestrictionNode
        :rtype: QMenu
        """
        return self.buildOperatorNodeMenu(mainwindow, scene, node)

    def buildDisjointUnionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for disjoint union nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: DisjointUnionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)
        if node.edges:
            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in {DisjointUnionNode, IntersectionNode, UnionNode})
        return menu

    def buildDomainRestrictionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for domain restriction nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: DomainRestrictionNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.addSeparator()
        menu.insertMenu(scene.mainwindow.actionOpenNodeProperties, scene.mainwindow.menuRestrictionChange)

        f1 = lambda x: x.isItem(Item.InputEdge)
        f2 = lambda x: x.identity is Identity.Attribute

        qualified = node.qualified
        attribute = next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

        # Switch the currently active restriction and hide invalid ones.
        for action in scene.mainwindow.actionsRestrictionChange:
            action.setChecked(node.restriction is action.data())
            action.setVisible(action.data() is not Restriction.Self or not qualified and not attribute)

        # Append label specific actions.
        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(scene.mainwindow.actionOpenNodeProperties)
        return menu

    def buildEnumerationNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for enumeration nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: EnumerationNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)

        if node.edges:

            if [e for e in node.edges if e.isItem(Item.InputEdge) and e.target is node]:
                # If we have input edges targeting the node keep only the Enumeration action
                # active: individuals can be connected only to Enumeration nodes and Link, so
                # switching to another operator would be an error.
                for action in mainwindow.actionsSwitchOperatorNode:
                    action.setVisible(action.data() is EnumerationNode)
            elif [e for e in node.edges if e.isItem(Item.InclusionEdge)]:
                # We have inclusion edges attached to this edge but no input => allow switching to
                # operators that can be identified using the identities declared by this very node.
                for action in mainwindow.actionsSwitchOperatorNode:
                    action.setVisible(action.data() in {DisjointUnionNode, EnumerationNode, IntersectionNode, UnionNode})

        return menu

    def buildIndividualNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for individual nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: IndividualNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeRefactor)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuSetIndividualNodeAs)

        ##################################
        ## BEGIN CONSTRAIN IDENTITY SWITCH
        ##################################

        I = True
        L = True

        f1 = lambda x: x.isItem(Item.InputEdge)
        f2 = lambda x: x.isItem(Item.EnumerationNode)
        f3 = lambda x: x.isItem(Item.IndividualNode)
        f4 = lambda x: x.isItem(Item.PropertyAssertionNode)
        f5 = lambda x: x.isItem(Item.InstanceOfEdge)
        f6 = lambda x: x.identity in {Identity.Attribute, Identity.Role}

        enumeration = next(iter(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None)

        if enumeration:
            num = len(enumeration.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            I = enumeration.identity is Identity.Concept or num < 2
            L = enumeration.identity is Identity.DataRange or num < 2

        assertion = next(iter(node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f4)), None)
        if assertion:
            operand = next(iter(assertion.outgoingNodes(filter_on_edges=f5, filter_on_nodes=f6)), None)
            if operand:
                if operand.identity is Identity.Role:
                    L = False
                elif operand.identity is Identity.Attribute:
                    num = len(assertion.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
                    I = I and (node.identity is Identity.Individual or num < 2)
                    L = L and (node.identity is Identity.Literal or num < 2)

        for a in mainwindow.actionsSetIndividualNodeAs:
            a.setVisible(a.data() is Identity.Individual and I or a.data() is Identity.Literal and L)

        ################################
        ## END CONSTRAIN IDENTITY SWITCH
        ################################

        # Append label specific actions.
        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildIntersectionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for intersection nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: IntersectionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)
        if node.edges:
            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in {DisjointUnionNode, IntersectionNode, UnionNode})
        return menu

    def buildOperatorNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for operator nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: OperatorNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuOperatorNodeSwitch)

        # Check the currently active operator type.
        for action in mainwindow.actionsSwitchOperatorNode:
            action.setChecked(isinstance(node, action.data()))
            action.setVisible(True)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildPropertyAssertionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for property assertion nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: PropertyAssertionNode
        :rtype: QMenu
        """
        return self.buildGenericNodeMenu(mainwindow, scene, node)

    def buildRangeRestrictionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for range restriction nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: RangeRestrictionNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)

        f1 = lambda x: x.isItem(Item.InputEdge)
        f2 = lambda x: x.identity is Identity.Attribute

        # Allow to change the restriction type only if it's not an Attribute range restriction
        if not next(iter(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)), None):
            menu.addSeparator()
            menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuRestrictionChange)
            for action in mainwindow.actionsRestrictionChange:
                action.setChecked(node.restriction is action.data())
                action.setVisible(action.data() is not Restriction.Self)

        # Append label specific actions.
        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildRoleNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for role nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: RoleNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeRefactor)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeCompose)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeSpecial)

        for action in mainwindow.actionsNodeSetSpecial:
            action.setChecked(node.special is action.data())

        mainwindow.actionRefactorName.setEnabled(node.special is None)
        mainwindow.actionComposeInverseFunctional.setEnabled(True)

        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    def buildRoleInverseNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for role inverse nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: RoleInverseNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)
        if node.edges:
            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in {ComplementNode, RoleChainNode, RoleInverseNode})
        return menu

    def buildRoleChainNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for role chain nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: RoleChainNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)

        if node.edges:

            switch = {ComplementNode, RoleChainNode, RoleInverseNode}
            if len([e for e in node.edges if e.isItem(Item.InputEdge) and e.target is node]) > 1:
                switch = {RoleChainNode}
            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in switch)

        return menu

    def buildUnionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for union nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: UnionNode
        :rtype: QMenu
        """
        menu = self.buildOperatorNodeMenu(mainwindow, scene, node)
        if node.edges:
            for action in mainwindow.actionsSwitchOperatorNode:
                action.setVisible(action.data() in {DisjointUnionNode, IntersectionNode, UnionNode})
        return menu

    def buildValueDomainNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for value domain nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: ValueDomainNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuChangeValueDomainDatatype)
        menu.insertSeparator(mainwindow.actionOpenNodeProperties)

        # Switch the check matching the current datatype.
        for action in mainwindow.actionsChangeValueDomainDatatype:
            action.setChecked(node.datatype == action.data())

        return menu

    def buildValueRestrictionNodeMenu(self, mainwindow, scene, node):
        """
        Build and return a QMenu instance for value restriction nodes.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: ValueRestrictionNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(mainwindow, scene, node)
        menu.insertMenu(mainwindow.actionOpenNodeProperties, mainwindow.menuNodeChangeBrush)
        menu.insertAction(mainwindow.actionOpenNodeProperties, mainwindow.actionChangeValueRestriction)

        # Append label specific actions.
        collection = self.buildNodeLabelSpecificActionSet(mainwindow, scene, node)
        if collection:
            menu.insertSeparator(mainwindow.actionOpenNodeProperties)
            for action in collection:
                menu.insertAction(mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(mainwindow.actionOpenNodeProperties)
        return menu

    ####################################################################################################################
    #                                                                                                                  #
    #   LABELS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def buildNodeLabelSpecificActionSet(mainwindow, scene, node):
        """
        Build and return a collection of actions for the given node label
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type node: AbstractNode
        :rtype: list
        """
        collection = []
        if node.label.movable and node.label.moved:
            collection.append(mainwindow.actionResetTextPosition)
        return collection

    ####################################################################################################################
    #                                                                                                                  #
    #   FACTORY                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def create(self, mainwindow, scene, item, pos=None):
        """
        Build and return a QMenu instance according to the given parameters.
        :type mainwindow: MainWindow
        :type scene: DiagramScene
        :type item: AbstractItem
        :type pos: QPointF
        :rtype: QMenu
        """
        if not item:
            return self.buildDiagramSceneMenu(mainwindow, scene)

        ## NODES
        if item.isItem(Item.AttributeNode):
            return self.buildAttributeNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.ComplementNode):
            return self.buildComplementNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.ConceptNode):
            return self.buildConceptNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.DatatypeRestrictionNode):
            return self.buildDatatypeRestrictionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.DisjointUnionNode):
            return self.buildDisjointUnionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.DomainRestrictionNode):
            return self.buildDomainRestrictionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.EnumerationNode):
            return self.buildEnumerationNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.IndividualNode):
            return self.buildIndividualNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.IntersectionNode):
            return self.buildIntersectionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.PropertyAssertionNode):
            return self.buildPropertyAssertionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.RangeRestrictionNode):
            return self.buildRangeRestrictionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.RoleNode):
            return self.buildRoleNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.RoleInverseNode):
            return self.buildRoleInverseNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.RoleChainNode):
            return self.buildRoleChainNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.UnionNode):
            return self.buildUnionNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.ValueDomainNode):
            return self.buildValueDomainNodeMenu(mainwindow, scene, item)
        if item.isItem(Item.ValueRestrictionNode):
            return self.buildValueRestrictionNodeMenu(mainwindow, scene, item)

        ## EDGES
        if item.isItem(Item.InclusionEdge):
            return self.buildInclusionEdgeMenu(mainwindow, scene, item, pos)
        if item.isItem(Item.InputEdge):
            return self.buildInputEdgeMenu(mainwindow, scene, item, pos)
        if item.isItem(Item.InstanceOfEdge):
            return self.buildInstanceOfEdgeMenu(mainwindow, scene, item, pos)

        ## GENERIC
        if item.node:
            return self.buildGenericNodeMenu(mainwindow, scene, item)
        if item.edge:
            return self.buildGenericEdgeMenu(mainwindow, scene, item, pos)

        raise RuntimeError('could not create menu for {}'.format(item))