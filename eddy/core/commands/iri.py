from PyQt5 import QtWidgets
from eddy.core.functions.signals import connect, disconnect

#############################################
#   IRI ANNOTATIONS
#################################
class CommandIRIAddAnnotation(QtWidgets.QUndoCommand):
    """
    This command is used to set IRI properties.
    """
    def __init__(self, project, iri, annAss, name=None):
        """
        Initialize the command.
        :type project: Project
        :type item: Item
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

class CommandIRIRemoveAnnotation(QtWidgets.QUndoCommand):
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

class CommandIRIModifyAnnotation(QtWidgets.QUndoCommand):
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