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

from abc import abstractmethod
import csv

import openpyxl
from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.iri import CommandIRISetTag
from eddy.core.commands.project import CommandProjectAddTag
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.tags import Tag
from eddy.ui.progress import BusyProgressDialog


class TagLoader(AbstractOntologyLoader):
    """
    Extends AbstractOntologyLoader with facilities to load tags from CSV/Xlsx files.

    The expected file format has 3 columns: `Name`, `Category`, `Description`.
    * `Name` is the tag own name.
    * `Category` is the breadcrumb of ancestor tag names (from the root down to
      the direct parent), separated by `categorySeparator`. An empty value
      means the tag has no parent (i.e. it's a root tag).
    * `Description` is an optional free-text description of the tag.

    Tags are uniquely identified by their id,
    which allows different tags sharing the same name to coexist as long as
    they belong to different branches of the hierarchy.
    """

    expectedHeader = ['name', 'category', 'description']
    categorySeparator = '>>'

    def __init__(self, path, project, session):
        super().__init__(path, project, session)
        self.importedTags = None

    @classmethod
    @abstractmethod
    def filetype(cls):
        pass

    def importTags(self, rows):
        roots = []
        nodesByPath = {}
        definedPaths = set()

        def splitCategory(category):
            if not category:
                return []
            parts = [self._clean(part) for part in category.split(self.categorySeparator)]
            return [part for part in parts if part]

        def getOrCreateNode(segments):
            path = None
            siblings = roots
            node = None
            for segment in segments:
                path = segment if path is None else '{0} {1} {2}'.format(
                    path, self.categorySeparator, segment,
                )
                node = nodesByPath.get(path)
                if node is None:
                    node = {'name': segment, 'description': '', 'subTags': []}
                    nodesByPath[path] = node
                    siblings.append(node)
                siblings = node['subTags']
            return node, path

        for index, row in enumerate(rows, start=2):
            values = list(row[:3]) + [None] * (3 - len(row))
            name = self._clean(values[0])
            category = self._clean(values[1])
            description = self._clean(values[2])
            if not any([name, category, description]):
                continue
            if not name:
                self._showError(
                    'Tag Import Error',
                    'Tag name not defined.',
                    'Row {} contains a tag without a name.'.format(index),
                )
                return None
            segments = splitCategory(category)
            segments.append(name)
            node, path = getOrCreateNode(segments)
            if path in definedPaths:
                self._showError(
                    'Tag Import Error',
                    'Duplicate tag definition.',
                    'Row {} defines tag "{}" more than once.'.format(index, name),
                )
                return None
            node['description'] = description
            definedPaths.add(path)
        return self._mergeIntoProject(roots)

    def _mergeIntoProject(self, roots):
        """
        Converts the given tree of plain dict nodes (as produced by the loop
        in `importTags`) into real `Tag` instances and merges them into the
        current Project.
        :type roots: list
        :rtype: list
        """
        existingByPath = {}

        def indexExisting(tagList):
            for existingTag in tagList:
                existingByPath[str(existingTag)] = existingTag
                indexExisting(existingTag.subtag)

        indexExisting(self.project.getTags())

        macroStarted = False

        def ensureMacroStarted():
            nonlocal macroStarted
            if not macroStarted:
                self.session.undostack.beginMacro('Import tags')
                macroStarted = True

        def convert(nodeList, parentTag, parentPath):
            resultTags = []
            for node in nodeList:
                path = node['name'] if parentPath is None else '{0} {1} {2}'.format(
                    parentPath, self.categorySeparator, node['name'],
                )
                tag = existingByPath.get(path)
                if tag is None:
                    tag = Tag(node['name'], node['description'] or None, id=None)
                    ensureMacroStarted()
                    self.session.undostack.push(
                        CommandProjectAddTag(self.project, tag, parent=parentTag))
                    existingByPath[path] = tag
                resultTags.append(tag)
                convert(node['subTags'], tag, path)
            return resultTags

        if not roots:
            return []
        try:
            importedRoots = convert(roots, None, None)
        finally:
            if macroStarted:
                self.session.undostack.endMacro()
        return importedRoots

    def isValidHeader(self, header):
        normalized = [self._clean(value).lower() for value in header[:3]]
        return normalized == self.expectedHeader

    def showTemplateMismatch(self):
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Template Mismatch')
        msgbox.setText(
            'The imported file does not match the predefined template.\n'
            'Please use the columns: name, category, description.'
        )
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.exec_()

    def _showError(self, title, text, informativeText):
        msgBox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning,
            title,
            text,
            informativeText=informativeText,
            parent=self.session,
        )
        msgBox.exec_()

    @staticmethod
    def _clean(value):
        if value is None:
            return ''
        return str(value).strip()


class CsvTagLoader(TagLoader):
    def run(self, file):
        bp = BusyProgressDialog('Loading Tags')
        bp.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        with bp:
            with open(file, newline='', encoding='utf-8-sig') as source:
                csvreader = csv.reader(source)
                header = next(csvreader, None)
                if not header or not self.isValidHeader(header):
                    self.showTemplateMismatch()
                    return
                rows = []
                for row in csvreader:
                    QtCore.QCoreApplication.processEvents()
                    rows.append(row)
                self.importedTags = self.importTags(rows)


class XlsxTagLoader(TagLoader):
    def run(self, file):
        bp = BusyProgressDialog('Loading Tags')
        bp.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        with bp:
            workbook = openpyxl.load_workbook(file, data_only=True)
            sheet = workbook.worksheets[0]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows or not self.isValidHeader(rows[0]):
                self.showTemplateMismatch()
                return
            self.importedTags = self.importTags(rows[1:])


class TaggedEntityLoader(AbstractOntologyLoader):
    """
    Extends AbstractOntologyLoader with facilities to associate existing IRIs
    with existing tags, reading the associations from a CSV/Xlsx file.

    The expected file format has 3 columns: `IRI`, `Category`, `Name`.
    * `IRI` is the full IRI string of the entity the tag has to be associated with.
    * `Category` is the full path of the tag to associate with the IRI (from the
      root down to the tag itself), separated by `categorySeparator`.
    * `Name` is not used during the import process.

    Rows referencing an IRI or a tag that do not already exist in the current
    Project are skipped.
    """

    expectedHeader = ['iri', 'category', 'name']
    categorySeparator = TagLoader.categorySeparator

    def __init__(self, path, project, session):
        super().__init__(path, project, session)
        self.importedCount = 0
        self.skippedCount = 0
        self.templateMismatch = False

    @classmethod
    @abstractmethod
    def filetype(cls):
        pass

    def importTaggedEntities(self, rows):
        tagsByPath = self._indexTagsByPath()
        macroStarted = False
        importedCount = 0
        skippedCount = 0

        def ensureMacroStarted():
            nonlocal macroStarted
            if not macroStarted:
                self.session.undostack.beginMacro('Import tagged entities')
                macroStarted = True

        try:
            for row in rows:
                QtCore.QCoreApplication.processEvents()
                values = list(row[:3]) + [None] * (3 - len(row))
                iriString = self._clean(values[0])
                category = self._clean(values[1])
                if not any([iriString, category]):
                    continue
                if not iriString or not category:
                    skippedCount += 1
                    continue
                if not self.project.existIRI(iriString):
                    skippedCount += 1
                    continue
                path = self._buildPath(category)
                tag = tagsByPath.get(path)
                if tag is None:
                    skippedCount += 1
                    continue
                iri = self.project.getIRI(iriString)
                if iri.tag == tag.id:
                    importedCount += 1
                    continue
                ensureMacroStarted()
                self.session.undostack.push(
                    CommandIRISetTag(self.project, iri, tag, iri.tag))
                importedCount += 1
        finally:
            if macroStarted:
                self.session.undostack.endMacro()
        self.importedCount = importedCount
        self.skippedCount = skippedCount

    def _buildPath(self, category):
        segments = [
            part for part in (
                self._clean(segment) for segment in category.split(self.categorySeparator)
            ) if part
        ]
        path = None
        for segment in segments:
            path = segment if path is None else '{0} {1} {2}'.format(
                path, self.categorySeparator, segment,
            )
        return path

    def _indexTagsByPath(self):
        index = {}

        def visit(tagList):
            for tag in tagList:
                index[str(tag)] = tag
                visit(tag.subtag)

        visit(self.project.getTags())
        return index

    def isValidHeader(self, header):
        normalized = [self._clean(value).lower() for value in header[:3]]
        return normalized == self.expectedHeader

    def showTemplateMismatch(self):
        self.templateMismatch = True
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Template Mismatch')
        msgbox.setText(
            'The imported file does not match the predefined template.\n'
            'Please use the columns: iri, category, name.'
        )
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgbox.exec_()

    @staticmethod
    def _clean(value):
        if value is None:
            return ''
        return str(value).strip()


class CsvTaggedEntityLoader(TaggedEntityLoader):
    def run(self, file):
        header = None
        rows = []
        bp = BusyProgressDialog('Importing Tagged Entities')
        bp.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        with bp:
            with open(file, newline='', encoding='utf-8-sig') as source:
                csvreader = csv.reader(source)
                header = next(csvreader, None)
                if header and self.isValidHeader(header):
                    for row in csvreader:
                        QtCore.QCoreApplication.processEvents()
                        rows.append(row)
        if not header or not self.isValidHeader(header):
            self.showTemplateMismatch()
            return
        self.importTaggedEntities(rows)


class XlsxTaggedEntityLoader(TaggedEntityLoader):
    def run(self, file):
        bp = BusyProgressDialog('Importing Tagged Entities')
        bp.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        with bp:
            workbook = openpyxl.load_workbook(file, data_only=True)
            sheet = workbook.worksheets[0]
            rows = list(sheet.iter_rows(values_only=True))
        if not rows or not self.isValidHeader(rows[0]):
            self.showTemplateMismatch()
            return
        self.importTaggedEntities(rows[1:])
