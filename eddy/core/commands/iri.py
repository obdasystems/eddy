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

from PyQt5 import QtWidgets

from eddy.core.owl import IRI


#############################################
#   AXIOM ANNOTATIONS
#################################

class CommandEdgeAddAnnotation(QtWidgets.QUndoCommand):
    """
    This command is used to set axiom properties.
    """
    def __init__(self, project, edge, ann, name=None):
        """
        Initialize the command.
        :type project: Project
        :type edge: IRI
        :type annAss: Annotation
        :type name: str
        """
        super().__init__(name or 'Add annotation to {0} '.format(str(edge)))
        self._edge = edge
        self._project = project
        self.ann = ann

    def redo(self):
        """redo the command"""
        self._edge.addAnnotation(self.ann)

    def undo(self):
        """undo the command"""
        self._edge.removeAnnotation(self.ann)


class CommandEdgeRemoveAnnotation(QtWidgets.QUndoCommand):
    """
    This command is used to set axiom properties.
    """
    def __init__(self, project, edge, ann, name=None):
        """
        Initialize the command.
        :type project: Project
        :type edge: AxiomEdge
        :type ann: Annotation
        :type name: str
        """
        super().__init__(name or 'Remove annotation from {0} '.format(str(edge)))
        self._edge = edge
        self._project = project
        self._ann = ann

    def redo(self):
        """redo the command"""
        self._edge.removeAnnotation(self._ann)

    def undo(self):
        """undo the command"""
        self._edge.addAnnotation(self._ann)


class CommandEdgeModifyAnnotation(QtWidgets.QUndoCommand):
    """
    This command is used to set axiom properties.
    """
    def __init__(self, project, ann, undo, redo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type ann: Annotation
        :type undo: dict
        :type redo: dict
        :type name: str
        """
        super().__init__(name or 'Modify annotation {} '.format(str(ann)))
        self._project = project
        self._ann = ann
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._ann.refactor(self._redo)

    def undo(self):
        """undo the command"""
        self._ann.refactor(self._undo)


#############################################
#   IRIs
#################################

class CommandChangeIRIIdentifier(QtWidgets.QUndoCommand):
    """
    This command is used to change the namespace identifying an IRI .
    """

    def __init__(self, project, iri, iriRedo, iriUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iri: IRI
        :type iriRedo: str
        :type iriUndo: str
        :type name: str
        """
        super().__init__(name or 'IRI <{}> refactor'.format(iriRedo))
        self._iri = iri
        self._iriRedo = iriRedo
        self._iriUndo = iriUndo
        self._project = project

    def redo(self):
        """redo the command"""
        self._iri.namespace = self._iriRedo

    def undo(self):
        """undo the command"""
        self._iri.namespace = self._iriUndo


class CommandIRIRefactor(QtWidgets.QUndoCommand):
    """
    This command is used to change the IRI associated to (possibly) numerous nodes.
    """

    def __init__(self, project, iriRedo, iriUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iriRedo: IRI
        :type iriUndo: IRI
        :type name: str
        """
        super().__init__(name or 'IRI <{}> refactor'.format(iriRedo))
        self._iriRedo = iriRedo
        self._iriUndo = iriUndo
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.sgnIRIRefactor.emit(self._iriUndo, self._iriRedo)

    def undo(self):
        """undo the command"""
        self._project.sgnIRIRefactor.emit(self._iriRedo, self._iriUndo )


class CommandCommmonSubstringIRIsRefactor(QtWidgets.QUndoCommand):
    """
    This command is used to modify all the IRIs whose identifiers start with a given string.
    """

    def __init__(self, project, startStr, dictIRIs, name=None):
        """
        Initialize the command.
        :type project: Project
        :type startStr: str
        :type dictRedo: dict
        :type name: str
        """
        super().__init__(name or "IRIs starting with '{}' refactor".format(startStr))
        self._dictIRIs = dictIRIs
        self._project = project

    def redo(self):
        """redo the command"""
        for pre,post in self._dictIRIs.items():
            preIRI = self._project.getIRI(pre)
            existPostIRI = self._project.existIRI(post)
            if existPostIRI:
                postIRI = self._project.getIRI(post)
                self._project.sgnIRIRefactor.emit(preIRI, postIRI)
            else:
                preIRI.namespace = post

    def undo(self):
        """undo the command"""
        for pre, post in self._dictIRIs.items():
            postIRI = self._project.getIRI(post)
            existPreIRI = self._project.existIRI(pre)
            if existPreIRI:
                preIRI = self._project.getIRI(pre)
                self._project.sgnIRIRefactor.emit(postIRI, preIRI)
            else:
                postIRI.namespace = pre


#############################################
#   IRI ANNOTATIONS
#################################

class CommandIRIAddAnnotationAssertion(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """
    def __init__(self, project, iri, annAss, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iri: IRI
        :type annAss: AnnotationAssertion
        :type name: str
        """
        super().__init__(name or 'Add annotation to {0} '.format(str(iri)))
        self._iri = iri
        self._project = project
        self._annAss = annAss

    def redo(self):
        """redo the command"""
        self._iri.addAnnotationAssertion(self._annAss)

    def undo(self):
        """undo the command"""
        self._iri.removeAnnotationAssertion(self._annAss)


class CommandIRIRemoveAnnotationAssertion(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """
    def __init__(self, project, iri, annAss, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iri: IRI
        :type annAss: AnnotationAssertion
        :type name: str
        """
        super().__init__(name or 'Remove annotation from {0} '.format(str(iri)))
        self._iri = iri
        self._project = project
        self._annAss = annAss

    def redo(self):
        """redo the command"""
        self._iri.removeAnnotationAssertion(self._annAss)

    def undo(self):
        """undo the command"""
        self._iri.addAnnotationAssertion(self._annAss)


class CommandIRIModifyAnnotationAssertion(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """
    def __init__(self, project,  annAss, undo, redo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type annAss: AnnotationAssertion
        :type undo: dict
        :type redo: dict
        :type name: str
        """
        super().__init__(name or 'Modify annotation {} '.format(str(annAss)))
        self._project = project
        self._annAss = annAss
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._annAss.refactor(self._redo)

    def undo(self):
        """undo the command"""
        self._annAss.refactor(self._undo)


#############################################
#   IRI METAPROPERTIES
#################################

class CommandIRISetMeta(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """
    def __init__(self, project, item, iri, undo, redo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type item: Item
        :type iri: IRI
        :type undo: dict
        :type redo: dict
        :type name: str
        """
        super().__init__(name or 'set {0} meta'.format(str(iri)))
        self._iri = iri
        self._project = project
        self._item = item
        self._undo = undo
        self._redo = redo

    def redo(self):
        """redo the command"""
        self._iri.setMetaProperties(self._redo)
        # TODO l'aggiornamento dei nodi di cui sotto, non dovrebbe essere necessaria (ci dovrebbero pensare direttamente i segnali della classe IRI)
        '''
        for node in self._project.predicates(self._item, self._predicate):
            node.updateNode(selected=node.isSelected())
        '''

    def undo(self):
        """undo the command"""
        self._iri.setMetaProperties(self._undo)
        # TODO l'aggiornamento dei nodi di cui sotto, non dovrebbe essere necessaria (ci dovrebbero pensare direttamente i segnali della classe IRI)
        '''
        for node in self._project.predicates(self._item, self._predicate):
            node.updateNode(selected=node.isSelected())
        '''


#############################################
#   IRI NODES
#################################

class CommandChangeIRIOfNode(QtWidgets.QUndoCommand):
    """
    This command is used to change the IRI associated to a single node.
    """

    def __init__(self, project, node, iriStringRedo, iriStringUndo, userExplicitInput=None, name=None):
        """
        Initialize the command.
        :type project: Project
        :type node: PredicateNodeMixin
        :type iriStringRedo: str
        :type iriStringUndo: str
        :type userExplicitInput: str
        :type name: str
        """
        super().__init__(name or 'Node {} set IRI <{}> '.format(node.id,iriStringRedo))
        self._iriStringRedo = iriStringRedo
        self._iriStringUndo = iriStringUndo
        self._userExplicitInput = userExplicitInput
        self._project = project
        self._node = node

    def redo(self):
        """redo the command"""
        iri = self._project.getIRI(self._iriStringRedo, addLabelFromSimpleName=True, addLabelFromUserInput=True, userInput=self._userExplicitInput)
        oldIri = self._project.getIRI(self._iriStringUndo, addLabelFromSimpleName=True, addLabelFromUserInput=True)
        self._node.iri = iri
        self._project.sgnIRIChanged.emit(self._node, oldIri)

    def undo(self):
        """undo the command"""
        iri = self._project.getIRI(self._iriStringRedo, addLabelFromSimpleName=True, addLabelFromUserInput=True)
        oldIri = self._project.getIRI(self._iriStringUndo, addLabelFromSimpleName=True, addLabelFromUserInput=True)
        self._node.iri = oldIri
        self._project.sgnIRIChanged.emit(self._node, iri)


#############################################
#   FACET NODES
#################################

class CommandChangeFacetOfNode(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """

    def __init__(self, project, node, facetRedo, facetUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type node: FacetNode
        :type facetRedo: Facet
        :type facetUndo: Facet
        :type name: str
        """
        super().__init__(name or 'Node {} modify Facet '.format(node.id))
        self._facetRedo = facetRedo
        self._facetUndo = facetUndo
        self._project = project
        self._node = node

    def redo(self):
        """redo the command"""
        self._node.facet = self._facetRedo
        #self._project.sgnIRIChanged.emit(self._node, oldIri)

    def undo(self):
        """undo the command"""
        self._node.facet = self._facetUndo
        #self._project.sgnIRIChanged.emit(self._node, iri)


#############################################
#   LITERAL NODES
#################################

class CommandChangeLiteralOfNode(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """

    def __init__(self, project, node, literalRedo, literalUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type node: FacetNode
        :type literalRedo: Literal
        :type literalUndo: Literal
        :type name: str
        """
        super().__init__(name or 'Node {} modify Literal '.format(node.id))
        self._literalRedo = literalRedo
        self._literalUndo = literalUndo
        self._project = project
        self._node = node

    def redo(self):
        """redo the command"""
        self._node.literal = self._literalRedo
        #self._project.sgnIRIChanged.emit(self._node, oldIri)

    def undo(self):
        """undo the command"""
        self._node.literal = self._literalUndo
        #self._project.sgnIRIChanged.emit(self._node, iri)
