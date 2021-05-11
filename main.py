import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QPushButton, QDialog, QLineEdit, QVBoxLayout
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtCore import Qt

from backend import Backend
from cache import CacheWithTree
from common_structures import show_message_box


class TextDialog(QDialog):
    def __init__(self, parent=None, init_text=''):
        super(TextDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        '''
        # nice widget for editing the date
        self.datetime = QDateTimeEdit(self)
        self.datetime.setCalendarPopup(True)
        self.datetime.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self.datetime)
        '''

        self.edit_capton = QLineEdit(self)
        self.edit_capton.setText(init_text)
        layout.addWidget(self.edit_capton)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    # get current date and time from the dialog
    def editedText(self):
        return self.edit_capton.text()
        # return self.datetime.dateTime()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getDateTime(parent=None, init_text=''):
        dialog = TextDialog(parent, init_text)
        result = dialog.exec_()
        text = dialog.editedText()
        return text, result == QDialog.Accepted


class AppDemo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('World Country Diagram')
        self.resize(700, 410)

        self.backend_tree_view = QTreeView(self)
        self.backend_tree_view.setGeometry(390, 10, 300, 350)
        # self.reset_db_items()
        self.backend = Backend(self.backend_tree_view)
        # self.backend.reset_items()

        self.cache_tree_view = QTreeView(self)
        self.cache_tree_view.setGeometry(10, 10, 300, 350)
        self.cache = CacheWithTree(self.cache_tree_view, self.backend)
        self.cache.reset_items()

        cache_item_button = QPushButton("<<<", self)
        cache_item_button.clicked.connect(self.cache_item)
        cache_item_button.setGeometry(320, 60, 60, 40)

        add_button = QPushButton("+", self)
        add_button.clicked.connect(self.add_item)
        add_button.setGeometry(10, 360, 60, 40)

        del_button = QPushButton("-", self)
        del_button.clicked.connect(self.delete_item)
        del_button.setGeometry(60, 360, 60, 40)

        edit_button = QPushButton("Edit", self)
        edit_button.clicked.connect(self.edit_item)
        edit_button.setGeometry(110, 360, 60, 40)

        apply_button = QPushButton("Apply", self)
        apply_button.clicked.connect(self.apply_items)
        apply_button.setGeometry(190, 360, 60, 40)

        reset_button = QPushButton("Reset", self)
        reset_button.clicked.connect(self.reset_all_items)
        reset_button.setGeometry(240, 360, 60, 40)
        # self.setCentralWidget(self.treeView)

    def reset_all_items(self):
        self.backend.reset_items()
        # self.reset_db_items()
        self.cache.reset_items()

    def cache_item(self):
        row = self.backend.get_selected_row()
        if row is None:
            return show_message_box("No backend item selected")

        self.cache.cache_row(row_id=row.row_id, parent_id=row.parent_id, text=row.text, level=row.level)

    def apply_items(self):
        self.cache.push_cache_to_db()



    def edit_item(self):
        row = self.cache.get_selected_row()
        if row is None:
            return show_message_box("No cache item selected")

        init_text = row.text
        text, ok = TextDialog.getDateTime(parent=self, init_text=init_text)
        print("{} {}".format(text, ok))

        if ok and text != init_text:    
            self.cache.edit_row(row.row_id, text)

    def add_item(self):
        row = self.cache.get_selected_row()
        if row is None:
            return show_message_box("No cache item selected")
        text, ok = TextDialog.getDateTime(parent=self, init_text='')
        print("{} {}".format(text, ok))

        if ok:
            self.cache.create_row(row.row_id, text)

    def delete_item(self, item):
        row = self.cache.get_selected_row()
        if row is None:
            return show_message_box("No cache item selected")
        self.cache.delete_row(row.row_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    demo = AppDemo()
    demo.show()

    sys.exit(app.exec_())