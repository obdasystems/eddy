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

from PyQt5 import QtCore
from PyQt5 import QtXmlPatterns

from rfc3987 import compose
from rfc3987 import parse
from rfc3987 import resolve

from eddy.core.datatypes.owl import Namespaces


class IRI(QtCore.QObject):
    """
    Represents International Resource Identifiers (https://www.ietf.org/rfc/rfc3987.txt)
    """
    def __init__(self, namespace, suffix=None, parent=None):
        super().__init__(parent)
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        self.namespace = str(namespace)
        self.suffix = suffix
        self.components = parse(IRI.concat(self.namespace, self.suffix))

    @staticmethod
    def concat(namespace, suffix):
        if suffix:
            return namespace + IRI.separator(namespace) + suffix
        return namespace

    @staticmethod
    def separator(iri):
        return '' if iri[-1] in {'/', '#', ':'} else '#'

    #############################################
    #   PROPERTIES
    #################################

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
            return parse(namespace, rule='IRI_reference') is not None
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


class PrefixManager(QtCore.QObject):
    """
    A `PrefixManager` manages associations between namespaces and prefix names
    """
    def __init__(self, parent=None):
        """
        Create a new `PrefixManager` with a default set of prefixes defined
        :type parent: QtCore.QObject
        """
        super().__init__(parent)
        self.prefix2namespaceMap = {}
        self.setDefaultPrefixes()

    #############################################
    #   INTERFACE
    #################################

    def clear(self):
        """
        Removes all prefix name to namespace associations in this `PrefixManager`
        """
        self.prefix2namespaceMap = {}

    def getDefaultPrefix(self):
        """
        Returns the default namespace associated with this `PrefixManager`, or None if it does not exist
        :rtype: IRI
        """
        return self.prefix2namespaceMap.get('')

    def getIRI(self, prefixIRI):
        """
        Returns the IRI corresponding to the given short form in `prefixIRI`, or None if no such
        IRI can be computed (i.e. the prefix value for `prefixIRI` is not managed by this `PrefixManager`).
        :type prefixIRI: str
        :rtype: IRI
        """
        if prefixIRI.find(':') != -1:
            idx = prefixIRI.find(':')
            prefix = prefixIRI[:idx]
            suffix = prefixIRI[idx + 1:]
            namespace = self.getPrefix(prefix)
            if namespace:
                return IRI(str(namespace), suffix, parent=self)
        return None

    def getPrefix(self, prefix, fallback=None):
        """
        Returns the namespace for `prefix`, or `fallback` if it `prefix` has not been associated with any namespace.
        :type prefix: str
        :type fallback: IRI
        :rtype: IRI
        """
        return self.prefix2namespaceMap.get(prefix, fallback)

    def getPrefixName(self, namespace):
        """
        Returns the prefix name for `namespace` if it exists, or `None` otherwise.
        :type namespace: IRI
        :rtype: str
        """
        if not isinstance(namespace, IRI):
            namespace = IRI(str(namespace), parent=self)
        for prefix in self.prefixes():
            if self.prefix2namespaceMap[prefix] == namespace:
                return prefix
        return None

    def getShortForm(self, iri):
        """
        Returns the short form for `iri`, or None if `iri` doesn't match any of the namespaces
        managed by this `PrefixManager`.
        :type iri: IRI
        :rtype: str
        """
        if not isinstance(iri, IRI):
            iri = IRI(iri)
        prefix = self.getPrefixName(iri.namespace)
        suffix = iri.suffix if iri.suffix else ''
        if prefix is None:
            nsLength = 0
            for p, ns in self.prefix2namespaceMap.items():
                if iri.namespace.startswith(str(ns)) and len(ns) > nsLength:
                    nsLength = len(ns)
                    suffix = str(iri)[nsLength:]
                    prefix = p
        if prefix is not None:
            return prefix + ':' + suffix
        return None

    def items(self):
        """
        Returns a list of pairs `(prefix, namespace)` managed by this `PrefixManager`.
        :rtype: list
        """
        return self.prefix2namespaceMap.items()

    def prefixes(self):
        """
        Returns a list of prefix names managed by this `PrefixManager`.
        :rtype: list
        """
        return self.prefix2namespaceMap.keys()

    def setDefaultPrefix(self, namespace):
        """
        Sets the namespace associated to the default empty prefix name
        """
        self.setPrefix('', namespace)

    def setDefaultPrefixes(self):
        """
        Initialises this `PrefixManager` with a set of commonly used prefix names
        """
        self.setPrefix(Namespaces.XML.name.lower(), Namespaces.XML.value)
        self.setPrefix(Namespaces.XSD.name.lower(), Namespaces.XSD.value)
        self.setPrefix(Namespaces.RDF.name.lower(), Namespaces.RDF.value)
        self.setPrefix(Namespaces.RDFS.name.lower(), Namespaces.RDFS.value)
        self.setPrefix(Namespaces.OWL.name.lower(), Namespaces.OWL.value)

    def setPrefix(self, prefix, namespace):
        """
        Associate `prefix` to `namespace` mapping in this `PrefixManager`
        :type prefix: str
        :type namespace: str|IRI
        """
        if not isinstance(namespace, str):
            namespace = str(namespace)
        if prefix and not QtXmlPatterns.QXmlName.isNCName(prefix):
            raise IllegalPrefixError('{0} for namespace: {1}'.format(prefix, namespace))
        if not IRI.isValidNamespace(namespace):
            raise IllegalNamespaceError(namespace)
        self.prefix2namespaceMap[prefix] = IRI(namespace, parent=self)

    def removePrefix(self, prefix):
        """
        Removes and returns the association for `prefix`.
        If `prefix` is not managed in this `PrefixManager`, no action is performed and `None` is returned.
        :type prefix: str
        :rtype: IRI
        """
        return self.prefix2namespaceMap.pop(prefix, None)

    def reset(self):
        """
        Resets the associations between prefix names and namespaces for this `PrefixManager`
        """
        self.prefix2namespaceMap = {}
        self.setDefaultPrefixes()

    def unregisterNamespace(self, namespace):
        """
        Unregisters `namespace` from this `PrefixManager`.
        :type namespace: IRI
        """
        if not isinstance(namespace, IRI):
            namespace = IRI(namespace)
        for prefix, ns in list(self.prefix2namespaceMap.items()):
            if ns == namespace:
                del self.prefix2namespaceMap[prefix]

    def __contains__(self, item):
        return item in self.prefix2namespaceMap

    def __delitem__(self, prefix):
        self.removePrefix(prefix)

    def __eq__(self, other):
        if isinstance(other, PrefixManager):
            return self.prefix2namespaceMap == other.prefix2namespaceMap
        return False

    def __getitem__(self, prefix):
        return self.getPrefix(prefix)

    def __hash__(self):
        return self.prefix2namespaceMap.__hash__()

    def __iter__(self):
        for prefix in self.prefixes():
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
