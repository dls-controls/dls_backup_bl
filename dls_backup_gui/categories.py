#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import sys
from functools import partial


from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QIcon, QStandardItemModel, QFont, QStandardItem
from PyQt5.QtWidgets import (
    QDialog, QLineEdit,
    QApplication, QLabel, QWidget, QDesktopWidget,
    QTabWidget, QTableView, QAbstractItemView, QPushButton,
    QHBoxLayout, QFileDialog, QHeaderView, QToolBar, QStatusBar,
    QAction, QVBoxLayout, QStyle, QMessageBox
)


class CategoryPopup(QDialog):
    def __init__(self, my_list, edit_mode, parent=None):
        QDialog.__init__(self, parent)

        print("Category popup")

        self.parent = parent
        self.JSONData = self.parent.JSONData

        # Create the needed layouts
        self.NameLayout = QHBoxLayout()
        self.ButtonsLayout = QHBoxLayout()
        self.VerLayout = QVBoxLayout()

        # Create the name widgets and add them to the name layout
        self.LabelName = QLabel("Name")
        self.Name = QLineEdit(self)
        self.NameLayout.addWidget(self.LabelName)
        self.NameLayout.addWidget(self.Name)

        # Setup the cancel button and add it to the button layout
        self.CancelButton = QPushButton('Cancel', self)
        self.CancelButton.clicked.connect(self.close)
        self.ButtonsLayout.addWidget(self.CancelButton)

        # Change the popup appearance depending on the mode
        if not edit_mode:
            # If add mode, setup the add next button
            self.setWindowTitle('Add Category')
            self.AddNextButton = QPushButton('Add Next', self)
            self.AddNextButton.setEnabled(False)
            self.AddNextButton.clicked.connect(
                partial(self.AddEditEntry, edit_mode, True))
            self.ButtonsLayout.addWidget(self.AddNextButton)
        else:
            # If edit mode, place the category name in the edit box
            self.setWindowTitle('Edit Entry')
            self.Name.setText(
                self.parent.CategoryList.currentIndex().data().toString())

        # Setup the finish button and add it to the button layout
        self.AddFinishButton = QPushButton('Finished', self)
        self.AddFinishButton.setEnabled(False)
        self.AddFinishButton.clicked.connect(
            partial(self.AddEditEntry, edit_mode, False))
        self.Name.textChanged.connect(partial(self.TextChanged, edit_mode))
        self.ButtonsLayout.addWidget(self.AddFinishButton)

        # Add both layouts to the final layout
        self.VerLayout.addLayout(self.NameLayout)
        self.VerLayout.addLayout(self.ButtonsLayout)
        self.setLayout(self.VerLayout)

    def TextChanged(self, EditMode):
        print("text changing!")
        print(self.Name.text())
        print(str(self.parent.CategoryList.currentIndex().data().toString()))

        if str(self.Name.text()) in self.JSONData["Nouns"]:
            self.AddNextButton.setEnabled(False)
            self.AddFinishButton.setEnabled(False)
        else:
            if EditMode:
                if self.Name.text() == str(
                        self.parent.CategoryList.currentIndex().data(

                        ).toString()):
                    self.AddFinishButton.setEnabled(False)
                else:
                    self.AddFinishButton.setEnabled(True)
            else:
                if len(self.Name.text()) < 1:
                    self.AddNextButton.setEnabled(False)
                    self.AddFinishButton.setEnabled(False)
                else:
                    self.AddNextButton.setEnabled(True)
                    self.AddFinishButton.setEnabled(True)

    def AddEditEntry(self, EditMode, NextEntry):

        print("AddEditEntry")

        self.CategoryName = str(
            self.parent.CategoryList.currentIndex().data().toString())

        if not EditMode:
            print("Adding category")
            self.JSONData["Nouns"][str(self.Name.text())] = []
        else:
            print("Editing category")
            self.JSONData["Nouns"][str(self.Name.text())] = \
            self.JSONData["Nouns"][self.CategoryName]
            del self.JSONData["Nouns"][self.CategoryName]

        self.parent.write_json_file()
        if NextEntry:
            self.Name.setText("")
        else:
            self.close()
