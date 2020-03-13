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

K_FUNCTIONAL = 'functional'
K_ASYMMETRIC = 'asymmetric'
K_INVERSE_FUNCTIONAL = 'inverseFunctional'
K_IRREFLEXIVE = 'irreflexive'
K_REFLEXIVE = 'reflexive'
K_SYMMETRIC = 'symmetric'
K_TRANSITIVE = 'transitive'

class Literal(QtCore.QObject):
    """
    Represents Literals
    """
    sgnLiteralModified = QtCore.pyqtSignal()
    def __init__(self, lexicalForm, datatype=None, language=None, parent=None):
        """
        :type lexicalForm:str
        :type datatype:IRI
        :type language:str
        """
        super().__init__(parent)
        self._lexicalForm = lexicalForm
        self._datatype = datatype
        self._language = language

    @property
    def lexicalForm(self):
        return self._lexicalForm

    @lexicalForm.setter
    def lexicalForm(self, lexicalForm):
        if isinstance(lexicalForm, str):
            self._lexicalForm = lexicalForm
            self.sgnLiteralModified.emit()

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, datatype):
        if isinstance(datatype, IRI):
            self._datatype = datatype
            self.sgnLiteralModified.emit()

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        if isinstance(language, str):
            self._language = language
            self.sgnLiteralModified.emit()

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        return self.lexicalForm == other.lexicalForm and self.datatype == other.datatype and self.language == other.language

    def __iter__(self):
        return str(self).__iter__()

    def __len__(self):
        return len(str(self))

    def __str__(self):
        result = ''
        if not self.datatype or (self.datatype and self.datatype is OWL2Datatype.PlainLiteral.value):
            result = '"{}"'.format(self.lexicalForm)
            if self.language:
                result += '@{}'.format(self.language)
        else:
            if self.language:
                result += '"{}@{}"'.format(self.lexicalForm,self.language)
            else:
                result += '"{}"'.format(self.lexicalForm)
            if self.datatype and not self.datatype is OWL2Datatype.PlainLiteral.value:
                prefixedType = self.datatype.manager.getShortestPrefixedForm(self.datatype)
                if prefixedType:
                    result += '^^{}'.format(str(prefixedType))
                else:
                    result += '^^<{}>'.format(self.datatype)
        return result

    def __repr__(self):
        return str(self)

class Facet(QtCore.QObject):
    """
    Represents Annotation Assertions
    """
    sgnFacetModified = QtCore.pyqtSignal()

    def __init__(self, constrainingFacet, literal, parent=None):
        """
        :type constrainingFacet:IRI
        :type literal:Literal
        """
        super().__init__(parent)
        self._constrainingFacet = constrainingFacet
        self._literal = literal

    @property
    def constrainingFacet(self):
        return self._constrainingFacet

    @constrainingFacet.setter
    def constrainingFacet(self, constrainingFacet):
        self._constrainingFacet = constrainingFacet
        self.sgnFacetModified.emit()

    @property
    def literal(self):
        return self._literal

    @literal.setter
    def literal(self, literal):
        self._literal = literal
        self.sgnFacetModified.emit()

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if not isinstance(other, Facet):
            return False
        return self.constrainingFacet == other.constrainingFacet and self.literal == other.literal

    def __str__(self):
        return 'Facet(<{}> {})'.format(self.constrainingFacet,self.literal)

    def __repr__(self):
        return str(self)

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

    def refactor(self,refDict):
        self._property=refDict['assertionProperty']
        self._value=refDict['value']
        self._datatype=refDict['datatype']
        self._language=refDict['language']
        self.sgnAnnotationModified.emit()

    def getObjectResourceString(self, prefixedForm):
        """
        Returns a string representing the object resource of the assertion.
        :type prefixedForm:bool
        :rtype: str
        """
        if self._value:
            if isinstance(self._value, IRI):
                prefixedIRI = self._value.manager.getShortestPrefixedForm(self._value)
                if prefixedForm and prefixedIRI:
                    return str(prefixedIRI)
                else:
                    return '<{}>'.format(str(self._value))
            elif isinstance(self._value, str):
                result = ''
                if not self.datatype or (self.datatype and self.datatype is OWL2Datatype.PlainLiteral.value):
                    result = '"{}"'.format(self.value)
                    if self.language:
                        result += '@{}'.format(self.language)
                else:
                    if self.language:
                        result += '"{}@{}"'.format(self.value, self.language)
                    else:
                        result += '"{}"'.format(self.value)
                    if self.datatype and not self.datatype is OWL2Datatype.PlainLiteral.value:
                        prefixedType = self.datatype.manager.getShortestPrefixedForm(self.datatype)
                        if prefixedType:
                            result += '^^{}'.format(str(prefixedType))
                        else:
                            result += '^^<{}>'.format(self.datatype)
                return result
                '''
                result = ''
                if self._language:
                    result += '"{}@{}"'.format(self._value,self._language)
                else:
                    result = '"{}"'.format(self._value)
                if self._datatype:
                    prefixedType = self._datatype.manager.getShortestPrefixedForm(self._datatype)
                    if prefixedForm and prefixedType:
                        result += '^^{}'.format(str(prefixedType))
                    else:
                        result += '^^<{}>'.format(self._datatype)
                return result
                '''

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

    def __str__(self):
        return 'AnnotationAssertion(<{}> <{}> {})'.format(self.assertionProperty,self.subject,self.getObjectResourceString(True))

    def __repr__(self):
        return str(self)

class IRI(QtCore.QObject):
    """
    Represents International Resource Identifiers (https://www.ietf.org/rfc/rfc3987.txt)
    """

    sgnIRIModified = QtCore.pyqtSignal(str)
    sgnAnnotationAdded = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationRemoved = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationModified = QtCore.pyqtSignal(AnnotationAssertion)

    sgnFunctionalModified = QtCore.pyqtSignal()
    sgnInverseFunctionalModified = QtCore.pyqtSignal()

    def __init__(self, namespace,suffix=None, functional=False, invFuctional=False, symmetric=False, asymmetric=False,reflexive=False,irreflexive=False,transitive=False, parent=None):
        """
        Create a new IRI
        """
        super().__init__(parent)
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        self._namespace = str(namespace)
        self._suffix = suffix
        self._isFunctional = functional
        self._isInverseFunctional = invFuctional
        self._isSymmetric = symmetric
        self._isAsymmetric = asymmetric
        self._isReflexive = reflexive
        self._isIrreflexive = irreflexive
        self._isTransitive = transitive
        self._manager = None
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
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, manager):
        if isinstance(manager,IRIManager):
            self._manager = manager

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        if not IRI.isValidNamespace(value):
            raise IllegalNamespaceError(value)
        oldIRIStr = compose(**self.components)
        self._namespace = value
        self.components = parse(IRI.concat(self._namespace, self._suffix))
        self.sgnIRIModified.emit(oldIRIStr)

    @property
    def functional(self):
        """
        Returns True if the IRI represents a functional (object, data) property,
        False if the IRI represents a non functional (object, data) property,
        None if the IRI does not represent a (object, data) property
        :rtype: bool
        """
        return self._isFunctional

    @functional.setter
    def functional(self, funct):
        self._isFunctional = funct
        self.sgnFunctionalModified.emit()

    @property
    def inverseFunctional(self):
        """
        Returns True if the IRI represents an inverse functional object property,
        False if the IRI represents a non inverse functional object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isInverseFunctional

    @inverseFunctional.setter
    def inverseFunctional(self, invFunct):
        self._isInverseFunctional = invFunct
        self.sgnInverseFunctionalModified.emit()

    @property
    def symmetric(self):
        """
        Returns True if the IRI represents a symmentric object property,
        False if the IRI represents a non symmentric object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isSymmetric

    @symmetric.setter
    def symmetric(self, symm):
        self._isSymmetric = symm

    @property
    def asymmetric(self):
        """
        Returns True if the IRI represents an asymmentric object property,
        False if the IRI represents a non asymmentric object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isAsymmetric

    @asymmetric.setter
    def asymmetric(self, asymm):
        self._isAsymmetric = asymm

    @property
    def reflexive(self):
        """
        Returns True if the IRI represents a reflexive object property,
        False if the IRI represents a non reflexive object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isReflexive

    @reflexive.setter
    def reflexive(self, ref):
        self._isReflexive = ref

    @property
    def irreflexive(self):
        """
        Returns True if the IRI represents a irreflexive object property,
        False if the IRI represents a non irreflexive object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isIrreflexive

    @irreflexive.setter
    def irreflexive(self, irref):
        self._isIrreflexive = irref

    @property
    def transitive(self):
        """
        Returns True if the IRI represents a transitive object property,
        False if the IRI represents a non transitive object property,
        None if the IRI does not represent an object property
        :rtype: bool
        """
        return self._isTransitive

    @transitive.setter
    def transitive(self, tran):
        self._isTransitive = tran

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
    def setMetaProperties(self, metaDict):
        '''
        :type: metaDict: dict
        '''
        for k,v in metaDict.items():
            if k==K_FUNCTIONAL:
                self.functional = v
            if k==K_INVERSE_FUNCTIONAL:
                self.inverseFunctional = v
            if k==K_SYMMETRIC:
                self.symmetric = v
            if k==K_ASYMMETRIC:
                self.asymmetric = v
            if k==K_REFLEXIVE:
                self.reflexive = v
            if k==K_IRREFLEXIVE:
                self.irreflexive = v
            if k==K_TRANSITIVE:
                self.transitive = v

    def getMetaProperties(self):
        """
        :rtype: dict
        """
        result = dict()
        result[K_FUNCTIONAL]=self.functional
        result[K_INVERSE_FUNCTIONAL] = self.inverseFunctional
        result[K_SYMMETRIC] = self.symmetric
        result[K_ASYMMETRIC] = self.asymmetric
        result[K_REFLEXIVE] = self.reflexive
        result[K_IRREFLEXIVE] = self.irreflexive
        result[K_TRANSITIVE] = self.transitive
        return result


    def getSimpleName(self):
        if self._suffix:
            return self._suffix
        index = self.namespace.rfind('#')
        if not index > -1:
            index = self.namespace.rfind('/')
        if index > -1 and self.namespace[index+1:]:
            return self.namespace[index+1:]
        return None

    def isTopBottomEntity(self):
        """
        Returns True if this iri represents a top/bottom entity, False otherwise
        :rtype: bool
        """
        return TopBottomProperty.isTopBottomEntity(self)

    def isOwlThing(self):
        return TopBottomProperty.isTopClass(self)

    def isOwlNothing(self):
        return TopBottomProperty.isBottomClass(self)

    def isTopObjectProperty(self):
        return TopBottomProperty.isTopRole(self)

    def isBottomObjectProperty(self):
        return TopBottomProperty.isBottomRole(self)

    def isTopDataProperty(self):
        return TopBottomProperty.isTopAttribute(self)

    def isBottomDataProperty(self):
        return TopBottomProperty.isBottomAttribute(self)

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
            return self is other
        return False

    def __getitem__(self, item):
        return str(self)[item]

    def __hash__(self):
        return super().__hash__()

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
    sgnPrefixAdded = QtCore.pyqtSignal('QString', 'QString')
    sgnPrefixRemoved = QtCore.pyqtSignal('QString')
    sgnPrefixModified = QtCore.pyqtSignal('QString', 'QString')
    sgnPrefixMapCleared = QtCore.pyqtSignal()

    sgnIRIManagerReset = QtCore.pyqtSignal()

    sgnOntologyIRIModified = QtCore.pyqtSignal(IRI)

    sgnIRIAdded = QtCore.pyqtSignal(IRI)
    sgnIRIRemoved = QtCore.pyqtSignal(IRI)

    sgnAnnotationPropertyAdded = QtCore.pyqtSignal(IRI)
    sgnAnnotationPropertyRemoved = QtCore.pyqtSignal(IRI)

    sgnDatatypeAdded = QtCore.pyqtSignal(IRI)
    sgnDatatypeRemoved = QtCore.pyqtSignal(IRI)

    def __init__(self, parent=None, prefixMap=None, ontologyIRI=None, ontologyPrefix=None, datatypes=None, languages=None, constrFacets=None, annotationProperties=None):
        """
        Create a new `IRIManager` with a default set of prefixes defined
        :type parent: QtCore.QObject
        """
        super().__init__(parent)
        self.iris = set()
        self.stringToIRI = {}
        if not prefixMap:
            self.prefix2namespaceMap = {}
            self.setDefaultPrefixes()
        else:
            self.prefix2namespaceMap = prefixMap
        self.ontologyIRI = None
        if ontologyIRI:
            self.setOntologyIRI(ontologyIRI)
            if not ontologyPrefix is None:
                self.setPrefix(ontologyPrefix,ontologyIRI)
            '''
            else:
                self.setEmptyPrefix(ontologyIRI)
            '''

        self.addTopBottomPredicateIRIs()

        self.annotationProperties = set()
        self.datatypes = set()
        self.languages = set()
        self.constrainingFacets = set()
        self.setDefaults()
        if annotationProperties:
            for annProp in annotationProperties:
                self.addAnnotationProperty(annProp)
        if datatypes:
            for dt in datatypes:
                self.addDatatype(dt)
        if constrFacets:
            for fac in constrFacets:
                self.addConstrainingFacet(fac)
        if languages:
            for lang in languages:
                self.addLanguageTag(lang)

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
        self.addLanguageTag('fr')
        self.addLanguageTag('es')
        self.addLanguageTag('de')

    def getLanguages(self):
        return self.languages


    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def setOntologyIRI(self, iriString):
        newOntIRI = self.getIRI(iriString)
        if self.ontologyIRI and not self.ontologyIRI == newOntIRI:
            for annot in self.ontologyIRI.annotationAssertions:
                newOntIRI.addAnnotationAssertion(annot)
        self.ontologyIRI = newOntIRI
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
        self.stringToIRI.pop(str(iri), None)
        self.sgnIRIRemoved.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def onIRIRemovedFromAllDiagrams(self,iri):
        if not (iri is self.ontologyIRI or iri in self.annotationProperties or iri in self.datatypes):
            self.deleteIRI(iri)

    @QtCore.pyqtSlot(IRI)
    def addIRI(self, iri):
        """
        Add the IRI iri to the index
        :type iri: IRI
        """
        if not iri in self.iris:
            if not iri.manager:
                iri.manager = self
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
            iri.manager = self
            self.addIRI(iri)
            connect(iri.sgnIRIModified,self.onIRIModified)
            connect(self.sgnAnnotationPropertyRemoved, iri.onAnnotationPropertyRemoved)
            return iri

    @QtCore.pyqtSlot(str)
    def onIRIModified(self,oldIRIStr):
        #TODO va testato
        iri = self.sender()
        self.stringToIRI.pop(oldIRIStr,None)
        self.stringToIRI[str(iri)] = iri

    def isValidIdentifier(self, iriStr):
        iri = IRI(iriStr)
        return True

    #############################################
    #   INTERFACE
    #################################
    def existIRI(self,iriString):
        """
        Returns True if there exists an IRI object identified by iriString. Return False otherwise
        :type iriString: str
        :rtype:bool
        """
        if iriString in self.stringToIRI:
            return True
        return False

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
        self.addDefaultAnnotationProperties()
        self.addDefaultDatatypes()
        self.addDefaultLanguages()
        self.addDefaultConstrainingFacets()

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

    def existAnnotationProperty(self, iriStr):
        iri = IRI(iriStr)
        if iri in self.annotationProperties:
            return True
        return False

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

    ##FACETS
    def addConstrainingFacet(self, iriString):
        iri = self.getIRI(iriString)
        return self.addConstrainingFacetIRI(iri)

    def addConstrainingFacetIRI(self, iri):
        if not iri in self.constrainingFacets:
            self.addIRI(iri)
            self.constrainingFacets.add(iri)
            return True
        return False

    def addDefaultConstrainingFacets(self):
        self.addConstrainingFacetIRI(OWL2Facet.langRange.value)
        self.addConstrainingFacetIRI(OWL2Facet.length.value)
        self.addConstrainingFacetIRI(OWL2Facet.maxExclusive.value)
        self.addConstrainingFacetIRI(OWL2Facet.maxInclusive.value)
        self.addConstrainingFacetIRI(OWL2Facet.maxLength.value)
        self.addConstrainingFacetIRI(OWL2Facet.minExclusive.value)
        self.addConstrainingFacetIRI(OWL2Facet.minInclusive.value)
        self.addConstrainingFacetIRI(OWL2Facet.minLength.value)
        self.addConstrainingFacetIRI(OWL2Facet.pattern.value)

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
        return self.areSameIRI(iri,OWL2Datatype.PlainLiteral.value)

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

    def areSameIRI(self, iri, otherIRI):
        """
        Check if two prefixed IRIs represent the same element
        :type iri: IRI|PrefixedIRI
        :type otherIRI: IRI|PrefixedIRI
        :rtype bool
        """
        first = iri
        if isinstance(iri,PrefixedIRI):
            if not iri.prefix in self.prefix2namespaceMap:
                raise KeyError('Cannot find prefix {}'.format(iri.prefix))
            ns = self.prefix2namespaceMap[iri.prefix]
            first = IRI(ns, suffix=iri.suffix, parent=self)
        second = otherIRI
        if isinstance(otherIRI, PrefixedIRI):
            if not otherIRI.prefix in self.prefix2namespaceMap:
                raise KeyError('Cannot find prefix {}'.format(otherIRI.prefix))
            ns = self.prefix2namespaceMap[otherIRI.prefix]
            second = IRI(ns, suffix=otherIRI.suffix, parent=self)
        return str(first) == str(second)

    ##Prefixes
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

    def isValidPrefixEntry(self,prefix, namespace):
        if prefix and not QtXmlPatterns.QXmlName.isNCName(prefix):
            raise IllegalPrefixError('{0} for namespace: {1}'.format(prefix, namespace))
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        return True

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

class IllegalLiteralError(RuntimeError):
    """
    Used to signal that a literal does not respect the structural specifications
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
    SIMPLE_NAME ='simple_name'

@unique
class OWL2Profiles(Enum_):
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

    def isTopClass(input):
        return input == TopBottomProperty.Thing.value

    def isBottomClass(input):
        return input == TopBottomProperty.Nothing.value

    def isTopRole(input):
        return input == TopBottomProperty.TopObjectProperty.value

    def isBottomRole(input):
        return input == TopBottomProperty.BottomObjectProperty.value

    def isTopAttribute(input):
        return input == TopBottomProperty.TopDataProperty.value

    def isBottomAttribute(input):
        return input == TopBottomProperty.BottomDataProperty.value




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
        if profile is OWL2Profiles.OWL2:
            return {x.value for x in OWL2Datatype}
        elif profile is OWL2Profiles.OWL2QL:
            return {OWL2Datatype.rational.value, OWL2Datatype.real.value, OWL2Datatype.PlainLiteral.value, OWL2Datatype.XMLLiteral.value,
                    OWL2Datatype.Literal.value, OWL2Datatype.anyURI.value, OWL2Datatype.base64Binary.value, OWL2Datatype.dateTime.value,
                    OWL2Datatype.dateTimeStamp.value, OWL2Datatype.decimal.value, OWL2Datatype.hexBinary.value, OWL2Datatype.integer.value,
                    OWL2Datatype.Name.value, OWL2Datatype.NCName.value, OWL2Datatype.NMTOKEN.value, OWL2Datatype.nonNegativeInteger.value,
                    OWL2Datatype.normalizedString.value, OWL2Datatype.string.value, OWL2Datatype.token.value}
        elif profile is OWL2Profiles.OWL2RL:
            return {OWL2Datatype.PlainLiteral.value, OWL2Datatype.XMLLiteral.value, OWL2Datatype.Literal.value, OWL2Datatype.anyURI.value,
                    OWL2Datatype.base64Binary.value, OWL2Datatype.boolean.value, OWL2Datatype.byte.value, OWL2Datatype.dateTime.value,
                    OWL2Datatype.dateTimeStamp.value, OWL2Datatype.decimal.value, OWL2Datatype.double.value, OWL2Datatype.float.value,
                    OWL2Datatype.hexBinary.value, OWL2Datatype.Name.value, OWL2Datatype.NCName.value, OWL2Datatype.negativeInteger.value,
                    OWL2Datatype.NMTOKEN.value, OWL2Datatype.nonNegativeInteger.value, OWL2Datatype.nonPositiveInteger.value,
                    OWL2Datatype.normalizedString.value, OWL2Datatype.positiveInteger.value, OWL2Datatype.short.value,
                    OWL2Datatype.string.value, OWL2Datatype.token.value, OWL2Datatype.unsignedByte.value, OWL2Datatype.unsignedInt.value,
                    OWL2Datatype.unsignedLong.value, OWL2Datatype.unsignedShort.value}
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
        :type value: IRI
        :rtype: list
        """
        allvalues = [x for x in cls]
        numbers = [OWL2Facet.maxExclusive.value, OWL2Facet.maxInclusive.value, OWL2Facet.minExclusive.value, OWL2Facet.minInclusive.value]
        strings = [OWL2Facet.langRange.value, OWL2Facet.length.value, OWL2Facet.maxLength.value, OWL2Facet.minLength.value, OWL2Facet.pattern.value]
        binary = [OWL2Facet.length.value, OWL2Facet.maxLength.value, OWL2Facet.minLength.value]
        anyuri = [OWL2Facet.length.value, OWL2Facet.maxLength.value, OWL2Facet.minLength.value, OWL2Facet.pattern.value]

        return {
            OWL2Datatype.anyURI.value: anyuri,
            OWL2Datatype.base64Binary.value: binary,
            OWL2Datatype.boolean.value: [],
            OWL2Datatype.byte.value: numbers.value,
            OWL2Datatype.dateTime.value: numbers,
            OWL2Datatype.dateTimeStamp.value: numbers,
            OWL2Datatype.decimal.value: numbers,
            OWL2Datatype.double.value: numbers,
            OWL2Datatype.float.value: numbers,
            OWL2Datatype.hexBinary.value: binary,
            OWL2Datatype.int.value: numbers,
            OWL2Datatype.integer.value: numbers,
            OWL2Datatype.language.value: strings,
            OWL2Datatype.Literal.value: allvalues,
            OWL2Datatype.long.value: numbers,
            OWL2Datatype.Name.value: strings,
            OWL2Datatype.NCName.value: strings,
            OWL2Datatype.negativeInteger.value: numbers,
            OWL2Datatype.NMTOKEN.value: strings,
            OWL2Datatype.nonNegativeInteger.value: numbers,
            OWL2Datatype.nonPositiveInteger.value: numbers,
            OWL2Datatype.normalizedString.value: strings,
            OWL2Datatype.PlainLiteral.value: strings,
            OWL2Datatype.positiveInteger.value: numbers,
            OWL2Datatype.rational.value: numbers,
            OWL2Datatype.real.value: numbers,
            OWL2Datatype.short.value: numbers,
            OWL2Datatype.string.value: strings,
            OWL2Datatype.token.value: strings,
            OWL2Datatype.unsignedByte.value: numbers,
            OWL2Datatype.unsignedInt.value: numbers,
            OWL2Datatype.unsignedLong.value: numbers,
            OWL2Datatype.unsignedShort.value: numbers,
            OWL2Datatype.XMLLiteral.value: []
        }[value]
