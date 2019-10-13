import signal
import sys
from functools import partial
from optparse import OptionParser
from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QIcon, QStandardItemModel, QFont, QStandardItem
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QDesktopWidget,
    QTabWidget, QTableView, QAbstractItemView, QPushButton,
    QHBoxLayout, QFileDialog, QHeaderView, QToolBar, QStatusBar,
    QAction, QVBoxLayout, QStyle, QMessageBox
)

from dls_backup_bl.config import BackupConfig
from .categories import CategoryPopup
from .entries import EntryPopup


# noinspection PyArgumentList,PyUnresolvedReferences,PyAttributeOutsideInit
class Editor(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.config = BackupConfig(Path('test/test_brick.json'))
        self.initialise_ui()

    def centre_window(self):
        # Get the geometry of the widget relative to its parent including any
        # window frame
        FrameGeometry = self.frameGeometry()
        ScreenCentre = QDesktopWidget().availableGeometry().center()
        FrameGeometry.moveCenter(ScreenCentre)
        self.move(FrameGeometry.topLeft())

    # noinspection PyAttributeOutsideInit
    def initialise_ui(self):
        # Set up the window and centre it on the screen  
        self.setWindowTitle('Backup Editor')
        self.MinimumSize = QSize(750, 450)
        self.resize(self.MinimumSize)
        self.setMinimumSize(self.MinimumSize)
        self.setWindowFlags(
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint)

        # self.setWindowIcon(QIcon('icon.png'))
        self.centre_window()

        # Create tab widget
        self.Tabs = QTabWidget()

        # Create individual tabs
        self.PMACTab = QWidget()
        self.TerminalServerTab = QWidget()
        self.ZebraTab = QWidget()

        # Add individual tabs to tab widget
        self.Tabs.addTab(self.PMACTab, "MotorControllers")
        self.Tabs.addTab(self.TerminalServerTab, "TerminalServers")
        self.Tabs.addTab(self.ZebraTab, "Zebras")

        # Create a table for entries
        self.DeviceList = QTableView(self)
        self.DeviceList.verticalHeader().setVisible(False)
        self.DeviceList.setColumnWidth(0, 600)
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
        self.PMACTab.setLayout(self.DeviceLayout)

        # Link the buttons to their actions
        self.Tabs.currentChanged.connect(self.tab_selected)
        self.AddEntryButton.clicked.connect(
            partial(self.open_add_entry_dialog, edit_mode=False))
        self.EditEntryButton.clicked.connect(
            partial(self.open_add_entry_dialog, edit_mode=True))
        self.RemoveEntryButton.clicked.connect(self.remove_entry)

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
        self.OpenAction.triggered.connect(self.show_open_dialog)

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
        self.open_json_file()

        self.display_entries()
        # Display the GUI
        self.show()

    def show_open_dialog(self):
        self.JSONFileName = QFileDialog.getOpenFileName(
            self, 'Open JSON File', '/home', "JSON Files (*.json)")
        self.open_json_file()

    def open_json_file(self):

        # If a file is specified, open it, display the path, and store the
        # location
        if self.JSONFileName:
            self.config.read_json_file()
            self.OpenFileLabel.setText(self.JSONFileName)
            self.EditorSettings.setValue("JSONFilePath", self.JSONFileName)

    def tab_selected(self, arg=None):
        self.display_entries()
        if arg == 0:
            self.PMACTab.setLayout(self.DeviceLayout)
        if arg == 1:
            self.TerminalServerTab.setLayout(self.DeviceLayout)
        if arg == 2:
            self.ZebraTab.setLayout(self.DeviceLayout)

    def display_entries(self):
        self.SelectedDevice = str(self.Tabs.tabText(self.Tabs.currentIndex()))
        self.ListModel = QStandardItemModel()

        for Card in self.config.json_data[self.SelectedDevice]:
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
        self.DeviceList.selectRow(0)

    def button_refresh(self):
        # Record the number of selected category and card entries
        NumCards = len(self.CardList.selectedIndexes())
        NumCategories = len(self.CategoryList.selectedIndexes())

        # Only enable buttons if they can be used (using 0 = False, 1+ = True)
        self.RemoveCategoryButton.setEnabled(NumCategories)
        self.EditCategoryButton.setEnabled(NumCategories)
        self.AddCardButton.setEnabled(NumCategories)
        self.RemoveCardButton.setEnabled(NumCards)
        self.EditCardButton.setEnabled(NumCards)

    def refresh_category_list(self):
        # Create a model for the data
        self.ListModel = QStandardItemModel(self)

        # For every category...
        for Category in self.config.json_data:
            # ...create a list entry including the number of entries
            CategoryTitle = QStandardItem(Category)
            NumEntries = QStandardItem(
                str(len(self.config.json_data[Category])))
            NumEntries.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Add the list entry to the list model
            CategoryListItem = [CategoryTitle, NumEntries]
            self.ListModel.appendRow(CategoryListItem)

        # Update the status bar
        self.StatusBar.showMessage("hello!")

        if self.ListModel.rowCount() < 1:
            self.ListModel.clear()
            self.CategoryList.setModel(self.ListModel)
            self.display_category_cards()

        else:
            self.CategoryList.setModel(self.ListModel)
            self.CategoryList.selectionModel().selectionChanged.connect(
                self.display_category_cards)
            self.CategoryList.model().dataChanged.connect(
                self.display_category_cards)

            self.CategoryList.model().setHeaderData(0, Qt.Horizontal,
                                                    "Title")
            self.CategoryList.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)
            self.CategoryList.model().setHeaderData(1, Qt.Horizontal,
                                                    "Entries")
            self.CategoryList.horizontalHeader().setResizeMode(
                QHeaderView.ResizeToContents)

            if self.LastSelectedCategory is not None:
                self.LastSelectedIndex = self.CategoryList.model().index(
                    self.LastSelectedCategory.row(), 0)
                self.CategoryList.setCurrentIndex(self.LastSelectedIndex)
            else:
                self.FirstItemIndex = self.CategoryList.model().index(0, 0)
                self.CategoryList.setCurrentIndex(self.FirstItemIndex)

                self.CategoryList.resizeColumnsToContents()
                self.NumColumns = self.ListModel.columnCount()

                # Ensure the category list fits the titles but is never
                # narrower than the buttons below
                self.CategoryButtonsWidth = \
                    self.CategoryButtonsLayout.sizeHint().width()

                self.CategoryListWidth = \
                    self.CategoryList.horizontalHeader().length() + 20

                if self.CategoryButtonsWidth < self.CategoryListWidth:
                    self.CategoryList.setFixedWidth(self.CategoryListWidth)
                else:
                    self.CategoryList.setFixedWidth(self.CategoryButtonsWidth)
                self.FirstItemIndex = self.CategoryList.model().index(0, 0)
                self.CategoryList.setCurrentIndex(self.FirstItemIndex)
                self.CategoryList.selectRow(1)
                self.CategoryList.selectRow(0)

    def display_category_cards(self):
        if len(self.CategoryList.selectedIndexes()) > 0:
            self.SelectedCategory = str(
                self.CategoryList.selectedIndexes()[0].data().toString())
        else:
            self.SelectedCategory = ''

        self.LastSelectedCategory = self.CategoryList.currentIndex()
        self.ListModel = QStandardItemModel(self)
        self.ListModel.setHeaderData(0, Qt.Horizontal, 'james')

        HeaderLabels = []

        if self.CategoryList.model().rowCount() > 0:

            for Card in self.config.json_data[self.SelectedCategory]:
                self.Row = []
                for Field in Card:
                    HeaderLabels.append(str(Field))
                    self.Row.append(QStandardItem(Card[str(Field)]))
                self.ListModel.appendRow(self.Row)
            self.CardList.setModel(self.ListModel)

            self.CardList.resizeColumnsToContents()
            self.NumColumns = self.ListModel.columnCount()

            for ColumnNum in range(0, self.NumColumns):
                self.CurrentColumnWidth = self.CardList.columnWidth(ColumnNum)
                self.CardList.setColumnWidth(ColumnNum,
                                             self.CurrentColumnWidth + 20)
            self.CardList.selectionModel().selectionChanged.connect(
                self.button_refresh)
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

        self.button_refresh()

    def remove_entry(self):
        self.SelectedDeviceList = ""
        self.NumColumns = self.DeviceList.model().columnCount()
        self.NumRows = int(
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

        self.MsgBoxResponse = QMessageBox.question(
            self, "Remove?",
            "Are you sure you want to remove:\n" + self.SelectedDeviceList,
            QMessageBox.Yes, QMessageBox.No)
        if self.MsgBoxResponse == QMessageBox.Yes:
            self.SelectedDevice = str(
                self.Tabs.tabText(self.Tabs.currentIndex()))
            self.SelectedIndexes.sort()

            self.LastSelectedRow = self.SelectedIndexes[-1].row()
            for Row in range((self.NumRows - 1), -1, -1):
                self.SelectedRow = self.SelectedIndexes[
                    Row * self.NumColumns].row()
                # print self.SelectedRow
                del self.config.json_data[self.SelectedDevice][self.SelectedRow]
            self.config.write_json_file()
            self.display_entries()

            # If the selected index was the last row in the list
            if self.LastSelectedRow == self.LastRow:
                # Select the new bottom of the list
                self.NewSelectedRow = (self.DeviceList.model().rowCount() - 1)
            else:
                # Otherwise select the same index in the list
                self.NewSelectedRow = self.LastSelectedRow
            # Create an index from this row and set it
            self.NewIndex = self.DeviceList.model().index(
                self.NewSelectedRow, 0)
            self.DeviceList.setCurrentIndex(self.NewIndex)

    def open_add_entry_dialog(self, edit_mode):
        self.AddEntryDialog = EntryPopup(edit_mode, self)
        #      self.w.setGeometry(QRect(100, 100, 400, 200))
        self.AddEntryDialog.show()

    def doit(self, edit_mode):
        self.SelectedIndex = self.CategoryList.selectionModel().currentIndex()
        if str(self.SelectedIndex.data().toString()) == 'Verbs':
            self.w = Verbs.CardPopup(edit_mode, self)
        else:
            self.w = Cards.CardPopup(edit_mode, self)
        self.w.setModal(True)
        self.w.show()

    def doit_cat(self, edit_mode):
        self.w = CategoryPopup(edit_mode, self)
        self.w.setModal(True)
        self.w.show()


# Start the application    
# noinspection PyUnresolvedReferences
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
