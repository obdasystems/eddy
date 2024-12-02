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
from textwrap import dedent, indent
from typing import Union, Optional, Iterable

from SPARQLWrapper import SPARQLWrapper, RDF as rdf
from rdflib import Graph, RDF, URIRef, Literal, Dataset
from rdflib.namespace import (
    FOAF,
    DCAT,
    DCTERMS,
    DefinedNamespace,
    Namespace,
)
from rdflib.store import Store

from eddy.core.commands.iri import CommandIRIAddAnnotationAssertion
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.path import expandPath
from eddy.core.owl import AnnotationAssertion, OWL2Datatype

# Create the default store if not exists yet
if not fexists(expandPath('@data/rdf-store.ttl')):
    with open(expandPath('@data/rdf-store.ttl'), 'w') as store:
        store.writelines(['# NDC default triple store'])


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


# Subset of the vcard ontology vocabulary
class VCARD(DefinedNamespace):
    Kind: URIRef
    fn: URIRef
    hasEmail: URIRef
    hasTelephone: URIRef
    _NS = Namespace('http://www.w3.org/2006/vcard/ns#')


@dataclass
class Agent:
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
            (self.uri, RDF.type, FOAF.Agent),
            (self.uri, FOAF.name, self.name_en),
            (self.uri, FOAF.name, self.name_it),
            (self.uri, DCTERMS.identifier, self.identifier),
        ]

    @staticmethod
    def bgp() -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{
            ?agent a {FOAF.Agent.n3()} .
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
        ?agent a {FOAF.Agent.n3()} ;
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
    uri: URIRef
    fn_en: Optional[Literal]
    fn_it: Optional[Literal]
    email: Optional[Literal]
    telephone: Optional[Literal]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, VCARD.Kind),
            (self.uri, VCARD.fn, self.fn_en),
            (self.uri, VCARD.fn, self.fn_it),
            (self.uri, VCARD.hasEmail, self.email),
        ]

    @staticmethod
    def bgp() -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{
            ?contact a {VCARD.Kind.n3()} .
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
        ?contact a {VCARD.Kind.n3()} ;
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
    uri: URIRef
    title_en: Optional[Literal]
    title_it: Optional[Literal]
    description_en: Optional[Literal]
    description_it: Optional[Literal]
    format: Optional[Literal]
    license: Optional[Literal]
    accessURL: Optional[URIRef]
    downloadURL: Optional[URIRef]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, ADMS.SemanticAssetDistribution),
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
    def bgp() -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{
            ?distrib a {ADMS.SemanticAssetDistribution.n3()} .
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
            ?distrib a {ADMS.SemanticAssetDistribution.n3()} ;
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
    uri: URIRef
    name_en: Optional[Literal]
    name_it: Optional[Literal]

    def triples(self) -> Iterable:
        """
        The list of RDF triples representing this instance.
        :return: the list  of triples representing this instance.
        """
        return [
            (self.uri, RDF.type, ADMS.Project),
            (self.uri, L0.name, self.name_en),
            (self.uri, L0.name, self.name_it),
        ]

    @staticmethod
    def bgp() -> str:
        """
        The SPARQL BGP that identifies instances of this class in an RDF dataset.
        :return: the SPARQL BGP
        """
        return dedent(f"""
        {{
            ?project a {ADMS.Project.n3()} .
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
        ?project a {ADMS.Project.n3()} ;
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
    STORE_PATH = expandPath('@data/ndc.trig')

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

    def agents(self) -> Iterable[Agent]:
        """
        Returns the list of agents in this dataset.
        :return: the list of agents stored
        """
        return [Agent(*b) for b in self.query(
            f'SELECT {Agent.vars()} WHERE {Agent.bgp()}'
        )]

    def contactPoints(self) -> Iterable[ContactPoint]:
        """
        Returns the list of contact points in this dataset.
        :return: the list of contact points stored
        """
        return [ContactPoint(*b) for b in self.query(
            f'SELECT {ContactPoint.vars()} WHERE {ContactPoint.bgp()}'
        )]

    def distributions(self) -> Iterable[Distribution]:
        """
        Returns the list of distributions in this dataset.
        :return: the list of distributions stored
        """
        return [Distribution(*b) for b in self.query(
            f'SELECT {Distribution.vars()} WHERE {Distribution.bgp()}'
        )]

    def projects(self) -> Iterable[Project]:
        """
        Returns the list of projects in this dataset.
        :return: the list of projects stored
        """
        return [Project(*b) for b in self.query(
            f'SELECT {Project.vars()} WHERE {Project.bgp()}'
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
        elif fexists(NDCDataset.STORE_PATH):
            return self.parse(NDCDataset.STORE_PATH)

    def save(self) -> None:
        """
        Saves this dataset to the default user destination.
        """
        self.serialize(NDCDataset.STORE_PATH, format='trig')


def sendQuery(query, endpointURL):
    sparql = SPARQLWrapper(endpointURL)
    sparql.setQuery(query)
    sparql.setReturnFormat(rdf)
    resultGraph = sparql.query().convert()
    '''for res in qres["results"]["bindings"]:
        print(res)'''
    return resultGraph


def extractAgents(endpointURL):
    prefix = """
            PREFIX dct: <http://purl.org/dc/terms/>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            """
    query = """CONSTRUCT {
                ?x a foaf:Agent.
                ?x foaf:name ?y0.
                ?x dct:identifier ?y1.
                } WHERE {
              ?x a foaf:Agent.
              OPTIONAL {
                ?x foaf:name ?y0.
              }.
              OPTIONAL {
                ?x dct:identifier ?y1.
              }.
            }"""
    graph = sendQuery(prefix+query, endpointURL)
    return graph


def extractContactPoints(endpointURL):
    prefix = """
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                """
    query = """CONSTRUCT {
                  ?x a vcard:Kind.
                  ?x vcard:fn ?y0.
                  ?x vcard:hasEmail ?y1.
                  ?x vcard:hasTelephone ?y2.
                } WHERE {
                  ?x a vcard:Kind.
                  OPTIONAL {
                    ?x vcard:fn ?y0.
                  }.
                  OPTIONAL {
                    ?x vcard:hasEmail ?y1.
                  }.
                  OPTIONAL {
                    ?x vcard:hasTelephone ?y2.
                  }.
                }"""
    graph = sendQuery(prefix+query, endpointURL)
    return graph


def extractProjects(endpointURL):
    prefix = """
                    PREFIX l0: <https://w3id.org/italia/onto/l0/>
                    PREFIX ADMS: <https://w3id.org/italia/onto/ADMS/>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    """
    query = """CONSTRUCT {
                    ?x a ADMS:Project.
                    ?x l0:name ?y0.
                } WHERE {
                  ?x a ADMS:Project.
                  OPTIONAL {
                    ?x l0:name ?y0.
                  }.
                }"""
    graph = sendQuery(prefix+query, endpointURL)
    return graph


def extractDistributions(endpointURL):
    prefix = """PREFIX dct: <http://purl.org/dc/terms/>
                PREFIX dcat: <http://www.w3.org/ns/dcat#>
                PREFIX ADMS: <https://w3id.org/italia/onto/ADMS/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                """
    query = """CONSTRUCT {
                  ?x a ADMS:SemanticAssetDistribution.
                  ?x dct:title ?y0.
                  ?x dct:description ?y1.
                  ?x dct:format ?y2.
                  ?x dct:license ?y3.
                  ?x dcat:accessURL ?y4.
                  ?x dcat:downloadURL ?y5.
                } WHERE {
                  ?x a ADMS:SemanticAssetDistribution.
                  OPTIONAL {
                    ?x dct:title ?y0.
                  }.
                  OPTIONAL {
                    ?x dct:description ?y1.
                  }.
                  OPTIONAL {
                    ?x dct:format ?y2.
                  }.
                  OPTIONAL {
                    ?x dct:license ?y3.
                  }.
                  OPTIONAL {
                    ?x dcat:accessURL ?y4.
                  }.
                  OPTIONAL {
                    ?x dcat:downloadURL ?y5.
                  }.
                }"""
    graph = sendQuery(prefix+query, endpointURL)
    return graph


def getDataFromEndpoint(endpointURL):
    # endpoint = "https://schema.gov.it/sparql"
    if endpointURL:
        agentsGraph = extractAgents(endpointURL)
        distributionGraph = extractDistributions(endpointURL)
        contactPointsGraph = extractContactPoints(endpointURL)
        projectsGraph = extractProjects(endpointURL)
        graph = agentsGraph + distributionGraph + contactPointsGraph + projectsGraph
        graphName = endpointURL.replace('https://', '[').replace('/', ']')
        graph.serialize(destination=expandPath(f'@data/{graphName}.ttl'))
    return True


def getAgentsFromStore(endpointURL):
    agents = [""]
    graphName = endpointURL.replace('https://', '[').replace('/', ']')
    g1 = Graph()
    g1.parse(expandPath(f'@data/{graphName}.ttl'))
    g2 = Graph()
    g2.parse(expandPath('@data/rdf-store.ttl'))
    g = g1 + g2
    for s, p, o in g.triples((None, RDF.type, FOAF.Agent)):
        agents.append(s)
    return agents


def getContactPointsFromStore(endpointURL):
    contacts = [""]
    graphName = endpointURL.replace('https://', '[').replace('/', ']')
    g1 = Graph()
    g1.parse(expandPath(f'@data/{graphName}.ttl'))
    g2 = Graph()
    g2.parse(expandPath('@data/rdf-store.ttl'))
    g = g1 + g2
    for s, p, o in g.triples((None, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind"))):
        contacts.append(s)
    return contacts


def getProjectsFromStore(endpointURL):
    projects = [""]
    graphName = endpointURL.replace('https://', '[').replace('/', ']')
    g1 = Graph()
    g1.parse(expandPath(f'@data/{graphName}.ttl'))
    g2 = Graph()
    g2.parse(expandPath('@data/rdf-store.ttl'))
    g = g1 + g2
    for s, p, o in g.triples(
        (None, RDF.type, URIRef("https://w3id.org/italia/onto/ADMS/Project"))):
        projects.append(s)
    return projects


def getDistributionsFromStore(endpointURL):
    distributions = [""]
    graphName = endpointURL.replace('https://', '[').replace('/', ']')
    g1 = Graph()
    g1.parse(expandPath(f'@data/{graphName}.ttl'))
    g2 = Graph()
    g2.parse(expandPath('@data/rdf-store.ttl'))
    g = g1 + g2
    for s, p, o in g.triples(
        (None, RDF.type, URIRef("https://w3id.org/italia/onto/ADMS/SemanticAssetDistribution"))):
        distributions.append(s)
    return distributions


def addAgentToStore(iri, nameIT, nameEN, id):
    dest = expandPath('@data/rdf-store.ttl')
    g = Graph()
    g.parse(dest)
    iriRef = URIRef(iri)
    nameITlit = Literal(nameIT, lang='it')
    nameENlit = Literal(nameEN,  lang='en')
    idLit = Literal(id, datatype=RDF.PlainLiteral)
    g.add((iriRef, RDF.type, FOAF.Agent))
    g.add((iriRef, FOAF.name, nameITlit))
    g.add((iriRef, FOAF.name, nameENlit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/identifier'), idLit))
    g.serialize(dest)
    return


def addProjectToStore(iri, nameIT, nameEN):
    dest = expandPath('@data/rdf-store.ttl')
    g = Graph()
    g.parse(dest)
    iriRef = URIRef(iri)
    nameITlit = Literal(nameIT,  lang='it')
    nameENlit = Literal(nameEN,  lang='en')
    g.add((iriRef, RDF.type, URIRef("https://w3id.org/italia/onto/ADMS/Project")))
    g.add((iriRef, URIRef("https://w3id.org/italia/onto/l0/name"), nameITlit))
    g.add((iriRef, URIRef("https://w3id.org/italia/onto/l0/name"), nameENlit))
    g.serialize(dest)
    return


def addDistributionToStore(iri, titleIT, titleEN, descriptionIT, descriptionEN, format, license, accessURL, downloadURL):
    dest = expandPath('@data/rdf-store.ttl')
    g = Graph()
    g.parse(dest)
    iriRef = URIRef(iri)
    titleITlit = Literal(titleIT, lang='it')
    titleENlit = Literal(titleEN,  lang='en')
    descriptionITlit = Literal(descriptionIT, lang='it')
    descriptionENlit = Literal(descriptionEN, lang='en')
    formatLit = URIRef(format)
    licenseLit = URIRef(license)
    accessURLlit = URIRef(accessURL)
    downloadURLlit = URIRef(downloadURL)
    g.add((iriRef, RDF.type, URIRef("https://w3id.org/italia/onto/ADMS/SemanticAssetDistribution")))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/title'), titleITlit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/title'), titleENlit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/description'), descriptionITlit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/description'), descriptionENlit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/format'), formatLit))
    g.add((iriRef, URIRef('http://purl.org/dc/terms/license'), licenseLit))
    g.add((iriRef, URIRef('http://www.w3.org/ns/dcat#accessURL'), accessURLlit))
    g.add((iriRef, URIRef('http://www.w3.org/ns/dcat#downloadURL'), downloadURLlit))
    g.serialize(dest)
    return


def addContactToStore(iri, nameIT, nameEN, email, telephone):
    dest = expandPath('@data/rdf-store.ttl')
    g = Graph()
    g.parse(dest)
    iriRef = URIRef(iri)
    nameITlit = Literal(nameIT,  lang='it')
    nameENlit = Literal(nameEN,  lang='en')
    emailLit = URIRef(email)
    telephoneLit = Literal(telephone)
    g.add((iriRef, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind")))
    g.add((iriRef, URIRef("http://www.w3.org/2006/vcard/ns#fn"), nameITlit))
    g.add((iriRef, URIRef("http://www.w3.org/2006/vcard/ns#fn"), nameENlit))
    g.add((iriRef, URIRef("http://www.w3.org/2006/vcard/ns#hasEmail"), emailLit))
    g.add((iriRef, URIRef("http://www.w3.org/2006/vcard/ns#hasTelephone"), telephoneLit))
    g.serialize(dest)
    return

def addIriAnnotationsToProject(url, project, subjectIri):
    graphName = url.replace('https://', '[').replace('/', ']')
    g1 = Graph()
    g1.parse(expandPath(f'@data/{graphName}.ttl'))
    g2 = Graph()
    g2.parse(expandPath('@data/rdf-store.ttl'))
    g = g1 + g2
    for s, p, o in g.triples((URIRef(subjectIri), None, None)):
        annotationAssertion = AnnotationAssertion(project.getIRI(subjectIri), project.getIRI(p.toPython()),
                                                  o.toPython() if isinstance(o, Literal) else project.getIRI(o.toPython()), OWL2Datatype.PlainLiteral.value if isinstance(o, Literal) else None, o.language if isinstance(o, Literal) else None)
        command = CommandIRIAddAnnotationAssertion(project, project.getIRI(subjectIri), annotationAssertion)
        project.session.undostack.push(command)
    return
