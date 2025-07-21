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

import json
from typing import (
    Iterable,
    cast,
)

from PyQt5 import (
    QtCore,
    QtNetwork,
)
from rdflib import Graph
from rdflib.term import (
    BNode,
    Identifier,
    Literal,
    URIRef,
)

from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

LOGGER = getLogger()


class SPARQLEndpoint(QtCore.QObject):
    """
    Object that abstracts a SPARQL endpoint to clients.
    This supports SELECT and CONSTRUCT queries through direct-POST only,
    and with JSON and TURTLE response formats, respectively.
    """
    sgnConstructFinished = QtCore.pyqtSignal(QtCore.QUrl, Graph)
    sgnSelectFinished = QtCore.pyqtSignal(QtCore.QUrl, tuple)
    sgnSPARQLError = QtCore.pyqtSignal(QtCore.QUrl)
    RequestBody = QtNetwork.QNetworkRequest.Attribute(2101)
    RequestType = QtNetwork.QNetworkRequest.Attribute(2102)

    def __init__(self, url: str, nmanager: QtNetwork.QNetworkAccessManager) -> None:
        """
        Create a new SPARQLEndpoint instance for the given URL.

        :param url: URL of the endpoint to query
        """
        super().__init__(nmanager)
        self._url = url

    #############################################
    #   PROPERTIES
    #################################

    @property
    def nmanager(self) -> QtNetwork.QNetworkAccessManager:
        """
        Returns the `QNetworkAccessManager` associated to this instance.

        :return: the `QNetworkAccessManager` of the instance
        """
        return cast(QtNetwork.QNetworkAccessManager, self.parent())

    @property
    def url(self) -> str:
        """
        Returns the URL of the associated SPARQL endpoint.

        :return: URL of the SPARQL endpoint
        """
        return self._url

    #############################################
    #   SLOTS
    #################################

    def onRequestFinished(self) -> None:
        """
        Executed when a request completes.
        """
        reply = cast(QtNetwork.QNetworkReply, self.sender())
        try:
            reply.deleteLater()
            if (
                reply.isFinished()
                and reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError
            ):
                body = reply.request().attribute(SPARQLEndpoint.RequestBody)
                type_ = reply.request().attribute(SPARQLEndpoint.RequestType)
                if type_ == 'CONSTRUCT':
                    graph = Graph(bind_namespaces='core')
                    graph.parse(data=str(reply.readAll(), encoding='utf-8'))  # noqa
                    self.sgnConstructFinished.emit(reply.url(), graph)
                elif type_ == 'SELECT':
                    response = json.loads(str(reply.readAll(), encoding='utf-8'))  # noqa
                    vars = response['head']['vars']
                    bindings = response['results']['bindings']
                    results = SPARQLEndpoint.process_bindings(bindings, vars)
                    self.sgnSelectFinished.emit(reply.url(), results)
                else:
                    LOGGER.error('Unrecognized request type: %s', type_)
                    self.sgnSPARQLError.emit(reply.url())
            else:
                LOGGER.warning('Failed to retrieve update data: %s', reply.errorString())
                self.sgnSPARQLError.emit(reply.url())
        except Exception as e:
            LOGGER.warning('Failed to retrive response data: %s', e)
            self.sgnSPARQLError.emit(reply.url())

    #############################################
    #   INTERFACE
    #################################

    def execConstruct(self, query: str) -> None:
        """
        Executes a SPARQL CONSTRUCT query against the endpoint, and returns
        and rdflib graph with the content of the endpoint response.

        :param query: the SPARQL CONSTRUCT query
        :return: the graph of the endpoint response
        """
        LOGGER.info('Executing SPARQL CONSTRUCT (Endpoint: %s)', self.url)
        request = SPARQLConstructRequest(QtCore.QUrl(self.url), query)
        reply = self.nmanager.post(request, query.encode('utf-8'))
        connect(reply.finished, self.onRequestFinished)
        # TIMEOUT AFTER 30 SECONDS
        QtCore.QTimer.singleShot(30000, reply.abort)

    def execSelect(self, query: str) -> None:
        """
        Executes a SPARQL SELECT query against the endpoint, and returns a tuple
        with an element per query variable in the same order as they are specified,
        converted the corresponding rdflib term.

        :param query: a SPARQL SELECT query
        :return: tuple with the bindings for variables in the query
        """
        LOGGER.info('Executing SPARQL SELECT (Endpoint: %s)', self.url)
        request = SPARQLSelectRequest(QtCore.QUrl(self.url), query)
        reply = self.nmanager.post(request, query.encode('utf-8'))
        connect(reply.finished, self.onRequestFinished)
        # TIMEOUT AFTER 30 SECONDS
        QtCore.QTimer.singleShot(30000, reply.abort)

    @staticmethod
    def process_binding(binding: dict[str, str]) -> Identifier:
        """
        Process the binding of a single variable in JSON form.

        The specifications of how the bindings are specified follow
        the RDF SPARQL JSON results spec:
        `https://www.w3.org/TR/rdf-sparql-json-res/#variable-binding-results`

        :param binding: the variable binding in JSON form
        :return: the identifier corresponding to the variable binding
        """
        type_, value = binding["type"], binding["value"]
        if type_ == "uri":
            return URIRef(value)
        elif type_ == "literal":
            return Literal(value, datatype=binding.get("datatype"), lang=binding.get("xml:lang"))
        elif type_ == "typed-literal":
            return Literal(value, datatype=URIRef(binding["datatype"]))
        elif type_ == "bnode":
            return BNode(value)
        else:
            raise ValueError(f"invalid binding type: {type_}")

    @staticmethod
    def process_bindings(bindings: dict[str, dict], vars: Iterable[str]) -> tuple[Identifier, ...]:
        """
        Extracts the bindings from a SPARQL query result by following the order
        of the variables specified in `vars`.

        The bindings are a list of `Query Solution Object`s which specify
        a binding for every variable in the head of the query.

        Given variables that have no binding will be mapped to `None`.

        :param bindings: the list of bindings that satisfy the query (i.e. the bindings)
        :param vars: the list of variables in the head of the query
        :return: a tuple with one binding for every variable (respecting their order)
        """
        return tuple([
            SPARQLEndpoint.process_binding(bindings[var])
            if var in bindings and bindings[var] else None
            for var in vars
        ])


class SPARQLConstructRequest(QtNetwork.QNetworkRequest):
    """
    Network request corresponding to a SPARQL CONSTRUCT query request.
    """

    def __init__(self, url: QtCore.QUrl, query: str) -> None:
        super().__init__(url)
        self.setRawHeader(b'Accept', b'text/turtle')
        self.setRawHeader(b'Content-Type', b'application/sparql-query')
        self.setAttribute(SPARQLEndpoint.RequestType, 'CONSTRUCT')
        self.setAttribute(SPARQLEndpoint.RequestBody, query)
        self.setAttribute(QtNetwork.QNetworkRequest.FollowRedirectsAttribute, True)


class SPARQLSelectRequest(QtNetwork.QNetworkRequest):
    """
    Network request corresponding to a SPARQL SELECT query request.
    """

    def __init__(self, url: QtCore.QUrl, query: str) -> None:
        super().__init__(url)
        self.setRawHeader(b'Accept', b'application/sparql-results+json')
        self.setRawHeader(b'Content-Type', b'application/sparql-query')
        self.setAttribute(SPARQLEndpoint.RequestType, 'SELECT')
        self.setAttribute(SPARQLEndpoint.RequestBody, query)
        self.setAttribute(QtNetwork.QNetworkRequest.FollowRedirectsAttribute, True)
