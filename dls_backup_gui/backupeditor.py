import json
import signal
import sys
from collections import OrderedDict
from functools import partial
from optparse import OptionParser

from PyQt5.QtCore import Qt, QSize, QSettings, QTimer
from PyQt5.QtGui import QIcon, QStandardItemModel, QFont, QStandardItem
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QDesktopWidget,
    QTabWidget, QTableView, QAbstractItemView, QPushButton,
    QHBoxLayout, QFileDialog, QHeaderView, QToolBar, QStatusBar,
    QAction, QVBoxLayout, QStyle, QMessageBox, QMainWindow
)

from .entries import EntryPopup
from .categories import CategoryPopup


class Editor(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.InitialiseUI()

    def CentreWindow(self):
        # Get the geometry of the widget relative to its parent including any
        # window frame
        FrameGeometry = self.frameGeometry()
        ScreenCentre = QDesktopWidget().availableGeometry().center()
        FrameGeometry.moveCenter(ScreenCentre)
        self.move(FrameGeometry.topLeft())

    def InitialiseUI(self):

        # Set up the window and centre it on the screen  
        self.setWindowTitle('Backup Editor')
        self.MinimumSize = QSize(750, 450)
        self.resize(self.MinimumSize)
        self.setMinimumSize(self.MinimumSize)
        self.setWindowFlags(
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint)

        # self.setWindowIcon(QIcon('icon.png'))
        self.CentreWindow()

        # Create tab widget
        self.Tabs = QTabWidget()

        # Create individual tabs
        self.GeoBrickTab = QWidget()
        self.PMACTab = QWidget()
        self.TerminalServerTab = QWidget()
        self.ZebraTab = QWidget()

        # Add individual tabs to tab widget
        self.Tabs.addTab(self.GeoBrickTab, "GeoBricks")
        self.Tabs.addTab(self.PMACTab, "PMACs")
        self.Tabs.addTab(self.TerminalServerTab, "TerminalServers")
        self.Tabs.addTab(self.ZebraTab, "Zebras")

        # Create a table for entries
        self.DeviceList = QTableView(self)
        self.DeviceList.verticalHeader().setVisible(False)
        self.DeviceList.setColumnWidth(0, 600);
        self.DeviceList.setShowGrid(False)
        self.DeviceList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.DeviceList.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Create an Add Entry button
        self.AddEntryButton = QPushButton('New', self)
        self.AddEntryButton.setIconSize(QSize(24, 24))

        # Create a Remove Entry button
        self.RemoveEntryButton = QPushButton('Delete', self)
        self.RemoveEntryButton.setIconSize(QSize(24, 24))

        # Create an Edit Entry button
        self.EditEntryButton = QPushButton('Edit', self)
        self.EditEntryButton.setIconSize(QSize(24, 24))

        # Create layout for the entry buttons
        self.EntryButtonsLayout = QHBoxLayout()
        self.EntryButtonsLayout.addWidget(self.AddEntryButton)
        self.EntryButtonsLayout.addWidget(self.RemoveEntryButton)
        self.EntryButtonsLayout.addWidget(self.EditEntryButton)

        # Add the table to the tab layout
        self.DeviceLayout = QHBoxLayout()
        self.DeviceLayout.addWidget(self.DeviceList)
        # Set an initial state      
        self.GeoBrickTab.setLayout(self.DeviceLayout)

        # Link the buttons to their actions
        self.Tabs.currentChanged.connect(self.TabSelected)
        self.AddEntryButton.clicked.connect(
            partial(self.OpenAddEntryDialog, EditMode=False))
        self.EditEntryButton.clicked.connect(
            partial(self.OpenAddEntryDialog, EditMode=True))
        self.RemoveEntryButton.clicked.connect(self.RemoveEntry)

        # Create a tool bar
        self.ToolBar = QToolBar(self)

        # Create a status bar
        self.StatusBar = QStatusBar(self)

        # Create a file path label and set font 
        self.FilePathFont = QFont()
        self.FilePathFont.setBold(True)
        self.FilePathFont.setPointSize(12)
        self.OpenFileLabel = QLabel()
        self.OpenFileLabel.setFont(self.FilePathFont)

        # Create an Open File action
        self.OpenAction = QAction(QIcon('Open.png'),
                                  'Open a JSON File', self)
        self.OpenAction.setShortcut('Ctrl+O')
        self.OpenAction.triggered.connect(self.ShowOpenDialog)

        # Add the Open Action and File Path label to the tool bar
        self.ToolBar.addAction(self.OpenAction)
        self.ToolBar.addWidget(self.OpenFileLabel)

        # Create layout for all the different elements
        self.MainLayout = QVBoxLayout()
        self.MainLayout.addWidget(self.ToolBar)
        self.MainLayout.addWidget(self.Tabs)
        self.MainLayout.addLayout(self.EntryButtonsLayout)
        self.MainLayout.addWidget(self.StatusBar)

        # Use this layout as the main layout
        self.setLayout(self.MainLayout)

        # Establish QSettings to store/retrieve program settings
        self.EditorSettings = QSettings("DLS", "Backup Editor")

        # Look for the previously opened JSON file path and open it
        self.JSONFileName = "test_brick.json"  # self.EditorSettings.value(
        # "JSONFilePath").toString()
        self.OpenJSONFile()

        # Display the GUI
        self.show()

    def ShowOpenDialog(self):
        self.JSONFileName = QFileDialog.getOpenFileName(self,
                                                        'Open JSON File',
                                                        '/home',
                                                        "JSON Files ("
                                                        "*.json)")
        self.OpenJSONFile()

    def OpenJSONFile(self):

        # If a file is specified, open it, display the path, and store the
        # location
        if self.JSONFileName:
            self.ReadJSONFile()
            self.OpenFileLabel.setText(self.JSONFileName)
            # Save JSON file path to /home/jimbo/.config/JimboMonkey Productions
            self.EditorSettings.setValue("JSONFilePath", self.JSONFileName)

    def TabSelected(self, arg=None):
        # self.DeviceList.clear()
        self.DisplayEntries()
        if arg == 0:
            self.GeoBrickTab.setLayout(self.DeviceLayout)
        if arg == 1:
            self.PMACTab.setLayout(self.DeviceLayout)
        if arg == 2:
            self.TerminalServerTab.setLayout(self.DeviceLayout)
        if arg == 3:
            self.ZebraTab.setLayout(self.DeviceLayout)

    def DisplayEntries(self):

        self.SelectedDevice = str(self.Tabs.tabText(self.Tabs.currentIndex()))
        self.ListModel = QStandardItemModel()

        # self.EntryList = self.TableList[self.Tabs.currentIndex()]

        for Card in self.JSONData[self.SelectedDevice]:
            self.Row = []
            for Field in Card:
                self.Row.append(QStandardItem(Card[str(Field)]))
            self.ListModel.appendRow(self.Row)
        self.DeviceList.setModel(self.ListModel)
        self.DeviceList.resizeColumnsToContents()
        self.NumColumns = self.ListModel.columnCount()

        for ColumnNum in range(0, self.NumColumns):
            self.CurrentColumnWidth = self.DeviceList.columnWidth(ColumnNum)
            self.DeviceList.setColumnWidth(ColumnNum, self.CurrentColumnWidth
                                           + 20)
        # self.CardList.selectionModel().selectionChanged.connect(
        # self.EntryClick)
        self.DeviceList.selectRow(0)

    def ButtonRefresh(self):

        # Record the number of selected category and card entries
        NumCards = len(self.CardList.selectedIndexes())
        NumCategories = len(self.CategoryList.selectedIndexes())

        # Only enable buttons if they can be used (using 0 = False, 1+ = True)
        self.RemoveCategoryButton.setEnabled(NumCategories)
        self.EditCategoryButton.setEnabled(NumCategories)
        self.AddCardButton.setEnabled(NumCategories)
        self.RemoveCardButton.setEnabled(NumCards)
        self.EditCardButton.setEnabled(NumCards)

    def ReadJSONFile(self):

        # Attempt to open the JSON file
        try:
            with open(self.JSONFileName) as self.JSONFile:
                # Maintain order using a dictionary
                self.JSONData = json.load(self.JSONFile,
                                          object_pairs_hook=OrderedDict)
            self.JSONFile.close()
        # Capture problems opening or reading the file
        except Exception as e:
            print
            "\nInvalid JSON file name or path or invalid JSON\n"
            sys.exit()
        # Populate the category list with the data
        self.DisplayEntries()

    def WriteJSONFile(self):

        # Overwrite the JSON file including the changes
        try:
            with open(self.JSONFileName, "w") as self.JSONFile:
                # Write the data keeping a readable style
                # Note that sort_keys is not used as this undoes the chosen
                # ordering
                self.JSONDataToWrite = json.dumps(self.JSONData, indent=4,
                                                  separators=(',', ': '))
                self.JSONFile.write(self.JSONDataToWrite)
                self.JSONFile.close()
        # Capture problems opening or saving the file
        except Exception as e:
            print("\nInvalid json file name or path or invalid JSON\n")
            sys.exit()
        # Re-read the JSON file after the write to refresh the GUI
        self.ReadJSONFile()

    def RefreshCategoryList(self):

        # Create a model for the data
        self.ListModel = QStandardItemModel(self)

        # Keep a tally of the number of cards
        # TotalNouns = 0
        # TotalVerbs = 0
        # Less 1 from category count to ignore verbs
        TotalCategories = len(self.JSONData) - 1

        # For every category...
        for Category in self.JSONData:
            # ...create a list entry including the number of entries
            CategoryTitle = QStandardItem(Category)
            NumEntries = QStandardItem(str(len(self.JSONData[Category])))
            NumEntries.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Update the tally
            # if Category != "Verbs":
            #   TotalNouns += len(self.JSONData[Category])
            # else:
            #   TotalVerbs += len(self.JSONData[Category])

            # Add the list entry to the list model
            CategoryListItem = [CategoryTitle, NumEntries]
            self.ListModel.appendRow(CategoryListItem)

        # Update the status bar
        self.StatusBar.showMessage("hello!")  # (str(TotalNouns) + " nouns
        # and " + str(TotalVerbs) + " verbs across " + str(TotalCategories) +
        # " categories")

        if self.ListModel.rowCount() < 1:
            self.ListModel.clear()
            self.CategoryList.setModel(self.ListModel)
            self.DisplayCategoryCards()

        else:
            self.CategoryList.setModel(self.ListModel)
            self.CategoryList.selectionModel().selectionChanged.connect(
                self.DisplayCategoryCards)
            self.CategoryList.model().dataChanged.connect(
                self.DisplayCategoryCards)
            # self.CategoryList.selectionModel().selectionChanged.connect(
            # self.ButtonRefresh)

            self.CategoryList.model().setHeaderData(0, Qt.Horizontal,
                                                    "Title")
            self.CategoryList.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)
            self.CategoryList.model().setHeaderData(1, Qt.Horizontal,
                                                    "Entries")
            self.CategoryList.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)

            if self.LastSelectedCategory != None:
                self.LastSelectedIndex = self.CategoryList.model().index(
                    self.LastSelectedCategory.row(), 0)
                self.CategoryList.setCurrentIndex(self.LastSelectedIndex)
            else:
                self.FirstItemIndex = self.CategoryList.model().index(0, 0)
                self.CategoryList.setCurrentIndex(self.FirstItemIndex)

                self.CategoryList.resizeColumnsToContents()
                self.NumColumns = self.ListModel.columnCount()

                '''for ColumnNum in range(0, self.NumColumns):
                    self.CurrentColumnWidth = self.CategoryList.columnWidth(
                    ColumnNum)
                    self.CategoryList.setColumnWidth(ColumnNum, 
                    self.CurrentColumnWidth + 1000)'''
                # self.CardList.selectionModel().selectionChanged.connect(
                # self.ButtonRefresh)

                # Ensure the category list fits the titles but is never
                # narrower than the buttons below
                self.CategoryButtonsWidth = \
                    self.CategoryButtonsLayout.sizeHint().width()
                # self.CategoryListWidth =
                # self.CategoryList.sizeHintForColumn(0)+20 +
                # self.CategoryList.sizeHintForColumn(1) + 20
                # print self.CategoryList.sizeHintForColumn(0)
                # print self.CategoryList.sizeHintForColumn(1)
                self.CategoryListWidth = self.CategoryList.horizontalHeader(

                ).length() + 20
                # print self.CategoryListWidth

                if self.CategoryButtonsWidth < self.CategoryListWidth:
                    self.CategoryList.setFixedWidth(self.CategoryListWidth)
                else:
                    self.CategoryList.setFixedWidth(self.CategoryButtonsWidth)
                self.FirstItemIndex = self.CategoryList.model().index(0, 0)
                self.CategoryList.setCurrentIndex(self.FirstItemIndex)
                self.CategoryList.selectRow(1)
                self.CategoryList.selectRow(0)

    def DisplayCategoryCards(self):
        if len(self.CategoryList.selectedIndexes()) > 0:
            self.SelectedCategory = str(
                self.CategoryList.selectedIndexes()[0].data().toString())
        else:
            self.SelectedCategory = ''
        # self.SelectedCategory = str(self.CategoryList.currentIndex().data(
        # ).toString())
        self.LastSelectedCategory = self.CategoryList.currentIndex()
        self.ListModel = QStandardItemModel(self)
        self.ListModel.setHeaderData(0, Qt.Horizontal, 'james')

        HeaderLabels = []

        # print "display!", self.SelectedCategory, self.CategoryList.model(
        # ).rowCount()
        if self.CategoryList.model().rowCount() > 0:

            for Card in self.JSONData[self.SelectedCategory]:
                self.Row = []
                for Field in Card:
                    HeaderLabels.append(str(Field))
                    self.Row.append(QStandardItem(Card[str(Field)]))
                self.ListModel.appendRow(self.Row)
            self.CardList.setModel(self.ListModel)

            # self.CardList.sortByColumn(0, Qt.AscendingOrder)

            self.CardList.resizeColumnsToContents()
            self.NumColumns = self.ListModel.columnCount()

            for ColumnNum in range(0, self.NumColumns):
                self.CurrentColumnWidth = self.CardList.columnWidth(ColumnNum)
                self.CardList.setColumnWidth(ColumnNum,
                                             self.CurrentColumnWidth + 20)
            self.CardList.selectionModel().selectionChanged.connect(
                self.ButtonRefresh)
            self.CardList.selectRow(0)

        else:
            self.ListModel.clear()
            self.CardList.setModel(self.ListModel)

        for i, Label in enumerate(HeaderLabels):
            self.CardList.model().setHeaderData(i, Qt.Horizontal, Label)
            self.CardList.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)

        margins = self.layout().contentsMargins()
        self.resize((
                            margins.left() + margins.right() +
                            self.CardList.frameWidth() * 2 +
                            self.CardList.verticalHeader().width() +
                            self.CardList.horizontalHeader().length() +
                            self.CardList.style().pixelMetric(
                                QStyle.PM_ScrollBarExtent)
                            * 2) + self.CategoryList.width(), self.height())

        self.ButtonRefresh()

    def RemoveEntry(self):

        self.SelectedDeviceList = ""
        self.NumColumns = self.DeviceList.model().columnCount()
        self.NumRows = (
                len(self.DeviceList.selectedIndexes()) / self.NumColumns)
        self.SelectedIndexes = self.DeviceList.selectedIndexes()
        for Row in range(0, self.NumRows):
            self.RowString = ""
            self.SelectedRow = self.SelectedIndexes[Row * self.NumColumns].row()
            for Column in range(0, self.NumColumns):
                self.RowString = self.RowString + self.DeviceList.model().item(
                    self.SelectedRow, Column).text() + "\t"
            self.SelectedDeviceList = self.SelectedDeviceList + "\n" + \
                                      self.RowString
        # Find the number of rows before a removal
        self.LastRow = (self.DeviceList.model().rowCount() - 1)

        self.MsgBoxResponse = QMessageBox.question(self, "Remove?",
                                                   "Are you sure you "
                                                   "want to remove:\n"
                                                   +
                                                   self.SelectedDeviceList,
                                                   QMessageBox.Yes,
                                                   QMessageBox.No)
        if self.MsgBoxResponse == QMessageBox.Yes:
            self.SelectedDevice = str(
                self.Tabs.tabText(self.Tabs.currentIndex()))
            self.SelectedIndexes.sort()

            self.LastSelectedRow = self.SelectedIndexes[-1].row()
            for Row in range((self.NumRows - 1), -1, -1):
                self.SelectedRow = self.SelectedIndexes[
                    Row * self.NumColumns].row()
                # print self.SelectedRow
                del self.JSONData[self.SelectedDevice][self.SelectedRow]
            self.WriteJSONFile()

            # If the selected index was the last row in the list
            if self.LastSelectedRow == self.LastRow:
                # Select the new bottom of the list
                self.NewSelectedRow = (self.DeviceList.model().rowCount() - 1)
            else:
                # Otherwise select the same index in the list
                self.NewSelectedRow = self.LastSelectedRow
            # Create an index from this row and set it
            self.NewIndex = self.DeviceList.model().index(self.NewSelectedRow,
                                                          0)
            self.DeviceList.setCurrentIndex(self.NewIndex)

    def OpenAddEntryDialog(self, EditMode):
        self.AddEntryDialog = EntryPopup(EditMode, self)
        #      self.w.setGeometry(QRect(100, 100, 400, 200))
        self.AddEntryDialog.show()

    def doit(self, EditMode):
        self.SelectedIndex = self.CategoryList.selectionModel().currentIndex()
        if str(self.SelectedIndex.data().toString()) == 'Verbs':
            self.w = Verbs.CardPopup(EditMode, self)
        else:
            self.w = Cards.CardPopup(EditMode, self)
        self.w.setModal(True)
        self.w.show()

    def doitCat(self, EditMode):
        self.w = CategoryPopup(EditMode, self)
        self.w.setModal(True)
        self.w.show()


# Start the application    
def main():
    print('Launching ...')
    usage = """usage: %prog [options]
    %prog edits configuration files for the dls-backup-bl.py tool"""
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="Print more details (than necessary in most "
                           "cases...)")

    app = QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)
    win = Editor()
    win.show()
    # catch CTRL-C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec_()


if __name__ == "__main__":
    main()