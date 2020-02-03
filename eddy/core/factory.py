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


from operator import attrgetter

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMenu

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.datatypes.owl import Datatype, Facet, OWLProfile, Namespace
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect
from eddy.ui.description import NodeDescriptionDialog
from eddy.ui.properties import DiagramProperty
from eddy.ui.properties import FacetNodeProperty
from eddy.ui.properties import NodeProperty
from eddy.ui.properties import OrderedInputNodeProperty
from eddy.ui.properties import PredicateNodeProperty
from eddy.ui.properties import ValueDomainNodeProperty
from eddy.ui.properties import ValueNodeProperty


class MenuFactory(QtCore.QObject):
    """
    This class can be used to produce diagram items contextual menus.
    """

    def __init__(self, session):
        """
        Initialize the factory.
        :type session: Session
        """
        super().__init__(session)
        self.customAction = {}
        self.customMenu = {}
        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')

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
        menu = QtWidgets.QMenu()
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
        menu = QtWidgets.QMenu()
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
        menu = QtWidgets.QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.action('remove_breakpoint')
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
        menu = QtWidgets.QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.action('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
        return menu

    def buildSameEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for same edges.
        :type diagram: Diagram
        :type edge: SameEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QtWidgets.QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.action('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
            menu.addAction(self.session.action('switch_same_to_different'))
        return menu

    def buildDifferentEdgeMenu(self, diagram, edge, pos):
        """
        Build and return a QMenu instance for different edges.
        :type diagram: Diagram
        :type edge: DifferentEdge
        :type pos: QPointF
        :rtype: QMenu
        """
        menu = QtWidgets.QMenu()
        breakpoint = edge.breakPointAt(pos)
        if breakpoint is not None:
            action = self.session.action('remove_breakpoint')
            action.setData((edge, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.session.action('delete'))
            menu.addAction(self.session.action('switch_different_to_same'))
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
        menu = QtWidgets.QMenu()
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
        menu.addSeparator()
        return menu

    def buildPredicateNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for a predicate node (CONCEPT, ROLE, ATTRIBUTE).
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)

        # BUILD CUSTOM ACTIONS FOR PREDICATE OCCURRENCES
        self.customAction['occurrences'] = []

        for pnode in self.project.predicates(node.type(), node.text()):
            action = QtWidgets.QAction(self.session)
            action.setCheckable(True)
            action.setChecked(pnode is node)
            action.setData(pnode)
            action.setText('{} ({})'.format(pnode.diagram.name, pnode.id))
            connect(action.triggered, self.session.doLookupOccurrence)
            self.customAction['occurrences'].append(action)

        # BUILD CUSTOM MENU FOR PREDICATE OCCURRENCES
        self.customMenu['occurrences'] = QtWidgets.QMenu('Occurrences')
        self.customMenu['occurrences'].setIcon(QtGui.QIcon(':/icons/24/ic_visibility_black'))
        for action in sorted(self.customAction['occurrences'], key=lambda x: x.text()):
            self.customMenu['occurrences'].addAction(action)
        menu.insertMenu(self.session.action('node_properties'), self.customMenu['occurrences'])
        # ADD DESCRIPTION LINK TO THE MENU OF PREDICATE NODE
        menu.addAction(self.session.action('node_description'))

        if node.special() is None:
            self.customAction['change_prefix'] = []
            self.customAction['refactor_change_prefix'] = []

            for iri in self.project.IRI_prefixes_nodes_dict.keys():
                prefixes_raw = self.project.IRI_prefixes_nodes_dict[iri][0]
                prefixes = prefixes_raw[:]

                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                    prefixes.append(':')
                for p in prefixes:
                    pr_node = self.project.get_prefix_of_node(node)

                    action = QtWidgets.QAction(self.session)
                    action.setCheckable(True)
                    action.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    action.setData(node)
                    action.setText('{}'.format(p))
                    connect(action.triggered, self.session.setprefix)
                    self.customAction['change_prefix'].append(action)

                    refactorAction = QtWidgets.QAction(self.session)
                    refactorAction.setCheckable(True)
                    refactorAction.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    refactorAction.setData(node)
                    refactorAction.setText('{}'.format(p))
                    connect(refactorAction.triggered, self.session.refactorsetprefix)
                    self.customAction['refactor_change_prefix'].append(refactorAction)

            self.customMenu['change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['change_prefix']:
                self.customMenu['change_prefix'].addAction(action)

            menu.insertMenu(self.session.action('node_properties'),
                            self.customMenu['change_prefix'])
            self.customMenu['refactor_change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['refactor_change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['refactor_change_prefix']:
                self.customMenu['refactor_change_prefix'].addAction(action)

            self.session.menu('refactor').insertMenu(self.session.action('node_properties'),
                                                     self.customMenu['refactor_change_prefix'])
        return menu

    def buildAttributeNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for attribute nodes.
        :type diagram: Diagram
        :type node: AttributeNode
        :rtype: QMenu
        """
        menu = self.buildPredicateNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('compose_attribute'))
        if self.project.profile.type() is not OWLProfile.OWL2RL:
            menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special() is None)
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
            switch = {Item.ComplementNode}
            if node.identity() in {Identity.Concept, Identity.ValueDomain}:
                switch.add(Item.DisjointUnionNode)
                switch.add(Item.IntersectionNode)
                switch.add(Item.UnionNode)
            elif node.identity() is Identity.Role:
                switch.add(Item.RoleInverseNode)
                if not node.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InclusionEdge):
                    switch.add(Item.RoleChainNode)
            elif node.identity() is Identity.Neutral:
                switch.add(Item.DisjointUnionNode)
                switch.add(Item.EnumerationNode)
                switch.add(Item.IntersectionNode)
                switch.add(Item.RoleChainNode)
                switch.add(Item.RoleInverseNode)
                switch.add(Item.UnionNode)
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.isVisible() and action.data() in switch)
        return menu

    def buildConceptNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for concept nodes.
        :type diagram: Diagram
        :type node: ConceptNode
        :rtype: QMenu
        """
        menu = self.buildPredicateNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special() is None)
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
                action.setVisible(action.isVisible() and action.data() in switch)
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
        qualified = node.isRestrictionQualified()
        attribute = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        for action in self.session.action('restriction').actions():
            action.setChecked(node.restriction() is action.data())
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
                    action.setVisible(action.isVisible() and action.data() is Item.EnumerationNode)
            elif node.outgoingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge):
                # We have inclusion edges attached to this edge but no input => allow
                # switching to operators whose identities set intersects the one of this node.
                switch = {Item.DisjointUnionNode, Item.EnumerationNode, Item.IntersectionNode, Item.UnionNode}
                for action in self.session.action('switch_operator').actions():
                    action.setVisible(action.isVisible() and action.data() in switch)
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

        self.customAction['occurrences'] = []

        for pnode in self.project.predicates(node.type(), node.text()):
            action = QtWidgets.QAction(self.session)
            action.setCheckable(True)
            action.setChecked(pnode is node)
            action.setData(pnode)
            action.setText('{} ({})'.format(pnode.diagram.name, pnode.id))
            connect(action.triggered, self.session.doLookupOccurrence)
            self.customAction['occurrences'].append(action)

        # BUILD CUSTOM MENU FOR PREDICATE OCCURRENCES
        self.customMenu['occurrences'] = QtWidgets.QMenu('Occurrences')
        self.customMenu['occurrences'].setIcon(QtGui.QIcon(':/icons/24/ic_visibility_black'))
        for action in sorted(self.customAction['occurrences'], key=lambda x: x.text()):
            self.customMenu['occurrences'].addAction(action)
        menu.insertMenu(self.session.action('node_properties'), self.customMenu['occurrences'])

        ############################
        # CHANGE PREFIX
        ############################

        if node.value is None:
            self.customAction['change_prefix'] = []
            self.customAction['refactor_change_prefix'] = []

            for iri in self.project.IRI_prefixes_nodes_dict.keys():
                prefixes_raw = self.project.IRI_prefixes_nodes_dict[iri][0]
                prefixes = prefixes_raw[:]

                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                    prefixes.append(':')

                for p in prefixes:
                    if Namespace.forPrefix(p):
                        continue

                    pr_node = self.project.get_prefix_of_node(node)

                    action = QtWidgets.QAction(self.session)
                    action.setCheckable(True)
                    action.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    action.setData(node)
                    action.setText('{}'.format(p))
                    connect(action.triggered, self.session.setprefix)
                    self.customAction['change_prefix'].append(action)

                    refactorAction = QtWidgets.QAction(self.session)
                    refactorAction.setCheckable(True)
                    refactorAction.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    refactorAction.setData(node)
                    refactorAction.setText('{}'.format(p))
                    connect(refactorAction.triggered, self.session.refactorsetprefix)
                    self.customAction['refactor_change_prefix'].append(refactorAction)

            self.customMenu['change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['change_prefix']:
                self.customMenu['change_prefix'].addAction(action)

            menu.insertMenu(self.session.action('node_properties'), self.customMenu['change_prefix'])

            self.customMenu['refactor_change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['refactor_change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['refactor_change_prefix']:
                self.customMenu['refactor_change_prefix'].addAction(action)

            self.session.menu('refactor').insertMenu(self.session.action('node_properties'),
                                                     self.customMenu['refactor_change_prefix'])

        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_individual'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        menu.insertSeparator(self.session.action('node_description'))

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
            value = value and node is not first(assertion.inputNodes())
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
                action.setVisible(action.isVisible() and action.data() in switch)
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
        # Initialize switch action set.
        for action in self.session.action('switch_operator').actions():
            action.setChecked(node.type() is action.data())
            action.setVisible(True)
        # Add OWL 2 QL switch constraints.
        if self.project.profile.type() is OWLProfile.OWL2QL:
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() not in {Item.DatatypeRestrictionNode,
                                                        Item.DisjointUnionNode, Item.EnumerationNode,
                                                        Item.RoleChainNode,
                                                        Item.UnionNode})
        # Add OWL 2 RL switch constraints.
        if self.project.profile.type() is OWLProfile.OWL2RL:
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.data() is not Item.DatatypeRestrictionNode)

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
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.identity() is Identity.Attribute
        f3 = lambda x: x.type() is Item.InclusionEdge
        f4 = lambda x: x.identity() is Identity.ValueDomain
        attribute_in_input = first(node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        valuedomain_in_isa = first(node.outgoingNodes(filter_on_edges=f3, filter_on_nodes=f4))
        menu = self.buildGenericNodeMenu(diagram, node)
        menu.addSeparator()
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('switch_restriction'))
        for action in self.session.action('switch_restriction').actions():
            action.setChecked(node.type() is action.data())
            action.setVisible(node.type() is action.data() or not attribute_in_input and not valuedomain_in_isa)
        if not attribute_in_input and not valuedomain_in_isa:
            qualified = node.isRestrictionQualified()
            menu.insertMenu(self.session.action('node_properties'), self.session.menu('property_restriction'))
            for action in self.session.action('restriction').actions():
                action.setChecked(node.restriction() is action.data())
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
        menu = self.buildPredicateNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('compose_role'))
        if self.project.profile.type() is not OWLProfile.OWL2RL:
            menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        menu.insertAction(self.session.action('node_properties'), self.session.action('invert_role'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special() is None)
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
            f1 = lambda x: x.type() is Item.InputEdge
            f2 = lambda x: x.type() is Item.InclusionEdge
            f3 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
            switch = {Item.RoleInverseNode}
            if not node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f3):
                switch.add(Item.ComplementNode)
            if not node.outgoingNodes(filter_on_edges=f1) and not node.incomingNodes(filter_on_edges=f2):
                switch.add(Item.RoleChainNode)
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.isVisible() and action.data() in switch)
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
            switch = {Item.RoleChainNode}
            if len(node.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge)) <= 1:
                switch.add(Item.ComplementNode)
                switch.add(Item.RoleInverseNode)
            for action in self.session.action('switch_operator').actions():
                action.setVisible(action.isVisible() and action.data() in switch)
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
                action.setVisible(action.isVisible() and action.data() in switch)
        return menu

    def buildValueDomainNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for value domain nodes.
        :type diagram: Diagram
        :type node: ValueDomainNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)
        # CREATE A NEW MENU FOR DATATYPE SELECTION NOT TO OVERWRITE THE PRE-DEFINED ONE
        self.customMenu['datatype'] = QtWidgets.QMenu('Select type')
        self.customMenu['datatype'].setIcon(self.session.menu('datatype').icon())
        # CREATE NEW CUSTOM ACTION SET FOR THE DATATYPES SUPPORTED BY THE CURRENT PROFILE
        self.customAction['datatype'] = []
        for datatype in sorted(Datatype.forProfile(self.project.profile.type()), key=attrgetter('value')):
            action = QtWidgets.QAction(self.session)
            action.setCheckable(True)
            action.setData(datatype)
            action.setText(datatype.value)
            connect(action.triggered, self.session.doSetDatatype)
            self.customAction['datatype'].append(action)
            self.customMenu['datatype'].addAction(action)
        # INSERT THE CUSTOM MENU IN THE NODE CONTEXTUAL MENU
        menu.insertMenu(self.session.action('node_properties'), self.customMenu['datatype'])
        menu.insertSeparator(self.session.action('node_properties'))
        for action in self.customAction['datatype']:
            action.setChecked(node.datatype == action.data())
        return menu

    #############################################
    #   IRI
    #################################

    # TODO
    def buildIRIPredicateNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for a predicate node having an associated IRI object (CONCEPT, ROLE, ATTRIBUTE).
        :type diagram: Diagram
        :type node: OntologyEntityNode
        :rtype: QMenu
        """
        menu = self.buildGenericNodeMenu(diagram, node)

        # BUILD CUSTOM ACTIONS FOR PREDICATE OCCURRENCES
        self.customAction['occurrences'] = []

        for pnode in self.project.iriOccurrences(node.iri):

            action = QtWidgets.QAction(self.session)
            action.setCheckable(True)

            action.setChecked(pnode is node)
            action.setData(pnode)
            action.setText('{} ({})'.format(pnode.diagram.name, pnode.id))

            if pnode.type() is Item.ConceptIRINode:
                action.setIcon(self.iconConcept)
            elif pnode.type() is Item.RoleIRINode:
                action.setIcon(self.iconRole)
            elif pnode.type() is Item.AttributeIRINode:
                action.setIcon(self.iconAttribute)
            elif pnode.type() is Item.IndividualIRINode:
                action.setIcon(self.iconInstance)
            connect(action.triggered, self.session.doLookupOccurrence)
            self.customAction['occurrences'].append(action)

        # BUILD CUSTOM MENU FOR PREDICATE OCCURRENCES
        self.customMenu['occurrences'] = QtWidgets.QMenu('Occurrences')
        self.customMenu['occurrences'].setIcon(QtGui.QIcon(':/icons/24/ic_visibility_black'))
        for action in sorted(self.customAction['occurrences'], key=lambda x: x.text()):
            self.customMenu['occurrences'].addAction(action)
        menu.insertMenu(self.session.action('node_properties'), self.customMenu['occurrences'])
        # ADD DESCRIPTION LINK TO THE MENU OF PREDICATE NODE
        menu.addAction(self.session.action('node_description'))

        # TODO node.special() ritorna "True" se è nodo con IRI dal reserved vocabulary (Thing, Nothing....)
        # TODO Devi aggiungere implementazione per oggetti con IRI (parti da enumerazione IRI riservate
        if not node.iri.isTopBottomEntity():
            print('The selected node is neither top nor bottom')
        else:
            print('The selected node is either top or bottom')

        if node.special() is None:
            '''
            self.customAction['change_prefix'] = []
            self.customAction['refactor_change_prefix'] = []

            for iri in self.project.IRI_prefixes_nodes_dict.keys():
                prefixes_raw = self.project.IRI_prefixes_nodes_dict[iri][0]
                prefixes = prefixes_raw[:]

                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                    prefixes.append(':')
                for p in prefixes:
                    pr_node = self.project.get_prefix_of_node(node)

                    action = QtWidgets.QAction(self.session)
                    action.setCheckable(True)
                    action.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    action.setData(node)
                    action.setText('{}'.format(p))
                    connect(action.triggered, self.session.setprefix)
                    self.customAction['change_prefix'].append(action)

                    refactorAction = QtWidgets.QAction(self.session)
                    refactorAction.setCheckable(True)
                    refactorAction.setChecked((pr_node is p) or ((pr_node is '') and (p is ':')))
                    refactorAction.setData(node)
                    refactorAction.setText('{}'.format(p))
                    connect(refactorAction.triggered, self.session.refactorsetprefix)
                    self.customAction['refactor_change_prefix'].append(refactorAction)

            self.customMenu['change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['change_prefix']:
                self.customMenu['change_prefix'].addAction(action)

            menu.insertMenu(self.session.action('node_properties'),
                            self.customMenu['change_prefix'])
            self.customMenu['refactor_change_prefix'] = QtWidgets.QMenu('Change prefix')
            self.customMenu['refactor_change_prefix'].setIcon(QtGui.QIcon(':/icons/24/ic_settings_ethernet_black'))

            for action in self.customAction['refactor_change_prefix']:
                self.customMenu['refactor_change_prefix'].addAction(action)
            
            self.session.menu('refactor').insertMenu(self.session.action('node_properties'),
                                                     self.customMenu['refactor_change_prefix'])
                                                     '''
        return menu

    # TODO
    def buildIRIConceptNodeMenu(self, diagram, node):
        """
        Build and return a QMenu instance for concept IRI nodes.
        :type diagram: Diagram
        :type node: ConceptNode
        :rtype: QMenu
        """
        menu = self.buildIRIPredicateNodeMenu(diagram, node)
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('refactor'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('brush'))
        menu.insertMenu(self.session.action('node_properties'), self.session.menu('special'))
        self.insertLabelActions(menu, node)
        menu.insertSeparator(self.session.action('node_properties'))
        self.session.action('refactor_name').setEnabled(node.special() is None)
        return menu

    #############################################
    #   LABEL
    #################################

    def insertLabelActions(self, menu, node):
        """
        Insert label specific actions in the given menu.
        :type menu: QtWidgets.QMenu
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

        ##IRI NODES
        if item.type() is Item.ConceptIRINode:
            return self.buildIRIConceptNodeMenu(diagram, item)

        ## EDGES
        if item.type() is Item.InclusionEdge:
            return self.buildGenericEdgeMenu(diagram, item, pos)
        if item.type() is Item.InputEdge:
            return self.buildGenericEdgeMenu(diagram, item, pos)
        if item.type() is Item.MembershipEdge:
            return self.buildMembershipEdgeMenu(diagram, item, pos)
        if item.type() is Item.EquivalenceEdge:
            return self.buildGenericEdgeMenu(diagram, item, pos)
        if item.type() is Item.SameEdge:
            return self.buildSameEdgeMenu(diagram, item, pos)
        if item.type() is Item.DifferentEdge:
            return self.buildDifferentEdgeMenu(diagram, item, pos)

        ## GENERIC
        if item.isNode():
            return self.buildGenericNodeMenu(diagram, item)
        if item.isEdge():
            return self.buildGenericEdgeMenu(diagram, item, pos)

        raise RuntimeError('could not create menu for {0}'.format(item))


class PropertyFactory(QtCore.QObject):
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


class DescriptionFactory(QtCore.QObject):
    """
    This class can be used to produce description dialog windows.
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
        Returns the project loaded in the active session (alias for DescriptionFactory.session.project).
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the active session (alias for DescriptionFactory.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def create(self, diagram, node=None):
        """
        Build and return a description dialog according to the given parameters.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: QDialog
        """
        description = NodeDescriptionDialog(diagram, node, self.session)
        description.setFixedSize(description.sizeHint())
        return description
