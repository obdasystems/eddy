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

from __future__ import annotations

from abc import (
    ABCMeta,
    abstractmethod,
)
from enum import unique
from typing import (
    List,
    Optional,
    cast,
)

from PyQt5 import (
    QtCore,
    QtNetwork,
)
from rdflib import (
    BNode,
    Graph,
    IdentifiedNode,
    Literal,
    URIRef,
)

from eddy.core.datatypes.common import IntEnum_

# Graph instance used to keep track of namespaces
K_GRAPH = Graph(bind_namespaces='none')


class RepositoryMonitor(QtCore.QObject):
    """
    This class can be used to listen for changes in the saved repository list.
    """
    sgnUpdated = QtCore.pyqtSignal()
    _instance = None

    def __new__(cls):
        """
        Implements the singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


K_REPO_MONITOR = RepositoryMonitor()


@unique
class MetadataRequest(IntEnum_):
    """
    This class defines the attributes used in metadata REST requests.
    """
    RepositoryAttribute = QtNetwork.QNetworkRequest.Attribute(7001)


class Repository:
    """
    A repository of metadata as a RESTful API endpoint.
    """

    def __init__(self, name: str, uri: URIRef | str):
        """Initialize the repository instance."""
        self._name = name
        self._uri = uri
        # TODO: Authentication mechanims will be added later

    @property
    def name(self):
        """Returns the repository name."""
        return self._name

    @property
    def uri(self):
        """Returns the repository uri."""
        return self._uri

    #############################################
    # INTERFACE
    #################################

    @classmethod
    def load(cls) -> List[Repository]:
        """Load the repositories list from user preferences."""
        repos = []  # type: List[Repository]
        settings = QtCore.QSettings()
        for index in range(settings.beginReadArray('metadata/repositories')):
            settings.setArrayIndex(index)
            repos.append(Repository(
                name=settings.value('name'),
                uri=settings.value('uri'),
            ))
        return repos

    @classmethod
    def save(cls, repositories: List[Repository]) -> None:
        """Save the repository in the user preferences."""
        settings = QtCore.QSettings()
        settings.beginWriteArray('metadata/repositories')
        for index, repo in enumerate(repositories):
            settings.setArrayIndex(index)
            settings.setValue('name', repo.name)
            settings.setValue('uri', repo.uri)
        settings.endArray()
        K_REPO_MONITOR.sgnUpdated.emit()


class Node(metaclass=ABCMeta):
    """
    Base class for any API object.
    """

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict, **kwargs: dict) -> Node:
        """Creates a new node from the given dict."""
        pass

    @abstractmethod
    def to_dict(self, deep: bool = False) -> dict:
        """Serializes the object to a dict."""
        pass

    @abstractmethod
    def n3(self) -> str:
        """Returns the N-TRIPLES (n3) representation of the object."""
        pass


class Entity(Node, metaclass=ABCMeta):
    """
    Base class for any named or unnamed entity.
    """

    def __init__(self, id_: str) -> None:
        """Initialize the entity."""
        super().__init__()
        self._id = id_
        self._types = []
        self._annotations = []

    @property
    def id(self) -> str:
        """Return the identifier for this entity."""
        return self._id

    @property
    @abstractmethod
    def name(self) -> IdentifiedNode:
        """Return the IRI or BNode for this entity."""
        pass

    @property
    def types(self) -> List[NamedEntity]:
        """Return the list of types of this entity."""
        return self._types

    @property
    def annotations(self) -> List[Annotation]:
        """Return the list of annotations of this entity."""
        return self._annotations

    def __eq__(self, other: Entity) -> bool:
        return self.__class__ == other.__class__ and self.id == other.id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class NamedEntity(Entity):
    """
    Represents entities that are uniquely identified with an IRI.
    """

    def __init__(self, id_: str, iri: URIRef | str) -> None:
        """Initialize the named entity."""
        super().__init__(id_)
        self._iri = iri if isinstance(iri, URIRef) else URIRef(iri)

    @property
    def iri(self) -> URIRef:
        """Return the iri associated with this named entity."""
        return self._iri

    @property
    def name(self) -> IdentifiedNode:
        return self.iri

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> Node:
        ent = NamedEntity(data["id"], data["iri"])  # noqa
        if "types" in data:
            for t in data["types"]:
                ent.types.append(cast(NamedEntity, NamedEntity.from_dict(t)))
        if "annotations" in data:
            for a in data["annotations"]:
                ant = cast(Annotation, Annotation.from_dict(a, subject=ent.to_dict()))
                ent.annotations.append(ant)
        return ent

    def to_dict(self, deep: bool = False) -> dict:
        res = {
            "id": self.id,
            "iri": self.name,
        }
        if deep:
            res |= {
                "types": [t.to_dict() for t in self.types],
                "annotations": [a.to_dict() for a in self.annotations],
            }
        return res

    def n3(self) -> str:
        return self.iri.n3(K_GRAPH.namespace_manager)

    def __eq__(self, other: Entity) -> bool:
        return super().__eq__(other) and self.iri == cast(NamedEntity, other).iri

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}, \"{self.iri}\")"


class AnonymousEntity(Entity):
    """
    Represents entities not identified by an IRI (i.e. blank nodes in RDF).
    """

    def __init__(self, id_: str, bnode: BNode | str) -> None:
        """Initialize the anonymous entity."""
        super().__init__(id_)
        self._bnode = bnode if isinstance(bnode, BNode) else BNode(bnode)

    @property
    def bnode(self) -> BNode:
        """Returns the blank node associated with this entity."""
        return self._bnode

    @property
    def name(self) -> IdentifiedNode:
        return self.bnode

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> Node:
        ent = NamedEntity(data["id"], data["bnode"])  # noqa
        if "types" in data:
            for t in data["types"]:
                ent.types.append(cast(NamedEntity, NamedEntity.from_dict(t)))
        if "annotations" in data:
            for a in data["annotations"]:
                ent.annotations.append(
                    cast(Annotation, Annotation.from_dict(a, subject=ent.to_dict())))
        return ent

    def to_dict(self, deep: bool = False) -> dict:
        res = {
            "id": self.id,
            "bnode": self.name,
        }
        if deep:
            res |= {
                "types": [t.to_dict() for t in self.types],
                "annotations": [a.to_dict() for a in self.annotations],
            }
        return res

    def n3(self) -> str:
        return self.bnode.n3(K_GRAPH.namespace_manager)

    def __eq__(self, other: Entity) -> bool:
        return super().__eq__(other) and self.bnode == cast(AnonymousEntity, other).bnode

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id}, \"{self.bnode}\")"


class LiteralValue(Node):
    """
    Represent a literal value associated with an annotation assertion.
    """

    def __init__(self, value: str, language: Optional[str] = None,
                 datatype: Optional[URIRef | str] = None) -> None:
        """Initialize the literal."""
        super().__init__()
        self._value = value
        self._language = language
        self._datatype = datatype
        # Check that literal is well-formed
        if self._language is not None and self._datatype is not None:
            raise ValueError("Literals with a datatype cannot have a language tag.")

    @property
    def value(self) -> str:
        """Return the value of this literal."""
        return self._value

    @property
    def language(self) -> Optional[str]:
        """Return the language tag of this literal, or `None` if there is no tag."""
        return self._language

    @property
    def datatype(self) -> Optional[URIRef | str]:
        """Return the datatype of this literal, or `None` if there is no datatype."""
        return self._datatype

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> Node:
        return cls(data["value"], data["language"], data["datatype"])  # noqa

    def to_dict(self, deep: bool = False) -> dict:
        return {
            "value": self.value,
            "language": self.language,
            "datatype": self.datatype
        }

    def n3(self) -> str:
        return Literal(self.value, self.language, self.datatype).n3(K_GRAPH.namespace_manager)

    def __eq__(self, other: Entity) -> bool:
        return (
            super().__eq__(other)
            and self.value == cast(LiteralValue, other).value
            and self.language == cast(LiteralValue, other).language
            and self.datatype == cast(LiteralValue, other).datatype
        )

    def __repr__(self) -> str:
        if self.language:
            return f"{self.__class__.__name__}(\"{self.value}\"@{self.language})"
        else:
            return f"{self.__class__.__name__}(\"{self.value}\"^^{self.datatype})"


class Annotation(Node):
    """
    Represent an annotation assertion.
    """

    def __init__(self, subject: Entity, predicate: NamedEntity, object: Node) -> None:
        """Initialize the annotation."""
        self._subject = subject
        self._predicate = predicate
        self._object = object

    @property
    def subject(self) -> Entity:
        """Return the annotation subject."""
        return self._subject

    @property
    def predicate(self) -> NamedEntity:
        """Return the annotation predicate."""
        return self._predicate

    @property
    def object(self) -> Node:
        """Return the annotation object."""
        return self._object

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> Node:
        s = kwargs["subject"]
        p = data["property"]
        v = data["value"]

        sub = NamedEntity.from_dict(s) if "iri" in s else AnonymousEntity.from_dict(s)
        prop = NamedEntity.from_dict(p)

        if "id" in v:
            obj = NamedEntity.from_dict(v) if "iri" in v else AnonymousEntity.from_dict(v)
        else:
            obj = LiteralValue.from_dict(v)

        return Annotation(cast(Entity, sub), cast(NamedEntity, prop), obj)

    def to_dict(self, deep: bool = False) -> dict:
        return {
            "property": self.predicate.to_dict(),
            "value": self.object.to_dict()
        }

    def n3(self) -> str:
        sub = self.subject.n3()
        pred = self.predicate.n3()
        obj = self.object.n3()
        return f'{sub} {pred} {obj}'

    def __eq__(self, other: Annotation) -> bool:
        return (
            self.__class__ == other.__class__
            and self.subject == other.subject
            and self.predicate == other.predicate
            and self.object == other.object
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.subject}, {self.predicate}, {self.object})"
