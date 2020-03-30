from enum import unique

from PyQt5 import QtWidgets

from eddy.core.datatypes.common import IntEnum_


class MessageBoxFactory():

    @staticmethod
    def getMessageBox(parent,text, title, boxType, detailedText=None, informativeText=None):
        msgBox = QtWidgets.QMessageBox(parent=parent)
        if boxType==MsgBoxType.ERROR.value:
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        elif boxType==MsgBoxType.WARNING.value:
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        else:
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText(text)
        msgBox.setWindowTitle(title)
        if detailedText:
            msgBox.setDetailedText(detailedText)
        if informativeText:
            msgBox.setInformativeText(informativeText)

        return msgBox



@unique
class MsgBoxType(IntEnum_):
    """
    Extends Enum providing all the available type of message
    """
    ERROR = 1
    WARNING = 2
    INFO = 3