# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


import os

from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.graphol import Item
from eddy.core.exporters.common import AbstractExporter
from eddy.core.exporters.graphol import GrapholExporter
from eddy.core.functions.fsystem import fwrite, mkdir
from eddy.core.project import Project


class ProjectExporter(AbstractExporter):
    """
    This class can be used to export graphol projects to disk.

    A graphol project is stored within a directory whose structure is the following:

    - projectname/
    -   .eddy/              # subdirectory which contains project specific information
    -       meta.xml        # contains ontology and predicates meta information
    -       modules.xml     # contains the paths of all the modules of the ontology
    -   module1.graphol
    -   module2.graphol
    -   ...
    -   moduleN.graphol
    """
    def __init__(self, project, session=None):
        """
        Initialize the project exporter.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.projectMainPath = project.path
        self.projectDataPath = os.path.join(self.projectMainPath, Project.Home)
        self.projectMetaDataPath = os.path.join(self.projectDataPath, Project.MetaXML)
        self.projectModulesDataPath = os.path.join(self.projectDataPath, Project.ModulesXML)
        
        self.metaDocument = None
        self.modulesDocument = None
        
        self.metaFuncForItem = {
            Item.AttributeNode: self.exportAttributeMetadata,
            Item.ConceptNode: self.exportPredicateMeta,
            Item.RoleNode: self.exportRoleMetadata,
        }

        self.itemToXml = {
            Item.AttributeNode: 'attribute',
            Item.ComplementNode: 'complement',
            Item.ConceptNode: 'concept',
            Item.DatatypeRestrictionNode: 'datatype-restriction',
            Item.DisjointUnionNode: 'disjoint-union',
            Item.DomainRestrictionNode: 'domain-restriction',
            Item.EnumerationNode: 'enumeration',
            Item.IndividualNode: 'individual',
            Item.IntersectionNode: 'intersection',
            Item.PropertyAssertionNode: 'property-assertion',
            Item.RangeRestrictionNode: 'range-restriction',
            Item.RoleNode: 'role',
            Item.RoleChainNode: 'role-chain',
            Item.RoleInverseNode: 'role-inverse',
            Item.UnionNode: 'union',
            Item.ValueDomainNode: 'value-domain',
            Item.InclusionEdge: 'inclusion',
            Item.InputEdge: 'input',
            Item.MembershipEdge: 'membership',
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    def exportPredicateMeta(self, item, name):
        """
        Export predicate metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        meta = self.project.meta(item, name)
        element = self.metaDocument.createElement('predicate')
        element.setAttribute('type', self.itemToXml[item])
        element.setAttribute('name', name)
        description = self.metaDocument.createElement('description')
        description.appendChild(self.metaDocument.createTextNode(meta.description))
        url = self.metaDocument.createElement('url')
        url.appendChild(self.metaDocument.createTextNode(meta.url))
        element.appendChild(url)
        element.appendChild(description)
        return element

    def exportAttributeMetadata(self, item, name):
        """
        Export attribute metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMeta(item, name)
        meta = self.project.meta(item, name)
        functional = self.metaDocument.createElement('functional')
        functional.appendChild(self.metaDocument.createTextNode(str(int(meta.functional))))
        element.appendChild(functional)
        return element

    def exportRoleMetadata(self, item, name):
        """
        Export role metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMeta(item, name)
        meta = self.project.meta(item, name)
        functional = self.metaDocument.createElement('functional')
        functional.appendChild(self.metaDocument.createTextNode(str(int(meta.functional))))
        inverseFunctional = self.metaDocument.createElement('inverseFunctional')
        inverseFunctional.appendChild(self.metaDocument.createTextNode(str(int(meta.inverseFunctional))))
        asymmetric = self.metaDocument.createElement('asymmetric')
        asymmetric.appendChild(self.metaDocument.createTextNode(str(int(meta.asymmetric))))
        irreflexive = self.metaDocument.createElement('irreflexive')
        irreflexive.appendChild(self.metaDocument.createTextNode(str(int(meta.irreflexive))))
        reflexive = self.metaDocument.createElement('reflexive')
        reflexive.appendChild(self.metaDocument.createTextNode(str(int(meta.reflexive))))
        symmetric = self.metaDocument.createElement('symmetric')
        symmetric.appendChild(self.metaDocument.createTextNode(str(int(meta.symmetric))))
        transitive = self.metaDocument.createElement('transitive')
        transitive.appendChild(self.metaDocument.createTextNode(str(int(meta.transitive))))
        element.appendChild(functional)
        element.appendChild(inverseFunctional)
        element.appendChild(asymmetric)
        element.appendChild(irreflexive)
        element.appendChild(reflexive)
        element.appendChild(symmetric)
        element.appendChild(transitive)
        return element

    #############################################
    #   EXPORT PROJECT SPECIFIC DATA
    #################################

    def exportMetaToXML(self):
        """
        Export project items' matadata to XML file.
        """
        # 1) CREATE DOCUMENT
        self.metaDocument = QDomDocument()
        instruction = self.metaDocument.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.metaDocument.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.metaDocument.createElement('project')
        root.setAttribute('version', str(Project.Version))
        self.metaDocument.appendChild(root)

        # 3) EXPORT PROJECT METADATA
        iri = self.metaDocument.createElement('iri')
        iri.appendChild(self.metaDocument.createTextNode(self.project.iri))
        prefix = self.metaDocument.createElement('prefix')
        prefix.appendChild(self.metaDocument.createTextNode(self.project.prefix))
        ontology = self.metaDocument.createElement('ontology')
        ontology.appendChild(prefix)
        ontology.appendChild(iri)
        root.appendChild(ontology)

        # 4) APPEND PREDICATE METADATA
        metadata = self.metaDocument.createElement('predicates')
        for item, predicate in self.project.metas():
            func = self.metaFuncForItem[item]
            meta = func(item, predicate)
            metadata.appendChild(meta)
        root.appendChild(metadata)

        # 5) WRITE CONTENT TO DISK
        fwrite(self.metaDocument.toString(2), self.projectMetaDataPath)

    def exportModulesToXML(self):
        """
        Export the list of diagrams in this project to XML file.
        """
        # 1) CREATE DOCUMENT
        self.modulesDocument = QDomDocument()
        instruction = self.modulesDocument.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.modulesDocument.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.modulesDocument.createElement('project')
        root.setAttribute('version', str(Project.Version))
        self.modulesDocument.appendChild(root)

        # 3) APPEND ALL THE DIAGRAM NAMES
        modules = self.modulesDocument.createElement('modules')
        for diagram in self.project.diagrams():
            module = self.modulesDocument.createElement('module')
            module.appendChild(self.modulesDocument.createTextNode(diagram.name))
            modules.appendChild(module)
        root.appendChild(modules)

        # 4) WRITE CONTENT TO DISK
        fwrite(self.modulesDocument.toString(2), self.projectModulesDataPath)

    #############################################
    #   PROJECT GENERATION
    #################################

    def run(self):
        """
        Perform graphol document generation.
        """
        # 1) CREATE PROJECT STRUCTURE
        mkdir(self.projectMainPath)
        mkdir(self.projectDataPath)

        # 2) EXPORT GRAPHOL DIAGRAMS
        for diagram in self.project.diagrams():
            worker = GrapholExporter(diagram)
            worker.run()

        # 3) EXPORT PROJECT SPECIFIC DATA
        self.exportMetaToXML()
        self.exportModulesToXML()
