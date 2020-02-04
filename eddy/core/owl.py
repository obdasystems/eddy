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
from enum import unique

from PyQt5 import QtCore
from PyQt5 import QtXmlPatterns
from eddy.core.datatypes.owl import Namespace

from eddy.core.datatypes.common import Enum_

from rfc3987 import compose
from rfc3987 import parse
from rfc3987 import resolve

from eddy.core.functions.signals import connect


class AnnotationAssertion(QtCore.QObject):
    """
    Represents Annotation Assertions
    """
    sgnAnnotationModified = QtCore.pyqtSignal()

    def __init__(self, subject, property, value, type=None, language=None, parent=None):
        """
        :type subject:IRI
        :type property:IRI
        :type value:IRI|str
        :type type:IRI
        :type language:str
        """
        super().__init__(parent)
        self._subject = subject
        self._property = property
        if not (isinstance(value, IRI) or isinstance(value, str)):
            raise ValueError('The value of an annotation assertion must be either an IRI or a string')
        self._value = value
        self._datatype = type
        self._language = language

    def isIRIValued(self):
        if isinstance(self.value, IRI):
            return True
        return False

    @property
    def assertionProperty(self):
        return self._property

    @assertionProperty.setter
    def assertionProperty(self, prop):
        if isinstance(prop, IRI):
            self._property = prop
            self.sgnAnnotationModified.emit()

    @property
    def subject(self):
        return self._subject

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, type):
        if isinstance(type, IRI):
            self._datatype = type
            self.sgnAnnotationModified.emit()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        self.sgnAnnotationModified.emit()

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, lang):
        self._language = lang
        self.sgnAnnotationModified.emit()

    def refactor(self,prop,value,type,lang):
        self._property=prop
        self._value=value
        self._datatype=type
        self._language=lang
        self.sgnAnnotationModified.emit()

    def getObjectResourceString(self, manager, prefixedForm):
        """
        Returns a string representing the object resource of the assertion.
        :type manager:IRIManager
        :type prefixedForm:bool
        :rtype: str
        """
        if self._value:
            if isinstance(self._value, IRI):
                prefixedIRI = manager.getShortestPrefixedForm(self._value)
                if prefixedForm and prefixedIRI:
                    return str(prefixedIRI)
                else:
                    return '<{}>'.format(str(self._value))
            elif isinstance(self._value, str):
                result = '"{}"'.format(self._value)
                if self._datatype:
                    prefixedType = manager.getShortestPrefixedForm(self._datatype)
                    if prefixedForm and prefixedType:
                        result += '^^{}'.format(str(prefixedType))
                    else:
                        result += '^^<{}>'.format(self._datatype)
                if self._language:
                    result += ' @{}'.format(self._language)
                return result

    def __hash__(self):
        result = self._property.__hash__()
        if self._value:
            if isinstance(self._value, IRI):
                result+=self._value.__hash__()
            elif isinstance(self._value, str):
                result+=self._value.__hash__()
                if self._datatype:
                    result+=self._datatype.__hash__()
                if self._language:
                    result+=self._language.__hash__()
        return result

    def __eq__(self, other):
        if not isinstance(other, AnnotationAssertion):
            return False
        return self.assertionProperty == other.assertionProperty and self.subject == other.subject and self.value == other.value and self.datatype == other.datatype and self.language == other.value


class IRI(QtCore.QObject):
    """
    Represents International Resource Identifiers (https://www.ietf.org/rfc/rfc3987.txt)
    """

    sgnIRIModified = QtCore.pyqtSignal()
    sgnAnnotationAdded = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationRemoved = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationModified = QtCore.pyqtSignal(AnnotationAssertion)

    def __init__(self, namespace, suffix=None, parent=None):
        """
        Create a new IRI
        """
        super().__init__(parent)
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        self._namespace = str(namespace)
        self._suffix = suffix
        self.components = parse(IRI.concat(self._namespace, self._suffix))
        self._annotationAssertionsMap = {}
        self._annotationAssertions = []

    @staticmethod
    def concat(namespace, suffix):
        if suffix:
            return namespace + suffix
        return namespace

    # @staticmethod
    # def concat(namespace, suffix):
    # if suffix:
    # return namespace + IRI.separator(namespace) + suffix
    # return namespace

    # @staticmethod
    # def separator(iri):
    # return '' if iri[-1] in {'/', '#', ':'} else '#'

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onAnnotationAssertionModified(self):
        annotation = self.sender()
        self.sgnAnnotationModified.emit(annotation)

    # @QtCore.pyqtSlot('IRI')
    def onAnnotationPropertyRemoved(self, iri):
        print("Called onAnnotationPropertyRemoved")
        # TODO se ho annotation assertion che coinvolge iri come PROPERTY RESOURCE (iri!=self), allora elimina assertion dalla lista

    #############################################
    #   PROPERTIES
    #################################
    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        if not IRI.isValidNamespace(value):
            raise IllegalNamespaceError(value)
        self._namespace = value
        self.sgnIRIModified.emit()

    @property
    def annotationAssertions(self):
        return self._annotationAssertions

    @property
    def annotationAssertionMapItems(self):
        return self._annotationAssertionsMap.items()

    @property
    def authority(self):
        """
        Returns the authority component of this `IRI`, i.e. the domain name and port number
        :rtype: str
        """
        return self.components.get('authority')

    @property
    def fragment(self):
        """
        Returns the fragment component of this `IRI`, i.e. anything after query parameters or path component
        :rtype: str
        """
        return self.components.get('fragment')

    @property
    def path(self):
        """
        Returns the path component of this `IRI`, i.e. anything between authority and query components
        :rtype: str
        """
        return self.components.get('path')

    @property
    def query(self):
        """
        Returns the query component of this `IRI`, i.e. anything between path and fragment components
        :rtype: str
        """
        return self.components.get('query')

    @property
    def scheme(self):
        """
        Returns the scheme component of this `IRI`, i.e. anything preceding the :// part of the `IRI`
        :rtype: str
        """
        return self.components.get('scheme')

    #############################################
    #   INTERFACE
    #################################

    def isTopBottomEntity(self):
        """
        Returns True if this iri represents a top/bottom entity, False otherwise
        :rtype: bool
        """
        return TopBottomProperty.isTopBottomEntity(self)

    def getLabelAnnotationAssertion(self, lang=None):
        '''
        :type lang:str
        :rtype AnnotationAssertion
        '''
        return self.getAnnotationAssertion(AnnotationAssertionProperty.Label.value, lang=lang)

    def getAnnotationAssertion(self, annotationProperty, lang=None):
        if annotationProperty in self._annotationAssertionsMap:
            currList = self._annotationAssertionsMap[annotationProperty]
            if lang:
                for annotation in currList:
                    if annotation.language == lang:
                        return annotation
            return currList[0]
        return None

    def addAnnotationAssertion(self, annotation):
        """
        Add an annotation assertion regarding self
        :type: annotation: AnnotationAssertion
        """
        if annotation.assertionProperty in self._annotationAssertionsMap:
            if not annotation in self._annotationAssertionsMap[annotation.assertionProperty]:
                self._annotationAssertionsMap[annotation.assertionProperty].append(annotation)
        else:
            currList = list()
            currList.append(annotation)
            self._annotationAssertionsMap[annotation.assertionProperty] = currList
        self._annotationAssertions.append(annotation)
        self.sgnAnnotationAdded.emit(annotation)
        connect(annotation.sgnAnnotationModified, self.onAnnotationAssertionModified)

    def removeAnnotationAssertion(self, annotation):
        """
        Remove an annotation assertion regarding self
        :type: annotation: AnnotationAssertion
        """
        if annotation.assertionProperty in self._annotationAssertionsMap:
            currList = self._annotationAssertionsMap[annotation.assertionProperty]
            if annotation in currList:
                currList.remove(annotation)
                if len(currList) < 1:
                    self._annotationAssertionsMap.pop(annotation.assertionProperty, None)
                self.sgnAnnotationRemoved.emit(annotation)
            if annotation in self._annotationAssertions:
                self.annotationAssertions.remove(annotation)
        else:
            raise KeyError('Cannot find the annotation assertion')

    def isAbsolute(self):
        """
        Returns `True` if this object represents an absolute IRI, and `False` otherwise
        :rtype: bool
        """
        try:
            return parse(str(self), rule='absolute_IRI') is not None
        except ValueError:
            return False

    def isRelative(self):
        """
        Returns `True if this object represents a relative IRI, and `False` otherwise
        :rtype: bool
        """
        try:
            return parse(str(self), rule='relative_ref') is not None
        except ValueError:
            return False

    def isURI(self):
        """
        Returns `True` if this object represents a valid URI, and `False` otherwise
        :return:
        """
        try:
            return parse(str(self), rule='URI_reference') is not None
        except ValueError:
            return False

    def isValid(self):
        """
        Returns `True` if this object represents a valid IRI, and `False` otherwise
        :rtype: bool
        """
        try:
            return parse(str(self), rule='IRI') is not None
        except ValueError:
            return False

    @staticmethod
    def isValidNamespace(namespace):
        """
        Returns `True` if the given `namespace` is a valid IRI
        :type namespace: str
        :rtype: bool
        """
        try:
            return namespace and (parse(namespace, rule='IRI_reference') is not None)
        except ValueError:
            return False

    def resolve(self, other):
        """
        Resolve `other` against `self`
        :type other: IRI|str
        :rtype: IRI
        """
        if not isinstance(other, IRI):
            other = IRI(other)
        if other.isAbsolute():
            return other
        return IRI(resolve(str(self), str(other)))

    def __eq__(self, other):
        """
        Returns `True` if `self` is equivalent to `other`
        :type other: IRI
        :rtype: bool
        """
        if isinstance(other, IRI):
            return str(self) == str(other)
        return False

    def __getitem__(self, item):
        return str(self)[item]

    def __hash__(self):
        return str(self).__hash__()

    def __iter__(self):
        return str(self).__iter__()

    def __len__(self):
        return len(str(self))

    def __str__(self):
        return compose(**self.components)

    def __repr__(self):
        return str(self)


class PrefixedIRI(QtCore.QObject):
    """
    Represents prefixed forms of International Resource Identifiers (https://www.ietf.org/rfc/rfc3987.txt)
    """

    def __init__(self, prefix, suffix, parent=None):
        super().__init__(parent)
        self._prefix = prefix
        self._suffix = suffix

    @property
    def prefix(self):
        return self._prefix

    @property
    def suffix(self):
        return self._suffix

    def __hash__(self):
        return str(self).__hash__()

    def __str__(self):
        return '{}:{}'.format(self.prefix, self.suffix)

    def __repr__(self):
        return str(self)


class IRIManager(QtCore.QObject):
    """
    A `IRIManager` manages: (i)associations between extended IRIs and their prefixed forms, (ii)the set of IRIs identifying active ontology elements
    """
    sgnPrefixAdded = QtCore.pyqtSignal(str, str)
    sgnPrefixRemoved = QtCore.pyqtSignal(str)
    sgnPrefixModified = QtCore.pyqtSignal(str, str)
    sgnPrefixMapCleared = QtCore.pyqtSignal()

    sgnIRIManagerReset = QtCore.pyqtSignal()

    sgnOntologyIRIModified = QtCore.pyqtSignal(IRI)

    sgnIRIAdded = QtCore.pyqtSignal(IRI)
    sgnIRIRemoved = QtCore.pyqtSignal(IRI)

    sgnAnnotationPropertyAdded = QtCore.pyqtSignal(IRI)
    sgnAnnotationPropertyRemoved = QtCore.pyqtSignal(IRI)

    sgnDatatypeAdded = QtCore.pyqtSignal(IRI)
    sgnDatatypeRemoved = QtCore.pyqtSignal(IRI)

    def __init__(self, parent=None):
        """
        Create a new `IRIManager` with a default set of prefixes defined
        :type parent: QtCore.QObject
        """
        super().__init__(parent)
        self.iris = set()
        self.stringToIRI = {}
        self.prefix2namespaceMap = {}
        self.annotationProperties = set()
        self.datatypes = set()
        self.languages = set()
        self.setDefaults()

    #############################################
    #   LANGUAGES
    #################################
    def addLanguageTag(self,lang):
        """
        Add the language tag identified by lang
        :type lang:str
        """
        self.languages.add(lang)

    def addDefaultLanguages(self):
        self.addLanguageTag('it')
        self.addLanguageTag('en')

    def getLanguages(self):
        return self.languages


    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def setOntologyIRI(self, iriString):
        self.ontologyIRI = self.getIRI(iriString)
        self.sgnOntologyIRIModified.emit(self.ontologyIRI)

    # TODO dovrai poi capire quando un'IRI dovrà essere rimossa (come capire quando non viene più utilizzata in alcun punto???)
    @QtCore.pyqtSlot(IRI)
    def deleteIRI(self, iri):
        """
        Remove the IRI iri from the index
        :type iri: IRI
        """
        # Questo metodo dovrà essere chiamato SOLO quando tutti i riferimenti a iri sono stati eliminati
        self.iris.remove(iri)
        self.stringToIRI.pop(iri, None)
        self.sgnIRIRemoved.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def addIRI(self, iri):
        """
        Add the IRI iri to the index
        :type iri: IRI
        """
        if not iri in self.iris:
            self.iris.add(iri)
            self.stringToIRI[str(iri)] = iri
            self.sgnIRIAdded.emit(iri)

    @QtCore.pyqtSlot(str)
    def getIRI(self, iriString):
        """
        Returns the IRI object identified by iriString. If such object does not exist, creates it and addes to the index
        :type iriString: str
        """
        if iriString in self.stringToIRI:
            return self.stringToIRI[iriString]
        else:
            iri = IRI(iriString)
            self.addIRI(iri)
            connect(self.sgnAnnotationPropertyRemoved, iri.onAnnotationPropertyRemoved)
            return iri

    '''
    @QtCore.pyqtSlot(Diagram, OntologyEntityNode)
    def addIRIOccurenceInDiagram(self,diagram,node):
        """
        Set node as occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: OntologyEntityNode
        """
        iri = node.iri
        if iri in self.iriOccurrences:
            if diagram in self.iriOccurreces[iri]:
                self.iriOccurreces[iri][diagram].add(node)
            else:
                currSet = set()
                currSet.add(node)
                self.iriOccurreces[iri][diagram] = currSet
        else:
            currDict = {}
            currSet = set()
            currSet.add(node)
            currDict[diagram] = currSet
            self.iriOccurreces[iri] = currDict

    @QtCore.pyqtSlot(Diagram, OntologyEntityNode)
    def removeIRIOccurenceInDiagram(self,diagram,node):
        """
        Remove node as occurrence of node.iri in diagram
        :type diagram: Diagram
        :type node: OntologyEntityNode
        """
        iri = node.iri
        if iri in self.iriOccurrences:
            if diagram in self.iriOccurreces[iri]:
                self.iriOccurreces[iri][diagram].remove(node)
                if not self.iriOccurreces[iri][diagram]:
                    self.iriOccurreces[iri].pop(diagram)
    '''

    #############################################
    #   INTERFACE
    #################################

    ##GENERAL
    def reset(self):
        """
        Resets the associations between prefix names and namespaces for this `IRIManager`
        """
        self.iris = set()
        self.stringToIRI = {}
        self.prefix2namespaceMap = {}
        self.sgnIRIManagerReset.emit()
        self.setDefaults()

    def setDefaults(self):
        self.setDefaultPrefixes()
        self.addTopBottomPredicateIRIs()
        self.addDefaultAnnotationProperties()
        self.addDefaultDatatypes()
        self.addDefaultLanguages()

    ##ANNOTATION PROPERTIES
    def getAnnotationPropertyIRIs(self):
        return self.annotationProperties

    def removeAnnotationPropertyIRI(self, iri):
        """
        Remove the IRI iri from the set of IRIs that can be used as Property into annotation assertions
         :type iri: IRI
         """
        if iri in self.annotationProperties:
            self.deleteIRI(iri)
            self.annotationProperties.remove(iri)
            self.sgnAnnotationPropertyRemoved.emit(iri)

    def removeAnnotationProperty(self, iriString):
        """
        Remove the IRI identified by iriString from the set of IRIs that can be used as Property into annotation assertions
        :type iriString: str
        """
        iri = self.getIRI(iriString)
        self.removeAnnotationPropertyIRI(iri)

    def addAnnotationPropertyIRI(self, iri):
        """
        Add the IRI iri to the set of IRIs that can be used as Property into annotation assertions
         :type iri: IRI
         """
        if not iri in self.annotationProperties:
            self.addIRI(iri)
            self.annotationProperties.add(iri)
            self.sgnAnnotationPropertyAdded.emit(iri)
            return True
        return False

    def addAnnotationProperty(self, iriString):
        """
        Add the IRI identified by iriString to the set of IRIs that can be used as Property into annotation assertions
        :type iriString: str
        """
        iri = self.getIRI(iriString)
        return self.addAnnotationPropertyIRI(iri)

    def addDefaultAnnotationProperties(self):
        """
        Initialises this `IRIManager` with a set of property commonly used for annotation assertions(a regime da usare solo per progetto vuoto??)
        """
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.Label.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.BackwardCompatibleWith.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.Deprecated.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.IncompatibleWith.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.PriorVersion.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.VersionInfo.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.Comment.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.IsDefinedBy.value)
        self.addAnnotationPropertyIRI(AnnotationAssertionProperty.seeAlso.value)

    ##DATATYPES
    def getDatatypeIRIs(self):
        return self.datatypes

    def removeDatatypeIRI(self, iri):
        """
        Remove the IRI iri from the set of IRIs that can be used as datatype
         :type iri: IRI
         """
        if iri in self.datatypes:
            self.deleteIRI(iri)
            self.datatypes.remove(iri)
            self.sgnDatatypeRemoved.emit(iri)

    def removeDatatypeProperty(self, iriString):
        """
        Remove the IRI identified by iriString from the set of IRIs that can be used as datatype
        :type iriString: str
        """
        iri = self.getIRI(iriString)
        self.removeDatatypeIRI(iri)

    def addDatatypeIRI(self, iri):
        """
        Add the IRI iri to the set of IRIs that can be used as datatypes
         :type iri: IRI
         """
        if not iri in self.datatypes:
            self.addIRI(iri)
            self.datatypes.add(iri)
            self.sgnDatatypeAdded.emit(iri)
            return True
        return False

    def addDatatype(self, iriString):
        """
        Add the IRI identified by iriString to the set of IRIs that can be used as datatypes
        :type iriString: str
        """
        iri = self.getIRI(iriString)
        return self.addDatatypeIRI(iri)

    def addDefaultDatatypes(self):
        """
        Initialises this `IRIManager` with a set of commonly used datatypes (a regime da usare solo per progetto vuoto??)
        """
        self.addDatatypeIRI(OWL2Datatype.rational.value)
        self.addDatatypeIRI(OWL2Datatype.real.value)
        self.addDatatypeIRI(OWL2Datatype.PlainLiteral.value)
        self.addDatatypeIRI(OWL2Datatype.XMLLiteral.value)
        self.addDatatypeIRI(OWL2Datatype.Literal.value)
        self.addDatatypeIRI(OWL2Datatype.anyURI.value)
        self.addDatatypeIRI(OWL2Datatype.base64Binary.value)
        self.addDatatypeIRI(OWL2Datatype.boolean.value)
        self.addDatatypeIRI(OWL2Datatype.byte.value)
        self.addDatatypeIRI(OWL2Datatype.dateTime.value)
        self.addDatatypeIRI(OWL2Datatype.dateTimeStamp.value)
        self.addDatatypeIRI(OWL2Datatype.decimal.value)
        self.addDatatypeIRI(OWL2Datatype.double.value)
        self.addDatatypeIRI(OWL2Datatype.float.value)
        self.addDatatypeIRI(OWL2Datatype.hexBinary.value)
        self.addDatatypeIRI(OWL2Datatype.int.value)
        self.addDatatypeIRI(OWL2Datatype.integer.value)
        self.addDatatypeIRI(OWL2Datatype.language.value)
        self.addDatatypeIRI(OWL2Datatype.long.value)
        self.addDatatypeIRI(OWL2Datatype.Name.value)
        self.addDatatypeIRI(OWL2Datatype.NCName.value)
        self.addDatatypeIRI(OWL2Datatype.negativeInteger.value)
        self.addDatatypeIRI(OWL2Datatype.NMTOKEN.value)
        self.addDatatypeIRI(OWL2Datatype.nonNegativeInteger.value)
        self.addDatatypeIRI(OWL2Datatype.nonPositiveInteger.value)
        self.addDatatypeIRI(OWL2Datatype.normalizedString.value)
        self.addDatatypeIRI(OWL2Datatype.positiveInteger.value)
        self.addDatatypeIRI(OWL2Datatype.short.value)
        self.addDatatypeIRI(OWL2Datatype.string.value)
        self.addDatatypeIRI(OWL2Datatype.token.value)
        self.addDatatypeIRI(OWL2Datatype.unsignedByte.value)
        self.addDatatypeIRI(OWL2Datatype.unsignedInt.value)
        self.addDatatypeIRI(OWL2Datatype.unsignedLong.value)
        self.addDatatypeIRI(OWL2Datatype.unsignedShort.value)

    def canAddLanguageTagToIRI(self, iri):
        """
        Return true if it's possible to add a language tag to data values having type iri
        :type iri: IRI
        """
        return iri == OWL2Datatype.PlainLiteral.value

    def canAddLanguageTag(self, iriString):
        """
        Return true if it's possible to add a language tag to data values having type IRI(iristring)
        :type iri: str
        """
        return not iriString or self.canAddLanguageTagToIRI(IRI(iriString))

    ##IRIs
    def addTopBottomPredicateIRIs(self):
        self.addIRI(TopBottomProperty.Thing.value)
        self.addIRI(TopBottomProperty.Nothing.value)
        self.addIRI(TopBottomProperty.TopObjectProperty.value)
        self.addIRI(TopBottomProperty.BottomObjectProperty.value)
        self.addIRI(TopBottomProperty.TopDataProperty.value)
        self.addIRI(TopBottomProperty.BottomDataProperty.value)

    def getExpandedIRI(self, prefixedIRI):
        """
        Returns the IRI corresponding to the given short form in `prefixIRI`, or None if no such
        IRI can be computed (i.e. the prefix value for `prefixIRI` is not managed by this `IRIManager`).
        :type prefixedIRI: str
        :rtype: IRI
        """
        if prefixedIRI.find(':') != -1:
            idx = prefixedIRI.find(':')
            prefix = prefixedIRI[:idx]
            suffix = prefixedIRI[idx + 1:]
            namespace = self.getPrefixResolution(prefix)
            if namespace:
                return IRI(namespace, suffix, parent=self)
        return None

    def areSameIRI(self, prefixedIRI, otherPrefixedIRI):
        """
        Check if two prefixed IRIs represent the same element
        :type prefixedIRI: PrefixedIRI
        :type otherPrefixedIRI: PrefixedIRI
        :rtype bool
        """
        if not (isinstance(prefixedIRI, PrefixedIRI) and isinstance(otherPrefixedIRI, PrefixedIRI)):
            return False
        if not prefixedIRI.prefix in self.prefix2namespaceMap:
            raise KeyError('Cannot find prefix {}'.format(prefixedIRI.prefix))
        if not otherPrefixedIRI.prefix in self.prefix2namespaceMap:
            raise KeyError('Cannot find prefix {}'.format(otherPrefixedIRI.prefix))
        ns_1 = self.prefix2namespaceMap[prefixedIRI.prefix]
        iri_1 = IRI(ns_1, suffix=prefixedIRI.suffix, parent=self)
        ns_2 = self.prefix2namespaceMap[otherPrefixedIRI.prefix]
        iri_2 = IRI(ns_2, suffix=otherPrefixedIRI.suffix, parent=self)
        return iri_1 == iri_2

    def getEmptyPrefixResolution(self):
        """
        Returns the string the empty prefix is resolved to, or None if it does not exist
        :rtype: str
        """
        return self.prefix2namespaceMap.get('')

    def getPrefixResolution(self, prefix, fallback=None):
        """
        Returns the extended resolution for `prefix`, or `fallback` if it `prefix` has not been associated with any namespace.
        :type prefix: str
        :type fallback: IRI
        :rtype: IRI
        """
        return self.prefix2namespaceMap.get(prefix, fallback)

    def getMatchingPrefixes(self, iri):
        """
        Returns the prefix name for `namespace` if it exists, or `None` otherwise.
        :type namespace: IRI
        :rtype: dict
        """
        result = {}
        if not isinstance(iri, IRI):
            namespace = IRI(str(iri), parent=self)
        for prefix, value in self.prefix2namespaceMap.items():
            if str(namespace).startswith(value):
                result[prefix] = value
        return result

    def getPrefixedForms(self, iri):
        """
        Returns the prefixed form for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `IRIManager`.
        :type iri: IRI
        :rtype: list
        """
        result = list()
        if not isinstance(iri, IRI):
            iri = IRI(str(iri), parent=self)
        matchingPrefixes = self.getMatchingPrefixes(iri._namespace)
        if matchingPrefixes:
            for prefix, ns in matchingPrefixes.items():
                nsLength = len(ns)
                suffix = str(iri)[nsLength:]
                prefixed = PrefixedIRI(prefix, suffix, self)
                result.append(prefixed)
        return result

    def getShortestPrefixedForm(self, iri):
        """
        Returns the prefixed form with shortest prefix+suffix for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `IRIManager`.
        :type iri: IRI
        :rtype: PrefixedIRI
        """
        matchingList = self.getPrefixedForms(iri)
        result = None
        minLength = -1
        for prefixed in matchingList:
            length = len(prefixed.prefix) + len(prefixed.suffix)
            if minLength < 0 or length < minLength:
                result = prefixed
        return result

    def getShortestPrefixPrefixedForm(self, iri):
        """
        Returns the prefixed form with shortest prefix for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `IRIManager`.
        :type iri: IRI
        :rtype: PrefixedIRI
        """
        matchingList = self.getPrefixedForms(iri)
        result = None
        minPrefixLength = -1
        for prefixed in matchingList:
            prefixLength = len(prefixed.prefix)
            if minPrefixLength < 0 or prefixLength < minPrefixLength:
                minPrefixLength = prefixLength
                result = prefixed
        return result

    def getShortestSuffixPrefixedForm(self, iri):
        """
        Returns the prefixed form with shortest suffix for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `IRIManager`.
        :type iri: IRI
        :rtype: PrefixedIRI
        """
        matchingList = self.getPrefixedForms(iri)
        result = None
        minSuffixLength = -1
        for prefixed in matchingList:
            sufLength = len(prefixed.suffix)
            if minSuffixLength < 0 or sufLength < minSuffixLength:
                minSuffixLength = sufLength
                result = prefixed
        return result

    def getLongestSuffixPrefixedForm(self, iri):
        """
        Returns the prefixed form with longest suffix for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `IRIManager`.
        :type iri: IRI
        :rtype: PrefixedIRI
        """
        matchingList = self.getPrefixedForms(iri)
        result = None
        maxSuffixLength = 0
        for prefixed in matchingList:
            sufLength = len(prefixed.suffix)
            if sufLength > maxSuffixLength:
                maxSuffixLength = sufLength
                result = prefixed
        return result

    def prefixDictItems(self):
        """
        Returns a list of pairs `(prefix, namespace)` managed by this `PrefixManager`.
        :rtype: list
        """
        return self.prefix2namespaceMap.items()

    def getNamespace(self, prefix):
        return self.prefix2namespaceMap[prefix]

    def getManagedPrefixes(self):
        """
        Returns a list of prefix names managed by this `PrefixManager`.
        :rtype: list
        """
        return self.prefix2namespaceMap.keys()

    def setEmptyPrefix(self, namespace):
        """
        Sets the namespace associated to the default empty prefix name
        """
        self.setPrefix('', namespace)

    def setPrefix(self, prefix, namespace):
        """
        Associate `prefix` to `namespace` mapping in this `PrefixManager`
        :type prefix: str
        :type namespace: str|IRI
        """
        if not isinstance(namespace, str):
            namespace = str(namespace, encoding='UTF-8')
        if not isinstance(prefix, str):
            prefix = str(prefix, encoding='UTF-8')
        if prefix and not QtXmlPatterns.QXmlName.isNCName(prefix):
            raise IllegalPrefixError('{0} for namespace: {1}'.format(prefix, namespace))
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        if prefix in self.prefix2namespaceMap:
            self.prefix2namespaceMap[prefix] = namespace
            self.sgnPrefixModified.emit(prefix, namespace)
        else:
            self.prefix2namespaceMap[prefix] = namespace
            self.sgnPrefixAdded.emit(prefix, namespace)

    def setDefaultPrefixes(self):
        """
        Initialises this `PrefixManager` with a set of commonly used prefix names (a regime da usare solo per progetto vuoto)
        """
        self.setPrefix(Namespace.XML.name.lower(), Namespace.XML.value)
        self.setPrefix(Namespace.XSD.name.lower(), Namespace.XSD.value)
        self.setPrefix(Namespace.RDF.name.lower(), Namespace.RDF.value)
        self.setPrefix(Namespace.RDFS.name.lower(), Namespace.RDFS.value)
        self.setPrefix(Namespace.OWL.name.lower(), Namespace.OWL.value)

    def removePrefix(self, prefix):
        """
        Removes and returns the association for `prefix`.
        If `prefix` is not managed in this `PrefixManager`, no action is performed and `None` is returned.
        :type prefix: str
        :rtype: str
        """
        ns = self.prefix2namespaceMap.pop(prefix, None)
        if ns:
            self.sgnPrefixRemoved.emit(prefix)
        return ns

    def clearPrefixes(self):
        """
        Removes all prefix name to namespace associations in this `IRIManager`
        """
        self.prefix2namespaceMap = {}
        self.sgnPrefixMapCleared.emit()

    def unregisterNamespace(self, namespace):
        """
        Unregisters `namespace` from this `IRIManager`.
        :type namespace: IRI
        """
        if not isinstance(namespace, IRI):
            namespace = IRI(namespace)
        for prefix, ns in list(self.prefix2namespaceMap.items()):
            if ns == namespace:
                del self.prefix2namespaceMap[prefix]
                self.sgnPrefixRemoved.emit(prefix)

    def __contains__(self, item):
        return item in self.prefix2namespaceMap

    def __delitem__(self, prefix):
        self.removePrefix(prefix)

    def __eq__(self, other):
        if isinstance(other, IRIManager):
            return self.prefix2namespaceMap == other.prefix2namespaceMap
        return False

    def __getitem__(self, prefix):
        return self.getPrefixResolution(prefix)

    def __hash__(self):
        return self.prefix2namespaceMap.__hash__()

    def __iter__(self):
        for prefix in self.getManagedPrefixes():
            yield prefix

    def __len__(self):
        return len(self.prefix2namespaceMap)

    def __str__(self):
        return '{0}: {1}'.format(self.__class__.__name__, self.prefix2namespaceMap)

    def __repr__(self):
        return str(self)


class IllegalPrefixError(RuntimeError):
    """
    Used to signal that a prefix contains illegal characters
    """
    pass


class IllegalNamespaceError(RuntimeError):
    """
    Used to signal that a namespace contains illegal characters
    """
    pass


@unique
class IRIRender(Enum_):
    """
    Extends Enum providing all the available rendering options for IRIs.
    """
    FULL = 'full_iri'
    PREFIX = 'prefix_iri'
    LABEL = 'label'

@unique
class OWL2Profile(Enum_):
    """
    Extends Enum providing all the available OWL 2 profiles.
    """
    OWL2 = 'OWL 2'
    OWL2EL = 'OWL 2 EL'
    OWL2QL = 'OWL 2 QL'
    OWL2RL = 'OWL 2 RL'


@unique
class OWL2Syntax(Enum_):
    """
    Extends Enum providing all the available OWL 2 syntax for ontology serialization.
    """
    Functional = 'Functional-style syntax'
    Manchester = 'Manchester OWL syntax'
    RDF = 'RDF/XML syntax for OWL'
    Turtle = 'Turtle syntax'


@unique
class TopBottomProperty(Enum_):
    """
    Extends Enum providing all the IRIs identifying the top/bottom predicates
    """
    Thing = IRI(Namespace.OWL.value, 'Thing')
    Nothing = IRI(Namespace.OWL.value, 'Nothing')
    TopObjectProperty = IRI(Namespace.OWL.value, 'topObjectProperty')
    BottomObjectProperty = IRI(Namespace.OWL.value, 'bottomObjectProperty')
    TopDataProperty = IRI(Namespace.OWL.value, 'topDataProperty')
    BottomDataProperty = IRI(Namespace.OWL.value, 'bottomDataProperty')

    def isTopBottomEntity(input):
        return input == TopBottomProperty.Thing.value or input is TopBottomProperty.Nothing.value or input is TopBottomProperty.TopObjectProperty or input is TopBottomProperty.BottomObjectProperty or input is TopBottomProperty.TopDataProperty or input is TopBottomProperty.BottomDataProperty





@unique
class AnnotationAssertionProperty(Enum_):
    """
    Extends Enum providing all the available standard IRIs that can be used as properties in Annotation Assertions
    """
    BackwardCompatibleWith = IRI(Namespace.OWL.value, 'backwardCompatibleWith')
    Deprecated = IRI(Namespace.OWL.value, 'deprecated')
    IncompatibleWith = IRI(Namespace.OWL.value, 'incompatibleWith')
    PriorVersion = IRI(Namespace.OWL.value, 'priorVersion')
    VersionInfo = IRI(Namespace.OWL.value, 'versionInfo')
    Comment = IRI(Namespace.RDFS.value, 'comment')
    IsDefinedBy = IRI(Namespace.RDFS.value, 'isDefinedBy')
    Label = IRI(Namespace.RDFS.value, 'label')
    seeAlso = IRI(Namespace.RDFS.value, 'backwardCompatibleWith')

@unique
class OWL2Datatype(Enum_):
    """
    Extends Enum providing all the IRIs identifying standard available datatypes.
    """
    rational = IRI(Namespace.OWL.value, suffix='rational')
    real = IRI(Namespace.OWL.value, suffix='real')
    PlainLiteral = IRI(Namespace.RDF.value, suffix='PlainLiteral')
    XMLLiteral = IRI(Namespace.RDF.value, suffix='XMLLiteral')
    Literal = IRI(Namespace.RDFS.value, suffix='Literal')
    anyURI = IRI(Namespace.XSD.value, suffix='anyURI')
    base64Binary = IRI(Namespace.XSD.value, suffix='base64Binary')
    boolean = IRI(Namespace.XSD.value, suffix='boolean')
    byte = IRI(Namespace.XSD.value, suffix='byte')
    dateTime = IRI(Namespace.XSD.value, suffix='dateTime')
    dateTimeStamp = IRI(Namespace.XSD.value, suffix='dateTimeStamp')
    decimal = IRI(Namespace.XSD.value, suffix='decimal')
    double = IRI(Namespace.XSD.value, suffix='double')
    float = IRI(Namespace.XSD.value, suffix='float')
    hexBinary = IRI(Namespace.XSD.value, suffix='hexBinary')
    int = IRI(Namespace.XSD.value, suffix='int')
    integer = IRI(Namespace.XSD.value, suffix='integer')
    language = IRI(Namespace.XSD.value, suffix='language')
    long = IRI(Namespace.XSD.value, suffix='long')
    Name = IRI(Namespace.XSD.value, suffix='Name')
    NCName = IRI(Namespace.XSD.value, suffix='NCName')
    negativeInteger = IRI(Namespace.XSD.value, suffix='negativeInteger')
    NMTOKEN = IRI(Namespace.XSD.value, suffix='NMTOKEN')
    nonNegativeInteger = IRI(Namespace.XSD.value, suffix='nonNegativeInteger')
    nonPositiveInteger = IRI(Namespace.XSD.value, suffix='nonPositiveInteger')
    normalizedString = IRI(Namespace.XSD.value, suffix='normalizedString')
    positiveInteger = IRI(Namespace.XSD.value, suffix='positiveInteger')
    short = IRI(Namespace.XSD.value, suffix='short')
    string = IRI(Namespace.XSD.value, suffix='string')
    token = IRI(Namespace.XSD.value, suffix='token')
    unsignedByte = IRI(Namespace.XSD.value, suffix='unsignedByte')
    unsignedInt = IRI(Namespace.XSD.value, suffix='unsignedInt')
    unsignedLong = IRI(Namespace.XSD.value, suffix='unsignedLong')
    unsignedShort = IRI(Namespace.XSD.value, suffix='unsignedShort')

    @classmethod
    def canAddLanguageTag(cls, type):
        if type == OWL2Datatype.PlainLiteral:
            return True
        return False

    @classmethod
    def forProfile(cls, profile):
        """
        Returns the list of supported datatypes for the given OWL 2 profile.
        :type profile: OWLProfile
        :rtype: set
        """
        if profile is OWL2Profile.OWL2:
            return {x for x in OWL2Datatype}
        elif profile is OWL2Profile.OWL2QL:
            return {OWL2Datatype.rational, OWL2Datatype.real, OWL2Datatype.PlainLiteral, OWL2Datatype.XMLLiteral,
                    OWL2Datatype.Literal, OWL2Datatype.anyURI, OWL2Datatype.base64Binary, OWL2Datatype.dateTime,
                    OWL2Datatype.dateTimeStamp, OWL2Datatype.decimal, OWL2Datatype.hexBinary, OWL2Datatype.integer,
                    OWL2Datatype.Name, OWL2Datatype.NCName, OWL2Datatype.NMTOKEN, OWL2Datatype.nonNegativeInteger,
                    OWL2Datatype.normalizedString, OWL2Datatype.string, OWL2Datatype.token}
        elif profile is OWL2Profile.OWL2RL:
            return {OWL2Datatype.PlainLiteral, OWL2Datatype.XMLLiteral, OWL2Datatype.Literal, OWL2Datatype.anyURI,
                    OWL2Datatype.base64Binary, OWL2Datatype.boolean, OWL2Datatype.byte, OWL2Datatype.dateTime,
                    OWL2Datatype.dateTimeStamp, OWL2Datatype.decimal, OWL2Datatype.double, OWL2Datatype.float,
                    OWL2Datatype.hexBinary, OWL2Datatype.Name, OWL2Datatype.NCName, OWL2Datatype.negativeInteger,
                    OWL2Datatype.NMTOKEN, OWL2Datatype.nonNegativeInteger, OWL2Datatype.nonPositiveInteger,
                    OWL2Datatype.normalizedString, OWL2Datatype.positiveInteger, OWL2Datatype.short,
                    OWL2Datatype.string, OWL2Datatype.token, OWL2Datatype.unsignedByte, OWL2Datatype.unsignedInt,
                    OWL2Datatype.unsignedLong, OWL2Datatype.unsignedShort}
        raise ValueError('unsupported profile: %s' % profile)


@unique
class OWL2Facet(Enum_):
    """
    Extends Enum providing all the available OWL2Facet restrictions.
    """
    maxExclusive = IRI(Namespace.XSD.value, suffix='maxExclusive')
    maxInclusive = IRI(Namespace.XSD.value, suffix='maxInclusive')
    minExclusive = IRI(Namespace.XSD.value, suffix='minExclusive')
    minInclusive = IRI(Namespace.XSD.value, suffix='minInclusive')
    langRange = IRI(Namespace.XSD.value, suffix='langRange')
    length = IRI(Namespace.XSD.value, suffix='length')
    maxLength = IRI(Namespace.XSD.value, suffix='maxLength')
    minLength = IRI(Namespace.XSD.value, suffix='minLength')
    pattern = IRI(Namespace.XSD.value, suffix='pattern')

    @classmethod
    def forDatatype(cls, value):
        """
        Returns a collection of Facets for the given datatype
        :type value: OWL2Datatype
        :rtype: list
        """
        allvalues = [x for x in cls]
        numbers = [OWL2Facet.maxExclusive, OWL2Facet.maxInclusive, OWL2Facet.minExclusive, OWL2Facet.minInclusive]
        strings = [OWL2Facet.langRange, OWL2Facet.length, OWL2Facet.maxLength, OWL2Facet.minLength, OWL2Facet.pattern]
        binary = [OWL2Facet.length, OWL2Facet.maxLength, OWL2Facet.minLength]
        anyuri = [OWL2Facet.length, OWL2Facet.maxLength, OWL2Facet.minLength, OWL2Facet.pattern]

        return {
            OWL2Datatype.anyURI: anyuri,
            OWL2Datatype.base64Binary: binary,
            OWL2Datatype.boolean: [],
            OWL2Datatype.byte: numbers,
            OWL2Datatype.dateTime: numbers,
            OWL2Datatype.dateTimeStamp: numbers,
            OWL2Datatype.decimal: numbers,
            OWL2Datatype.double: numbers,
            OWL2Datatype.float: numbers,
            OWL2Datatype.hexBinary: binary,
            OWL2Datatype.int: numbers,
            OWL2Datatype.integer: numbers,
            OWL2Datatype.language: strings,
            OWL2Datatype.Literal: allvalues,
            OWL2Datatype.long: numbers,
            OWL2Datatype.Name: strings,
            OWL2Datatype.NCName: strings,
            OWL2Datatype.negativeInteger: numbers,
            OWL2Datatype.NMTOKEN: strings,
            OWL2Datatype.nonNegativeInteger: numbers,
            OWL2Datatype.nonPositiveInteger: numbers,
            OWL2Datatype.normalizedString: strings,
            OWL2Datatype.PlainLiteral: strings,
            OWL2Datatype.positiveInteger: numbers,
            OWL2Datatype.rational: numbers,
            OWL2Datatype.real: numbers,
            OWL2Datatype.short: numbers,
            OWL2Datatype.string: strings,
            OWL2Datatype.token: strings,
            OWL2Datatype.unsignedByte: numbers,
            OWL2Datatype.unsignedInt: numbers,
            OWL2Datatype.unsignedLong: numbers,
            OWL2Datatype.unsignedShort: numbers,
            OWL2Datatype.XMLLiteral: []
        }[value]
