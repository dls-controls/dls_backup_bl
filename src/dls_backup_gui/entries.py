#!/usr/bin/python
# -*- coding: utf-8 -*-

# WHY DOES THIS NOT WORK??
# from .backupeditor import BackupEditor

from functools import partial
from logging import getLogger

from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

log = getLogger(__name__)


class EntryPopup(QDialog):
    def __init__(self, EditMode, parent=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.EditMode = EditMode

        # Create the required layouts
        self.GridLayout = QGridLayout()
        self.ButtonsLayout = QHBoxLayout()
        self.VerLayout = QVBoxLayout()

        this_tab = self.parent.Tabs.currentIndex()
        self.SelectedDevice = str(self.parent.Tabs.tabText(this_tab))
        self.data_type = parent.tab_entry_type[this_tab]
        self.FieldsList = self.data_type.keys()

        self.LineEditList = []

        for i, Field in enumerate(self.FieldsList):
            self.GridLayout.addWidget(QLabel(str(Field)), i, 0)
            temp = QLineEdit()
            self.LineEditList.append(temp)
            self.GridLayout.addWidget(temp, i, 1)

        # Create the cancel button and add it to the buttons layout
        self.CancelButton = QPushButton("Cancel", self)
        self.CancelButton.clicked.connect(self.close)
        self.ButtonsLayout.addWidget(self.CancelButton)

        # Setup the add next button and add it to the button layout
        self.AddNextButton = QPushButton("Add Next", self)
        self.AddNextButton.setEnabled(False)
        self.AddNextButton.clicked.connect(partial(self.AddEditEntry, EditMode, True))
        self.ButtonsLayout.addWidget(self.AddNextButton)

        if EditMode:
            self.AddNextButton.setVisible(False)
            self.setWindowTitle("Edit Entry")
            for n in range(0, len(self.FieldsList)):
                self.LineEditList[n].setText(
                    self.parent.DeviceList.selectedIndexes()[n].data()
                )
        else:
            self.setWindowTitle("Add Entry")

        # Setup the finish button and add it to the button layout
        self.AddFinishButton = QPushButton("Finished", self)
        self.AddFinishButton.setEnabled(False)
        self.AddFinishButton.clicked.connect(
            partial(self.AddEditEntry, EditMode, False)
        )
        # self.Name.textChanged.connect(partial(self.TextChanged, EditMode))
        self.ButtonsLayout.addWidget(self.AddFinishButton)

        # these have to be here, as the buttons in the function now exist
        for LineEdit in self.LineEditList:
            LineEdit.textChanged.connect(self.ButtonVisibility)

        # Add both layouts to the final layout
        self.VerLayout.addLayout(self.GridLayout)
        self.VerLayout.addLayout(self.ButtonsLayout)
        self.setLayout(self.VerLayout)

    def TextChanged(self, thing, obj):
        for n, letter in enumerate(thing.text()):
            UnicodeNum = letter.toUtf8()
            Ordinal = ord(UnicodeNum)
            Ordinal = Ordinal  # fixing linting but this is a null function

    def ButtonVisibility(self):
        Present = False
        EmptyLineEdit = False

        if self.EditMode:
            Present = False

        for LineEdit in self.LineEditList:
            if len(LineEdit.text()) < 1:
                EmptyLineEdit = True

        if Present or EmptyLineEdit:
            ButtonVisibility = False
            self.AddNextButton.setEnabled(ButtonVisibility)
            self.AddFinishButton.setEnabled(ButtonVisibility)
            # self.setTabOrder(self.TraPluText, self.CancelButton)
            self.CancelButton.setDefault(True)
        else:
            ButtonVisibility = True
            self.AddNextButton.setEnabled(ButtonVisibility)
            self.AddFinishButton.setEnabled(ButtonVisibility)
            # self.setTabOrder(self.TraPluText, self.AddNextButton)
            self.setTabOrder(self.AddNextButton, self.AddFinishButton)
            if self.EditMode:
                self.AddFinishButton.setDefault(True)
            else:
                self.AddNextButton.setDefault(True)

    def AddEditEntry(self, EditMode, NextEntry):
        self.SelectedDevice = str(
            self.parent.Tabs.tabText(self.parent.Tabs.currentIndex())
        )
        self.RowNumber = self.parent.DeviceList.selectionModel().currentIndex().row()

        values = [self.LineEditList[i].text() for i in range(len(self.FieldsList))]
        try:
            new_data = self.data_type(*values)
        except ValueError as e:
            QMessageBox.warning(
                self, "Warning", "Invalid field\n" + str(e), QMessageBox.Ok
            )
        else:
            if EditMode:
                self.parent.config[self.SelectedDevice][self.RowNumber] = new_data
            else:
                self.parent.config[self.SelectedDevice].append(new_data)

            self.parent.config.save(self.parent.file)
            self.parent.display_entries()
            if NextEntry:
                for EditBox in self.LineEditList:
                    EditBox.setText("")
                self.LineEditList[0].setFocus()
            else:
                self.close()
