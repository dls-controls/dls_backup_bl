#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from functools import partial

from PyQt5.QtWidgets import (
    QDialog, QGridLayout,
    QLineEdit, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout
)


class EntryPopup(QDialog):
    def __init__(self, EditMode, parent=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.EditMode = EditMode
        # self.List = myList
        # self.JSONData = JSONData

        # Create the required layouts        
        self.GridLayout = QGridLayout()
        self.ButtonsLayout = QHBoxLayout()
        self.VerLayout = QVBoxLayout()

        self.SelectedDevice = str(
            self.parent.Tabs.tabText(self.parent.Tabs.currentIndex()))

        if self.SelectedDevice == "PMACs" or self.SelectedDevice == "GeoBricks":
            self.FieldsList = ["Controller", "Port", "Server"]
        elif self.SelectedDevice == "TerminalServers":
            self.FieldsList = ["Server", "Type"]
        else:
            self.FieldsList = ["Name"]

        self.LineEditList = []

        for i, Field in enumerate(self.FieldsList):
            self.GridLayout.addWidget(QLabel(str(Field)), i, 0)
            temp = QLineEdit()
            self.LineEditList.append(temp)
            self.GridLayout.addWidget(temp, i, 1)

        # Create the cancel button and add it to the buttons layout
        self.CancelButton = QPushButton('Cancel', self)
        self.CancelButton.clicked.connect(self.close)
        self.ButtonsLayout.addWidget(self.CancelButton)

        # Setup the add next button and add it to the button layout
        self.AddNextButton = QPushButton('Add Next', self)
        self.AddNextButton.setEnabled(False)
        self.AddNextButton.clicked.connect(
            partial(self.AddEditEntry, EditMode, True))
        self.ButtonsLayout.addWidget(self.AddNextButton)

        if EditMode:
            self.AddNextButton.setVisible(False)
            self.setWindowTitle('Edit Entry')
            # self.Name.setText(self.parent.CategoryList.currentIndex().data(
            # ).toString())
            for n in range(0, len(self.FieldsList)):
                self.LineEditList[n].setText(
                    self.parent.DeviceList.selectedIndexes()[n].data())
        else:
            self.setWindowTitle('Add Entry')

        # Setup the finish button and add it to the button layout
        self.AddFinishButton = QPushButton('Finished', self)
        self.AddFinishButton.setEnabled(False)
        self.AddFinishButton.clicked.connect(partial(self.AddEditEntry,
                                                     EditMode, False))
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

    def ButtonVisibility(self):

        Present = False
        EmptyLineEdit = False

        '''for Entry in self.parent.JSONData["Nouns"][self.CategoryName]:
            if Entry.values()[0] == unicode(self.EngSingText.text().toUtf8(), 
            encoding="UTF-8"):
                self.EngSingText.setStyleSheet("border: 2px solid red")
                break
            else:
                self.EngSingText.setStyleSheet("")

        for Entry in self.parent.JSONData["Nouns"][self.CategoryName]:
            if Entry.values()[1] == unicode(self.TraSingText.text().toUtf8(), 
            encoding="UTF-8"):
                self.TraSingText.setStyleSheet("border: 2px solid red")
                Present = True
                break
            else:
                self.TraSingText.setStyleSheet("")'''

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
            self.parent.Tabs.tabText(self.parent.Tabs.currentIndex()))
        self.RowNumber = self.parent.DeviceList.selectionModel(

        ).currentIndex().row()
        self.NewEntry = OrderedDict()

        for i in range(len(self.FieldsList)):
            self.NewEntry[self.FieldsList[i]] = self.LineEditList[i].text()

        if EditMode:
            self.parent.JSONData[self.SelectedDevice][
                self.RowNumber] = self.NewEntry
        else:
            self.parent.JSONData[self.SelectedDevice].append(self.NewEntry)

        self.parent.JSONData[self.SelectedDevice] = sorted(
            self.parent.JSONData[self.SelectedDevice],
            key=lambda dicts: dicts[self.FieldsList[0]])

        self.parent.write_json_file()
        if NextEntry:
            for EditBox in self.LineEditList:
                EditBox.setText("")
            self.LineEditList[0].setFocus()
        else:
            self.close()
