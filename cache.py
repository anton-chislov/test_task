import time
import uuid
import heapq

from common_structures import GeneralDbWithTree


class CachedRow(object):
    def __init__(self, row_id, parent_id, text, level, is_obsolete, is_new):
        super().__init__()

        self.row_id = row_id
        self.parent_id = parent_id

        self._text = None
        self.text = text

        self._level = level

        self._is_obsolete = None
        self.is_obsolete = is_obsolete

        self._is_new = is_new

        self._last_updated = time.time() if self.is_new else 0
        self._last_synced = 0

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._last_updated = time.time()

    @property
    def is_obsolete(self):
        return self._is_obsolete

    @is_obsolete.setter
    def is_obsolete(self, value):
        self._is_obsolete = value
        self._last_updated = time.time()

    @property
    def is_synced(self):
        return self._last_synced >= self._last_updated and not self.is_new

    def set_sync_succeed(self):
        self._is_new = False
        self._last_synced = time.time()

    @property
    def is_new(self):
        return self._is_new

    @property
    def level(self):
        return self._level

    def __lt__(self, other):
        return self.level <= other.level

    def __str__(self):
        return str(self.__dict__)


class CacheWithTree(GeneralDbWithTree):
    def __init__(self, tree_view, backend):
        self.rows = {}

        self.backend = backend

        super().__init__(tree_view)

    @staticmethod
    def _get_new_id_for_row():
        return str(uuid.uuid4())

    def get_row_by_id(self, _id):
        return self.rows[_id]

    @property
    def tree_shaped_data(self):
        tree_shaped_data = list(self.rows.values())
        heapq.heapify(tree_shaped_data)
        while tree_shaped_data:
            yield heapq.heappop(tree_shaped_data)

    def reset_items(self):
        self.rows = {}
        self.init_model_and_items_dict()
        self.init_view()

    def cache_row(self, row_id, parent_id, text, level):
        new_row = CachedRow(row_id=row_id, parent_id=parent_id, text=text, level=level,
                            is_obsolete=False, is_new=False)
        self.rows[new_row.row_id] = new_row
        self.update_tree_view()

    def create_row(self, parent_id, text):
        row_id = self._get_new_id_for_row()
        level = self.rows[parent_id].level + 1
        new_row = CachedRow(row_id=row_id, parent_id=parent_id, text=text, level=level,
                            is_obsolete=False, is_new=True)
        self.rows[new_row.row_id] = new_row
        self.update_tree_view()

    def edit_row(self, row_id, text):
        self.rows[row_id].text = text
        self.update_tree_view()

    def delete_row(self, row_id):
        self.rows[row_id].is_obsolete = True
        self.update_tree_view()

    def push_cache_to_db(self):
        rows_with_any_update = []
        all_cached_ids = []

        for row in self.rows.values():
            if not row.is_synced:
                rows_with_any_update.append(row)
            all_cached_ids.append(row.row_id)

        obsolete_ids_in_cache = self.backend.sync_cache(rows_with_any_update, all_cached_ids)

        for row_id in obsolete_ids_in_cache:
            self.rows[row_id].is_obsolete = True
            self.rows[row_id].set_sync_succeed()

        for row in rows_with_any_update:
            row.set_sync_succeed()

        self.update_tree_view()

