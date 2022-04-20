import csv

import openpyxl
from PyQt5.uic.properties import QtWidgets, QtGui, QtCore

from eddy.core.commands.iri import CommandIRIRemoveAnnotationAssertion, \
    CommandIRIAddAnnotationAssertion
from eddy.core.commands.project import CommandProjectAddAnnotationProperty
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.loaders.common import AbstractLoader, AbstractOntologyLoader
from eddy.core.output import getLogger
from eddy.core.owl import IllegalNamespaceError, AnnotationAssertion

LOGGER = getLogger()

class CsvLoader(AbstractOntologyLoader):
    """
        Extends AbstractOntologyLoader with facilities to load annotations from CSV file format.
        """

    def __init__(self, path, project, session):
        """
        Initialize the GraphML importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, project, session)

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Csv

    def run(self, file, override):

        file = open(file)
        csvreader = csv.reader(file)

        header = next(csvreader)
        # print(header)
        if header == ['RESOURCE', 'SIMPLE_NAME', 'TYPE', 'ANNOTATION', 'DATATYPE', 'LANG','VALUE']:
            pass
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Template Mismatch')
            msgbox.setText(
                    'The imported file does not match the predifined template. \n Please fill the predifined template and try again.')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            return

        rows = []
        for row in csvreader:
            rows.append(row)
        # print(rows)
        file.close()
        self.importAnnotations(rows, override)

    def importAnnotations(self, rows, override):

        types = {
                'Data Property': Item.AttributeNode,
                'Class': Item.ConceptNode,
                'Named Individual': Item.IndividualNode,
                'Object Property': Item.RoleNode
        }

        if override:

            for row in rows:
                resource = row[0]
                simple_name = row[1]
                type = row[2]
                annotation = row[3]
                datatype = row[4]
                lang = row[5] if row[5] != '' else 'eng'
                value = row[6]

                if value == '':
                    pass

                else:
                    # ADD ANNOTATION PROPERTY
                    try:
                        annIRI = str(annotation)
                        listProperties = [str(el) for el in list(self.project.annotationProperties)]

                        if annIRI not in listProperties:
                            self.project.isValidIdentifier(annIRI)

                            command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                            self.session.undostack.beginMacro(
                                    'Add annotation property {0} '.format(annIRI))
                            if command:
                                self.session.undostack.push(command)
                            self.session.undostack.endMacro()

                    except IllegalNamespaceError as e:
                            # noinspection PyArgumentList
                        msgBox = QtWidgets.QMessageBox(
                                QtWidgets.QMessageBox.Warning,
                                'Entity Definition Error',
                                'Illegal namespace defined.',
                                informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                                detailedText=str(e),
                                parent=self,
                        )
                        msgBox.exec_()

                        # ADD ANNOTATION ASSERTION
                    annotationAss = AnnotationAssertion(resource, annotation, value,
                                                            language=lang)

                    for diagram in self.project.diagrams():
                        # LOOK FOR RESOURCE
                        for item in diagram.items():
                            if item.isNode() and item.type() == types[type] and str(item.iri) == resource:

                                itemAnnotations = dict(item.iri.annotationAssertionMapItems)
                                newdict = {}
                                for k, v in itemAnnotations.items():
                                    if str(k) not in newdict.keys():
                                        newdict[str(k)] = [v]
                                    else:
                                        newdict[str(k)].append(v)

                                existing = None
                                for k, v in newdict.items():
                                    # k, v -> (k, [[A1],[A2], ...])
                                    if str(annotation) == k:
                                        currList = v
                                        if lang:
                                            for el in currList:
                                                ann = el[0]
                                                # ann -> [Ai]
                                                if ann.language == annotationAss.language:
                                                    existing = ann
                                                    if existing:
                                                        # REMOVE ALL THE EXISTING ANNOTATION ASSERTIONS WITH SAME PROPERTY-LANG
                                                        self.session.undostack.push(
                                                            CommandIRIRemoveAnnotationAssertion(
                                                                self.project, item.iri,
                                                                existing))

                                # ADD NEW ANNOTATION ASSERTION FOR PROPERTY-LANG
                                self.session.undostack.push(
                                    CommandIRIAddAnnotationAssertion(self.project, item.iri,
                                                                         annotationAss))
                                # print('final anno set for', item.iri, ':', item.iri.annotationAssertionMapItems)


        else:

            for row in rows:
                resource = row[0]
                simple_name = row[1]
                type = row[2]
                annotation = row[3]
                datatype = row[4]
                lang = row[5] if row[5] != '' else 'eng'
                value = row[6]

                if value == '':
                    pass

                else:
                    # ADD ANNOTATION PROPERTY
                    try:
                        annIRI = str(annotation)
                        listProperties = [str(el) for el in
                                              list(self.project.annotationProperties)]

                        if annIRI not in listProperties:
                            self.project.isValidIdentifier(annIRI)

                            command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                            self.session.undostack.beginMacro(
                                    'Add annotation property {0} '.format(annIRI))
                            if command:
                                self.session.undostack.push(command)
                            self.session.undostack.endMacro()

                    except IllegalNamespaceError as e:
                            # noinspection PyArgumentList
                        msgBox = QtWidgets.QMessageBox(
                                QtWidgets.QMessageBox.Warning,
                                'Entity Definition Error',
                                'Illegal namespace defined.',
                                informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                                detailedText=str(e),
                                parent=self,
                        )
                        msgBox.exec_()

                        # ADD ANNOTATION ASSERTION
                    annotationAss = AnnotationAssertion(resource, annotation, value,
                                                            language=lang)

                    for diagram in self.project.diagrams():
                        for item in diagram.items():
                            if item.isNode() and item.type() == types[type] and str(item.iri) == resource:
                                self.session.undostack.push(
                                    CommandIRIAddAnnotationAssertion(self.project, item.iri,
                                                                         annotationAss))

class XlsxLoader(AbstractOntologyLoader):
    """
        Extends AbstractOntologyLoader with facilities to load annotations from CSV file format.
        """

    def __init__(self, path, project, session):
        """
        Initialize the GraphML importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, project, session)

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Xlsx

    def run(self, file, override):

        workbook = openpyxl.load_workbook(file, enumerate)
        sheet = workbook.worksheets[0]

        number_of_rows = sheet.max_row +1
        number_of_columns = sheet.max_column +1

        rows = []
        for i in range(1, number_of_rows):
            row = []
            for x in range(1, number_of_columns):
                value = sheet.cell(row=i, column=x).value
                row.append(value)

            rows.append(row)

        header = rows[0]
        if header == ['RESOURCE', 'SIMPLE_NAME', 'TYPE', 'ANNOTATION', 'DATATYPE', 'LANG', 'VALUE']:
            pass
        else:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Template Mismatch')
            msgbox.setText(
                'The imported file does not match the predifined template. \n Please fill the predifined template and try again.')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
            return

        rows = rows[1:]

        self.importAnnotations(rows, override)

    def importAnnotations(self, rows, override):

        types = {
            'Data Property': Item.AttributeNode,
            'Class': Item.ConceptNode,
            'Named Individual': Item.IndividualNode,
            'Object Property': Item.RoleNode
        }

        if override:

            for row in rows:
                resource = row[0]
                simple_name = row[1]
                type = row[2]
                annotation = row[3]
                datatype = row[4]
                lang = row[5] if row[5] != '' else 'eng'
                value = row[6]

                if value == '':
                    pass

                else:
                    # ADD ANNOTATION PROPERTY
                    try:
                        annIRI = str(annotation)
                        listProperties = [str(el) for el in list(self.project.annotationProperties)]

                        if annIRI not in listProperties:
                            self.project.isValidIdentifier(annIRI)

                            command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                            self.session.undostack.beginMacro(
                                'Add annotation property {0} '.format(annIRI))
                            if command:
                                self.session.undostack.push(command)
                            self.session.undostack.endMacro()

                    except IllegalNamespaceError as e:
                        # noinspection PyArgumentList
                        msgBox = QtWidgets.QMessageBox(
                            QtWidgets.QMessageBox.Warning,
                            'Entity Definition Error',
                            'Illegal namespace defined.',
                            informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                            detailedText=str(e),
                            parent=self,
                        )
                        msgBox.exec_()

                        # ADD ANNOTATION ASSERTION
                    annotationAss = AnnotationAssertion(resource, annotation, value,
                                                        language=lang)

                    for diagram in self.project.diagrams():
                        # LOOK FOR RESOURCE
                        for item in diagram.items():
                            if item.isNode() and item.type() == types[type] and str(
                                item.iri) == resource:

                                itemAnnotations = dict(item.iri.annotationAssertionMapItems)
                                newdict = {}
                                for k, v in itemAnnotations.items():
                                    if str(k) not in newdict.keys():
                                        newdict[str(k)] = [v]
                                    else:
                                        newdict[str(k)].append(v)

                                existing = None
                                for k, v in newdict.items():
                                    # k, v -> (k, [[A1],[A2], ...])
                                    if str(annotation) == k:
                                        currList = v
                                        if lang:
                                            for el in currList:
                                                ann = el[0]
                                                # ann -> [Ai]
                                                if ann.language == annotationAss.language:
                                                    existing = ann
                                                    if existing:
                                                        # REMOVE ALL THE EXISTING ANNOTATION ASSERTIONS WITH SAME PROPERTY-LANG
                                                        self.session.undostack.push(
                                                            CommandIRIRemoveAnnotationAssertion(
                                                                self.project, item.iri,
                                                                existing))

                                # ADD NEW ANNOTATION ASSERTION FOR PROPERTY-LANG
                                self.session.undostack.push(
                                    CommandIRIAddAnnotationAssertion(self.project, item.iri,
                                                                     annotationAss))
                                # print('final anno set for', item.iri, ':', item.iri.annotationAssertionMapItems)


        else:

            for row in rows:
                resource = row[0]
                simple_name = row[1]
                type = row[2]
                annotation = row[3]
                datatype = row[4]
                lang = row[5] if row[5] != '' else 'eng'
                value = row[6]

                if value == '':
                    pass

                else:
                    # ADD ANNOTATION PROPERTY
                    try:
                        annIRI = str(annotation)
                        listProperties = [str(el) for el in
                                          list(self.project.annotationProperties)]

                        if annIRI not in listProperties:
                            self.project.isValidIdentifier(annIRI)

                            command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                            self.session.undostack.beginMacro(
                                'Add annotation property {0} '.format(annIRI))
                            if command:
                                self.session.undostack.push(command)
                            self.session.undostack.endMacro()

                    except IllegalNamespaceError as e:
                        # noinspection PyArgumentList
                        msgBox = QtWidgets.QMessageBox(
                            QtWidgets.QMessageBox.Warning,
                            'Entity Definition Error',
                            'Illegal namespace defined.',
                            informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                            detailedText=str(e),
                            parent=self,
                        )
                        msgBox.exec_()

                        # ADD ANNOTATION ASSERTION
                    annotationAss = AnnotationAssertion(resource, annotation, value,
                                                        language=lang)

                    for diagram in self.project.diagrams():
                        for item in diagram.items():
                            if item.isNode() and item.type() == types[type] and str(
                                item.iri) == resource:
                                self.session.undostack.push(
                                    CommandIRIAddAnnotationAssertion(self.project, item.iri,
                                                                     annotationAss))
