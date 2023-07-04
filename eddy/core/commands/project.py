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

from eddy.core.datatypes.graphol import Item


class CommandProjectRename(QtWidgets.QUndoCommand):
    """
    Extends QtWidgets.QUndoCommand with facilities to rename the Project.
    """
    def __init__(self, undo, redo, project):
        """
        Initialize the command.
        :type undo: str
        :type redo: str
        :type project: Project
        """
        super().__init__("rename project '{0}' to '{1}'".format(undo, redo))
        self.project = project
        self.undo = undo
        self.redo = redo

    def redo(self):
        """redo the command"""
        self.project.name = self.redo
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.name = self.undo
        self.project.sgnUpdated.emit()


#############################################
#   Ontology IRI
#################################

class CommandProjectSetLabelFromSimpleNameOrInputAndLanguage(QtWidgets.QUndoCommand):
    """
    This command is used to set the IRI identifying the ontology.
    """
    def __init__(self, project, labelFromSimpleNameRedo, labelFromUserInputRedo, languageRedo, snakeConversionRedo, camelConversionRedo, labelFromSimpleNameUndo, labelFromUserInputUndo, languageUndo, snakeConversionUndo, camelConversionUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type labelFromSimpleNameRedo: bool
        :type labelFromUserInputRedo: bool
        :type languageRedo: str
        :type labelFromSimpleNameUndo: bool
        :type labelFromUserInputUndo: bool
        :type languageUndo: str
        :type name: str
        """
        super().__init__(name or 'Set automatic rdfs:label management')
        self._project = project
        self._labelFromSimpleNameRedo = labelFromSimpleNameRedo
        self._labelFromUserInputRedo = labelFromUserInputRedo
        self._languageRedo = languageRedo
        self._snakeConversionRedo = snakeConversionRedo
        self._camelConversionRedo = camelConversionRedo
        self._labelFromSimpleNameUndo = labelFromSimpleNameUndo
        self._labelFromUserInputUndo = labelFromUserInputUndo
        self._languageUndo = languageUndo
        self._snakeConversionUndo = snakeConversionUndo
        self._camelConversionUndo = camelConversionUndo
    def redo(self):
        """redo the command"""
        self._project.addLabelFromSimpleName = self._labelFromSimpleNameRedo
        self._project.addLabelFromUserInput = self._labelFromUserInputRedo
        self._project.defaultLanguage = self._languageRedo
        self._project.convertSnake = self._snakeConversionRedo
        self._project.convertCamel = self._camelConversionRedo

    def undo(self):
        """undo the command"""
        self._project.addLabelFromSimpleName = self._labelFromSimpleNameUndo
        self._project.addLabelFromUserInput = self._labelFromUserInputUndo
        self._project.defaultLanguage = self._languageUndo
        self._project.convertSnake = self._snakeConversionUndo
        self._project.convertCamel = self._camelConversionUndo

class CommandProjectSetOntologyIRIAndVersion(QtWidgets.QUndoCommand):
    """
    This command is used to set the IRI identifying the ontology.
    """
    def __init__(self, project, iriRedo, versionRedo, iriUndo, versionUndo, name=None):
        """
        Initialize the command.
        :type project: Project
        :type iriRedo: str
        :type versionRedo: str
        :type iriUndo: str
        :type versionUndo: str
        :type name: str
        """
        super().__init__(name or 'Set ontology IRI')
        self._project = project
        self._iriRedo = iriRedo
        self._versionRedo = versionRedo
        self._iriUndo = iriUndo
        self._versionUndo = versionUndo

    def redo(self):
        """redo the command"""
        self._project.setOntologyIRI(self._iriRedo)
        self._project.version = self._versionRedo

    def undo(self):
        """undo the command"""
        self._project.setOntologyIRI(self._iriUndo)
        self._project.version = self._versionUndo

#############################################
#   PREFIXES
#################################
class CommandProjectAddPrefix(QtWidgets.QUndoCommand):
    """
    This command is used to add a prefix entry.
    """
    def __init__(self, project, prefix, namespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type name: str
        """
        super().__init__(name or 'Add prefix {0} '.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace

    def redo(self):
        """redo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

    def undo(self):
        """undo the command"""
        self._project.removePrefix(self._prefix)

class CommandProjectRemovePrefix(QtWidgets.QUndoCommand):
    """
    This command is used to remove a prefix entry.
    """
    def __init__(self, project, prefix, namespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type name: str
        """
        super().__init__(name or 'Remove prefix {0} '.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace

    def redo(self):
        """redo the command"""
        self._project.removePrefix(self._prefix)

    def undo(self):
        """undo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

class CommandProjectModifyPrefixResolution(QtWidgets.QUndoCommand):
    """
    This command is used to modify the namespace associated to a prefix.
    """
    def __init__(self, project, prefix, namespace, oldNamespace, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type oldNamespace: str
        :type name: str
        """
        super().__init__(name or 'Modify prefix {0}'.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace
        self._oldNamespace = oldNamespace

    def redo(self):
        """redo the command"""
        self._project.setPrefix(self._prefix,self._namespace)

    def undo(self):
        """undo the command"""
        self._project.setPrefix(self._prefix,self._oldNamespace)

class CommandProjectModifyNamespacePrefix(QtWidgets.QUndoCommand):
    """
    This command is used to modify the prefix associated to a namespace.
    """
    def __init__(self, project, namespace, prefix, oldPrefix, name=None):
        """
        Initialize the command.
        :type project: Project
        :type prefix: str
        :type namespace: str
        :type oldNamespace: str
        :type name: str
        """
        super().__init__(name or 'Modify prefix {0}'.format(prefix))
        self._prefix = prefix
        self._project = project
        self._namespace = namespace
        self._oldPrefix = oldPrefix

    def redo(self):
        """redo the command"""
        self._project.removePrefix(self._oldPrefix)
        self._project.setPrefix(self._prefix,self._namespace)
        if self._project.ontologyPrefix and self._oldPrefix == self._project.ontologyPrefix:
            self._project.ontologyPrefix = self._prefix


    def undo(self):
        """undo the command"""
        self._project.removePrefix(self._prefix)
        self._project.setPrefix(self._oldPrefix,self._namespace)
        if self._project.ontologyPrefix and self._prefix == self._project.ontologyPrefix:
            self._project.ontologyPrefix = self._oldPrefix

#############################################
#   ANNOTATION PROPERTIES
#################################
class CommandProjectAddAnnotationProperty(QtWidgets.QUndoCommand):
    """
    This command is used to add an annotation property entry.
    """
    def __init__(self, project, propIriStr, name=None):
        """
        Initialize the command.
        :type project: Project
        :type propIriStr: str
        :type name: str
        """
        super().__init__(name or 'Add annotation property {0} '.format(propIriStr))
        self._propIriStr = propIriStr
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.addAnnotationProperty(self._propIriStr)

    def undo(self):
        """undo the command"""
        self._project.removeAnnotationProperty(self._propIriStr)

class CommandProjectRemoveAnnotationProperty(QtWidgets.QUndoCommand):
    """
    This command is used to remove an annotation property entry.
    """
    def __init__(self, project, propIriStr, name=None):
        """
        Initialize the command.
        :type project: Project
        :type propIriStr: str
        :type name: str
        """
        super().__init__(name or 'Remove annotation property {0} '.format(propIriStr))
        self._propIriStr = propIriStr
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.removeAnnotationProperty(self._propIriStr)

    def undo(self):
        """undo the command"""
        self._project.addAnnotationProperty(self._propIriStr)

#############################################
#   ONTOLOGY IMPORTS
#################################
class CommandProjectAddOntologyImport(QtWidgets.QUndoCommand):
    """
    This command is used to add an imported ontology entry.
    """
    def __init__(self, project, impOnt, name=None):
        """
        Initialize the command.
        :type project: Project
        :type impOnt: ImportedOntology
        :type name: str
        """
        super().__init__(name or 'Add imported ontology {0} '.format(impOnt.docLocation))
        self._impOnt = impOnt
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.addImportedOntology(self._impOnt)

    def undo(self):
        """undo the command"""
        self._project.removeImportedOntology(self._impOnt)

class CommandProjectRemoveOntologyImport(QtWidgets.QUndoCommand):
    """
    This command is used to remove an imported ontology entry.
    """
    def __init__(self, project, impOnt, name=None):
        """
        Initialize the command.
        :type project: Project
        :type impOnt: ImportedOntology
        :type name: str
        """
        super().__init__(name or 'Add imported ontology {0} '.format(impOnt.docLocation))
        self._impOnt = impOnt
        self._project = project

    def redo(self):
        """redo the command"""
        self._project.removeImportedOntology(self._impOnt)

    def undo(self):
        """undo the command"""
        self._project.addImportedOntology(self._impOnt)



#TODO A REGIME METODI SOTTO CANCELLATI (TUTTI??)



class CommandProjectSetProfile(QtWidgets.QUndoCommand):
    """
    This command is used to set the profile of a project.
    """
    def __init__(self, project, undo, redo):
        """
        Initialize the command.
        :type project: Project
        :type undo: OWLProfile
        :type redo: OWLProfile
        """
        super().__init__("set project profile to '{0}'".format(redo))
        self.project = project
        self.data = {'undo': undo, 'redo': redo}

    def redo(self):
        """redo the command"""
        self.project.profile = self.project.session.createProfile(self.data['redo'], self.project)

        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())

        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()

    def undo(self):
        """undo the command"""
        self.project.profile = self.project.session.createProfile(self.data['undo'], self.project)

        # Reshape all the Role and Attribute nodes to show/hide functionality and inverse functionality.
        for node in self.project.nodes():
            if node.type() in {Item.RoleNode, Item.AttributeNode}:
                node.updateNode(selected=node.isSelected())
                # Emit updated signals.

        # Emit updated signals.
        self.project.session.sgnUpdateState.emit()
        self.project.sgnUpdated.emit()



