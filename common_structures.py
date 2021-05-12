from PyQt5.Qt import QStandardItemModel, QStandardItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

COLOR_OBSOLETE = QColor(128, 0, 0)


def show_message_box(text):
    message_box = QMessageBox()
    message_box.setText(text)
    message_box.exec()


class SimpleStandardItem(QStandardItem):
    def __init__(self, row_id, text, is_obsolete):
        super().__init__()
        self.row_id = row_id
        self.setText(text)

        if is_obsolete:
            self.setForeground(COLOR_OBSOLETE)
            self.setFlags(self.flags() & ~Qt.ItemIsEnabled)

        self.setEditable(False)

    def __str__(self):
        return str(self.__dict__)


class GeneralDbWithTree(object):
    def __init__(self, tree_view):
        self.tree_view = tree_view
        self.tree_model = None
        self.tree_items = {}

        self.update_tree_view()

    @property
    def tree_shaped_data(self):
        raise NotImplemented

    def get_row_by_id(self, _id):
        raise NotImplemented

    def get_selected_row(self):
        view_index = self.tree_view.currentIndex()
        model_item = self.tree_model.itemFromIndex(view_index)
        if model_item is None:
            return None
        return self.get_row_by_id(model_item.row_id)

    def init_model_and_items_dict(self):
        self.tree_model = QStandardItemModel()
        self.tree_items = {0: self.tree_model.invisibleRootItem()}

    def init_view(self):
        self.tree_view.setModel(self.tree_model)
        self.tree_view.expandAll()

    def update_tree_view(self):
        self.init_model_and_items_dict()

        for row in self.tree_shaped_data:
            _id = row.row_id
            new_item = SimpleStandardItem(row_id=row.row_id, text=str(row.text), is_obsolete=row.is_obsolete)
            self.tree_items[_id] = new_item
            parent_node = self.tree_items.get(row.parent_id)
            if parent_node is None:
                parent_node = self.tree_items.get(0)
            parent_node.appendRow(new_item)

        self.init_view()
