from functools import partial
from logging import getLogger
from pathlib import Path

from PyQt5.QtCore import QRect, QSettings, QSize, Qt
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDesktopWidget,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from dls_backup_bl.config import BackupsConfig

from .entries import EntryPopup

log = getLogger(__name__)


# noinspection PyArgumentList, PyAttributeOutsideInit
class BackupEditor(QWidget):
    def __init__(self, config_file: Path):
        QWidget.__init__(self)
        self.file = config_file
        self.config = BackupsConfig.from_json(config_file)
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
        self.setWindowTitle("Backup Editor")
        self.MinimumSize = QSize(750, 450)
        self.resize(self.MinimumSize)
        self.setMinimumSize(self.MinimumSize)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        # self.setWindowIcon(QIcon('icon.png'))
        self.centre_window()

        # Create tab widget
        self.Tabs = QTabWidget()

        self.tab_widgets = []
        self.tab_names = []
        self.tab_entry_type = []
        # Create and add individual tabs to tab widget
        for i, tab_name in enumerate(self.config.keys()):
            w = QWidget()
            self.tab_widgets.append(w)
            self.tab_names.append(tab_name)
            self.tab_entry_type.append(BackupsConfig.my_types()[i])
            self.Tabs.addTab(w, tab_name)

        # Create a table for entries
        self.DeviceList = QTableView(self)
        self.DeviceList.verticalHeader().setVisible(False)
        self.DeviceList.setColumnWidth(0, 600)
        self.DeviceList.setShowGrid(False)
        self.DeviceList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.DeviceList.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Create an Add Entry button
        self.AddEntryButton = QPushButton("New", self)
        self.AddEntryButton.setIconSize(QSize(24, 24))

        # Create a Remove Entry button
        self.RemoveEntryButton = QPushButton("Delete", self)
        self.RemoveEntryButton.setIconSize(QSize(24, 24))

        # Create an Edit Entry button
        self.EditEntryButton = QPushButton("Edit", self)
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
        self.tab_widgets[0].setLayout(self.DeviceLayout)

        # Link the buttons to their actions
        self.Tabs.currentChanged.connect(self.tab_selected)
        self.AddEntryButton.clicked.connect(
            partial(self.open_add_entry_dialog, edit_mode=False)
        )
        self.EditEntryButton.clicked.connect(
            partial(self.open_add_entry_dialog, edit_mode=True)
        )
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
        self.OpenFileLabel.setText(str(self.file))
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

        self.display_entries()
        # Display the GUI
        self.show()

    def tab_selected(self, arg=None):
        self.display_entries()
        self.tab_widgets[arg].setLayout(self.DeviceLayout)

    def display_entries(self):
        self.SelectedDevice = str(self.Tabs.tabText(self.Tabs.currentIndex()))

        data_type = self.tab_entry_type[self.Tabs.currentIndex()]
        self.ListModel = QStandardItemModel()
        self.ListModel.setHorizontalHeaderLabels(data_type.keys())

        for device in self.config[self.SelectedDevice]:
            self.Row = []
            for Field in device.keys():
                self.Row.append(QStandardItem(str(device[Field])))
            self.ListModel.appendRow(self.Row)
        self.DeviceList.setModel(self.ListModel)
        self.DeviceList.resizeColumnsToContents()
        self.NumColumns = self.ListModel.columnCount()

        for ColumnNum in range(0, self.NumColumns):
            self.CurrentColumnWidth = self.DeviceList.columnWidth(ColumnNum)
            self.DeviceList.setColumnWidth(ColumnNum, self.CurrentColumnWidth + 20)
        self.DeviceList.selectRow(0)
        self.button_refresh()

    def button_refresh(self):
        num_entries = len(self.DeviceList.selectedIndexes())

        # Only enable buttons if they can be used (using 0 = False, 1+ = True)
        self.AddEntryButton.setEnabled(1)
        self.RemoveEntryButton.setEnabled(num_entries)
        self.EditEntryButton.setEnabled(num_entries)

    def remove_entry(self):
        self.SelectedDeviceList = ""
        self.NumColumns = self.DeviceList.model().columnCount()
        self.NumRows = int(len(self.DeviceList.selectedIndexes()) / self.NumColumns)
        self.SelectedIndexes = self.DeviceList.selectedIndexes()
        for Row in range(0, self.NumRows):
            self.RowString = ""
            self.SelectedRow = self.SelectedIndexes[Row * self.NumColumns].row()
            for Column in range(0, self.NumColumns):
                self.RowString = (
                    self.RowString
                    + self.DeviceList.model().item(self.SelectedRow, Column).text()
                    + "\t"
                )
            self.SelectedDeviceList = self.SelectedDeviceList + "\n" + self.RowString
        # Find the number of rows before a removal
        self.LastRow = self.DeviceList.model().rowCount() - 1

        self.MsgBoxResponse = QMessageBox.question(
            self,
            "Remove?",
            "Are you sure you want to remove:\n" + self.SelectedDeviceList,
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if self.MsgBoxResponse == QMessageBox.Yes:
            self.SelectedDevice = str(self.Tabs.tabText(self.Tabs.currentIndex()))
            self.SelectedIndexes.sort()

            self.LastSelectedRow = self.SelectedIndexes[-1].row()
            for Row in range((self.NumRows - 1), -1, -1):
                self.SelectedRow = self.SelectedIndexes[Row * self.NumColumns].row()
                # print self.SelectedRow
                del self.config[self.SelectedDevice][self.SelectedRow]
            self.config.save(self.file)
            self.display_entries()

            # If the selected index was the last row in the list
            if self.LastSelectedRow == self.LastRow:
                # Select the new bottom of the list
                self.NewSelectedRow = self.DeviceList.model().rowCount() - 1
            else:
                # Otherwise select the same index in the list
                self.NewSelectedRow = self.LastSelectedRow
            # Create an index from this row and set it
            self.NewIndex = self.DeviceList.model().index(self.NewSelectedRow, 0)
            self.DeviceList.setCurrentIndex(self.NewIndex)

    def open_add_entry_dialog(self, edit_mode):
        self.AddEntryDialog = EntryPopup(edit_mode, self)
        self.AddEntryDialog.setGeometry(QRect(self.x(), self.y(), 400, 200))
        self.AddEntryDialog.show()
