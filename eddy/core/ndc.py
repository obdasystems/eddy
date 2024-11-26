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


from SPARQLWrapper import SPARQLWrapper, RDF as rdf
from rdflib import Graph, RDF, FOAF, URIRef, Literal

from eddy.core.commands.iri import CommandIRIAddAnnotationAssertion
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.path import expandPath
from eddy.core.owl import AnnotationAssertion, OWL2Datatype

# Create the default store if not exists yet
if not fexists(expandPath('@data/rdf-store.ttl')):
    with open(expandPath('@data/rdf-store.ttl'), 'w') as store:
        store.writelines(['# NDC default triple store'])


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
