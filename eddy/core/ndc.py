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


from dataclasses import dataclass
from textwrap import dedent
from typing import (
    ClassVar,
    Iterable,
    Optional,
    Union,
)

from rdflib import (
    Dataset,
    Graph,
    Literal,
    URIRef,
)
from rdflib.namespace import (
    FOAF,
    DCAT,
    DCTERMS,
    RDF,
    DefinedNamespace,
    Namespace,
)
from rdflib.store import Store

from eddy.core.functions.fsystem import fexists
from eddy.core.functions.path import expandPath


# Subset of the l0 ontology vocabulary
class L0(DefinedNamespace):
    name: URIRef
    _NS = Namespace('https://w3id.org/italia/onto/l0/')


# Subset of the ADMS ontology vocabulary
class ADMS(DefinedNamespace):
    Project: URIRef
    SemanticAssetDistribution: URIRef
    hasKeyClass: URIRef
    hasSemanticAssetDistribution: URIRef
    officialURI: URIRef
    prefix: URIRef
    semanticAssetInUse: URIRef
    _NS = Namespace('https://w3id.org/italia/onto/ADMS/')


# Subset of the dcatapit ontology vocabulary
class DCATAPIT(DefinedNamespace):
    Agent: URIRef
    Organization: URIRef
    _NS = Namespace('http://dati.gov.it/onto/dcatapit#')


# Subset of the vcard ontology vocabulary
class VCARD(DefinedNamespace):
    Kind: URIRef
    fn: URIRef
    hasEmail: URIRef
    hasTelephone: URIRef
    Organization: URIRef
    _NS = Namespace('http://www.w3.org/2006/vcard/ns#')


@dataclass
class Agent:
    type: ClassVar[URIRef] = FOAF.Agent
    uri: URIRef
    name_en: Optional[Literal]
    name_it: Optional[Literal]
    identifier: Optional[Literal]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, Agent.type),
            (self.uri, RDF.type, DCATAPIT.Agent),
            (self.uri, FOAF.name, self.name_en),
            (self.uri, FOAF.name, self.name_it),
            (self.uri, DCTERMS.identifier, self.identifier),
        ]

    @staticmethod
    def bgp(uri: Optional[URIRef] = None) -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :param uri: optional uri of the element to filter for
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{ {f'BIND( {uri.n3()} AS ?agent)' if uri else ''}
            ?agent a {Agent.type.n3()} .
            OPTIONAL {{
                ?agent {FOAF.name.n3()} ?name_en .
                FILTER langMatches(lang(?name_en), 'en')
            }}
            OPTIONAL {{
                ?agent {FOAF.name.n3()} ?name_it .
                FILTER langMatches(lang(?name_it), 'it')
            }}
            OPTIONAL {{ ?agent {DCTERMS.identifier.n3()} ?id }}
        }}
        """).strip()

    @staticmethod
    def head() -> str:
        """
        The head for SPARQL CONSTRUCT queries of this object, will all fields
        without optionals.
        :return: the SPARQL CONSTRUCT head
        """
        return dedent(f"""
        ?agent a {Agent.type.n3()} ;
               {FOAF.name.n3()} ?name_en ;
               {FOAF.name.n3()} ?name_it ;
               {DCTERMS.identifier.n3()} ?id .
        """).strip()

    @staticmethod
    def vars() -> str:
        """
        The variable names used in the object BGP. Useful to build extraction
        queries from the BGP with the proper variable order.
        :return: the ordered list of variables appearing in the BGP
        """
        return "?agent ?name_en ?name_it ?id"


@dataclass
class ContactPoint:
    type: ClassVar[URIRef] = VCARD.Kind
    uri: URIRef
    fn_en: Optional[Literal]
    fn_it: Optional[Literal]
    email: Optional[URIRef]
    telephone: Optional[URIRef]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, ContactPoint.type),
            (self.uri, RDF.type, DCATAPIT.Organization),
            (self.uri, RDF.type, VCARD.Organization),
            (self.uri, VCARD.fn, self.fn_en),
            (self.uri, VCARD.fn, self.fn_it),
            (self.uri, VCARD.hasEmail, self.email),
            (self.uri, VCARD.hasTelephone, self.telephone),
        ]

    @staticmethod
    def bgp(uri: Optional[URIRef] = None) -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :param uri: optional uri of the element to filter for
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{ {f'BIND( {uri.n3()} AS ?contact)' if uri else ''}
            ?contact a {ContactPoint.type.n3()} .
            OPTIONAL {{
                ?contact {VCARD.fn.n3()} ?fn_en .
                FILTER langMatches(lang(?fn_en), 'en')
            }}
            OPTIONAL {{
                ?contact {VCARD.fn.n3()} ?fn_it .
                FILTER langMatches(lang(?fn_it), 'it')
            }}
            OPTIONAL {{ ?contact {VCARD.hasEmail.n3()} ?email }}
            OPTIONAL {{ ?contact {VCARD.hasTelephone.n3()} ?tel }}
        }}
        """).strip()

    @staticmethod
    def head() -> str:
        """
        The head for SPARQL CONSTRUCT queries of this object, will all fields
        without optionals.
        :return: the SPARQL CONSTRUCT head
        """
        return dedent(f"""
        ?contact a {ContactPoint.type.n3()} ;
                 {VCARD.fn.n3()} ?fn_en ;
                 {VCARD.fn.n3()} ?fn_it ;
                 {VCARD.hasEmail.n3()} ?email ;
                 {VCARD.hasTelephone.n3()} ?tel .
        """).strip()

    @staticmethod
    def vars() -> str:
        """
        The variable names used in the object BGP. Useful to build extraction
        queries from the BGP with the proper variable order.
        :return: the ordered list of variables appearing in the BGP
        """
        return "?contact ?fn_en ?fn_it ?email ?tel"


@dataclass
class Distribution:
    type: ClassVar[URIRef] = ADMS.SemanticAssetDistribution
    uri: URIRef
    title_en: Optional[Literal]
    title_it: Optional[Literal]
    description_en: Optional[Literal]
    description_it: Optional[Literal]
    format: Optional[URIRef]
    license: Optional[URIRef]
    accessURL: Optional[URIRef]
    downloadURL: Optional[URIRef]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, Distribution.type),
            (self.uri, DCTERMS.title, self.title_en),
            (self.uri, DCTERMS.title, self.title_it),
            (self.uri, DCTERMS.description, self.description_en),
            (self.uri, DCTERMS.description, self.description_it),
            (self.uri, DCTERMS.format, self.format),
            (self.uri, DCTERMS.license, self.license),
            (self.uri, DCAT.accessURL, self.accessURL),
            (self.uri, DCAT.downloadURL, self.downloadURL),
        ]

    @staticmethod
    def bgp(uri: Optional[URIRef] = None) -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :param uri: optional uri of the element to filter for
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{ {f'BIND( {uri.n3()} AS ?distrib)' if uri else ''}
            ?distrib a {Distribution.type.n3()} .
            OPTIONAL {{
                ?distrib {DCTERMS.title.n3()} ?title_en .
                FILTER langMatches(lang(?title_en), 'en')
            }}
            OPTIONAL {{
                ?distrib {DCTERMS.title.n3()} ?title_it .
                FILTER langMatches(lang(?title_it), 'it')
            }}
            OPTIONAL {{
                ?distrib {DCTERMS.description.n3()} ?description_en .
                FILTER langMatches(lang(?description_en), 'en')
            }}
            OPTIONAL {{
                ?distrib {DCTERMS.description.n3()} ?description_it .
                FILTER langMatches(lang(?description_it), 'it')
            }}
            OPTIONAL {{ ?distrib {DCTERMS.format.n3()} ?format }}
            OPTIONAL {{ ?distrib {DCTERMS.license.n3()} ?license }}
            OPTIONAL {{ ?distrib {DCAT.accessURL.n3()} ?accessURL }}
            OPTIONAL {{ ?distrib {DCAT.downloadURL.n3()} ?downloadURL }}
        }}
        """).strip()

    @staticmethod
    def head() -> str:
        """
        The head for SPARQL CONSTRUCT queries of this object, will all fields
        without optionals.
        :return: the SPARQL CONSTRUCT head
        """
        return dedent(f"""
            ?distrib a {Distribution.type.n3()} ;
                     {DCTERMS.title.n3()} ?title_en ;
                     {DCTERMS.title.n3()} ?title_it ;
                     {DCTERMS.description.n3()} ?description_en ;
                     {DCTERMS.description.n3()} ?description_it ;
                     {DCTERMS.format.n3()} ?format ;
                     {DCTERMS.license.n3()} ?license ;
                     {DCAT.accessURL.n3()} ?accessURL ;
                     {DCAT.downloadURL.n3()} ?downloadURL .
        """).strip()

    @staticmethod
    def vars() -> str:
        """
        The variable names used in the object BGP. Useful to build extraction
        queries from the BGP with the proper variable order.
        :return: the ordered list of variables appearing in the BGP
        """
        return ("?distrib ?title_en ?title_it ?description_en ?description_it"
                "?format ?license ?accessURL ?downloadURL")


@dataclass
class Project:
    type: ClassVar[URIRef] = ADMS.Project
    uri: URIRef
    name_en: Optional[Literal]
    name_it: Optional[Literal]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, Project.type),
            (self.uri, L0.name, self.name_en),
            (self.uri, L0.name, self.name_it),
        ]

    @staticmethod
    def bgp(uri: Optional[URIRef] = None) -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :param uri: optional uri of the element to filter for
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{ {f'BIND( {uri.n3()} AS ?project)' if uri else ''}
            ?project a {Project.type.n3()} .
            OPTIONAL {{
                ?project {L0.name.n3()} ?name_en .
                FILTER langMatches(lang(?name_en), 'en')
            }}
            OPTIONAL {{
                ?project {L0.name.n3()} ?name_it .
                FILTER langMatches(lang(?name_it), 'it')
            }}
        }}
        """).strip()

    @staticmethod
    def head() -> str:
        """
        The head for SPARQL CONSTRUCT queries of this object, will all fields
        without optionals.
        :return: the SPARQL CONSTRUCT head
        """
        return dedent(f"""
        ?project a {Project.type.n3()} ;
                 {L0.name.n3()} ?name_en ;
                 {L0.name.n3()} ?name_it .
        """).strip()

    @staticmethod
    def vars() -> str:
        """
        The variable names used in the object BGP. Useful to build extraction
        queries from the BGP with the proper variable order.
        :return: the ordered list of variables appearing in the BGP
        """
        return "?project ?name_en ?name_it"


class NDCDataset(Dataset):
    """
    Small wrapper around the RDF 1.1 Dataset class from rdflib to provide some
    custom methods that extract the relevant entities for the national data catalog.
    """
    DEFAULT_GRAPH = 'urn:x-eddy:ndc:'

    def __init__(
        self,
        store: Union[Store, str] = 'default',
        default_union: bool = True,
        default_graph_base: Optional[str] = DEFAULT_GRAPH,
    ):
        super().__init__(store, default_union, default_graph_base)

    @staticmethod
    def construct() -> str:
        """
        Return the SPARQL CONSTRUCT query to relevant data for this dataset.
        :return: the SPARQL CONSTRUCT query
        """
        # Do not indent to avoid problems with indentation
        return f"""
CONSTRUCT {{
    {Agent.head()}
    {ContactPoint.head()}
    {Distribution.head()}
    {Project.head()}
}}
WHERE {{
{Agent.bgp()}
UNION {ContactPoint.bgp()}
UNION {Distribution.bgp()}
UNION {Project.bgp()}
}}
        """.strip()

    def agents(self, uri: Optional[URIRef] = None) -> Iterable[Agent]:
        """
        Returns the list of agents in this dataset.
        :param uri: the uri of the element to filter for
        :return: the list of agents stored
        """
        return [Agent(*b) for b in self.query(
            f'SELECT {Agent.vars()} WHERE {Agent.bgp(uri)}'
        )]

    def contactPoints(self, uri: Optional[URIRef] = None) -> Iterable[ContactPoint]:
        """
        Returns the list of contact points in this dataset.
        :param uri: the uri of the element to filter for
        :return: the list of contact points stored
        """
        return [ContactPoint(*b) for b in self.query(
            f'SELECT {ContactPoint.vars()} WHERE {ContactPoint.bgp(uri)}'
        )]

    def distributions(self, uri: Optional[URIRef] = None) -> Iterable[Distribution]:
        """
        Returns the list of distributions in this dataset.
        :param uri: the uri of the element to filter for
        :return: the list of distributions stored
        """
        return [Distribution(*b) for b in self.query(
            f'SELECT {Distribution.vars()} WHERE {Distribution.bgp(uri)}'
        )]

    def projects(self, uri: Optional[URIRef] = None) -> Iterable[Project]:
        """
        Returns the list of projects in this dataset.
        :param uri: the uri of the element to filter for
        :return: the list of projects stored
        """
        return [Project(*b) for b in self.query(
            f'SELECT {Project.vars()} WHERE {Project.bgp(uri)}'
        )]

    def load(self, path: str = None) -> Graph:
        """
        Loads the dataset from a serialized version. If not specified will use
        the default store path.
        :param path: path of the serialized dataset to load
        :return: the dataset graph
        """
        if path:
            return self.parse(path)
        elif fexists(expandPath('@data/ndc.trig')):
            return self.parse(expandPath('@data/ndc.trig'))

    def save(self) -> None:
        """
        Saves this dataset to the default user destination.
        """
        self.serialize(expandPath('@data/ndc.trig'), format='trig')
