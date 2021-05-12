import sqlite3
import sys, os
from sqlite3 import Error
import csv

from common_structures import GeneralDbWithTree, show_message_box

DB_FILE = 'mydatabase.db'
CSV_TREE_FILE = 'tree_paths2.csv'
# CSV_TREE_FILE = 'tree_paths/geo-Table 1.csv'
CSV_COMMENTS_FILE = 'comments2.csv'
# CSV_COMMENTS_FILE = 'AdjList/simple-Table 1.csv'


class RowForTree(object):
    def __init__(self, row_id, text, nearest_ancestor, level, is_obsolete):
        super().__init__()

        self.row_id = row_id
        self.text = text
        self.parent_id = nearest_ancestor
        self.level = level
        self.is_obsolete = is_obsolete

    def __str__(self):
        return str(self.__dict__)


class Backend(GeneralDbWithTree):
    def __init__(self, tree_view):
        self.db_con = self.sql_connection()
        self.db_cursor = self.db_con.cursor()

        is_ok, msg = self.perform_db_sanity()
        if not is_ok:
            show_message_box(f"DB sanity failed with message: '{msg}'. Will try to recover")
            os.remove(DB_FILE)
            self.db_con = self.sql_connection()
            self.db_cursor = self.db_con.cursor()
            self.reset_items(update_tree_view=False)

        super().__init__(tree_view)

    def perform_db_sanity(self):
        try:
            sum(0 for _ in self.tree_shaped_data)
            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def sql_connection():
        try:
            con = sqlite3.connect(DB_FILE)
            return con
        except Error:
            show_message_box(f"Critical error: {Error}")
            sys.exit(1)

    def reset_items(self, update_tree_view=True):
        self.load_geo_data_from_csv()
        self.load_tree_data_from_csv()
        if update_tree_view:
            self.update_tree_view()

    def load_tree_data_from_csv(self):
        with open(CSV_TREE_FILE, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader)

            self.db_cursor.execute("DROP TABLE IF EXISTS TreePaths")
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS TreePaths(
                    ancestor	INT NOT NULL,
                    descendant	INT NOT NULL,
                    nearest_ancestor    INT NOT NULL,
                    level       INT NOT NULL,
                    PRIMARY KEY (ancestor, descendant),
                    FOREIGN KEY(ancestor)
                        REFERENCES Comments(geo_id),
                    FOREIGN KEY(descendant)
                        REFERENCES Comments(geo_id)
                );
                """)
            self.db_cursor.executemany("INSERT INTO TreePaths VALUES(?, ?, ?, ?)", reader)

            self.db_con.commit()

    def load_comments_data_from_csv(self):
        with open(CSV_COMMENTS_FILE, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader)

            self.db_cursor.execute("DROP TABLE IF EXISTS Comments")
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Comments(
                    geo_id	INT NOT NULL,
                    author	STR NOT NULL,
                    comment    STR NOT NULL,
                    is_obsolete BOOLEAN NOT NULL,
                    PRIMARY KEY (geo_id)
                );
                """)
            self.db_cursor.executemany("INSERT INTO Comments VALUES(?, ?, ?, ?)", reader)

            self.db_con.commit()

    def load_geo_data_from_csv(self):
        with open(CSV_COMMENTS_FILE, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            next(reader)

            self.db_cursor.execute("DROP TABLE IF EXISTS Comments")
            self.db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Comments(
                    geo_id	INT NOT NULL,
                    text    STR NOT NULL,
                    is_obsolete BOOLEAN NOT NULL,
                    PRIMARY KEY (geo_id)
                );
                """)
            self.db_cursor.executemany("INSERT INTO Comments VALUES(?, ?, ?)", reader)

            self.db_con.commit()

    def get_row_by_id(self, descendant_id):
        query = """
            SELECT 
                Comments.geo_id,
                Comments.text,
                TreePaths.nearest_ancestor,
                TreePaths.level,
                Comments.is_obsolete
            FROM `Comments`
            JOIN `TreePaths`
            ON `Comments`.`geo_id` = `TreePaths`.`descendant`
            WHERE `TreePaths`.`descendant` = ?
            LIMIT 1
            """
        self.db_cursor.execute(query, [descendant_id])
        data = self.db_cursor.fetchone()
        row = RowForTree(*data)
        return row

    @property
    def tree_shaped_data(self):
        for row in self.get_tree():
            yield row

    def get_tree(self, root_id=1):
        query = """
            SELECT 
                Comments.geo_id,
                Comments.text,
                TreePaths.nearest_ancestor,
                TreePaths.level,
                Comments.is_obsolete
            FROM `Comments`
            JOIN `TreePaths`
            ON `Comments`.`geo_id` = `TreePaths`.`descendant`
            WHERE `TreePaths`.`ancestor` = ?
            ORDER BY TreePaths.level, TreePaths.nearest_ancestor
            """
        self.db_cursor.execute(query, [root_id])
        tree_data = self.db_cursor.fetchall()

        """
        header = ('geo_id', 'author', 'comment', 'nearest_ancestor', 'level')
        tree_dict = [dict(zip(header, row)) for row in tree_data]
        """

        tree_rows = [RowForTree(*row_data) for row_data in tree_data]

        return tree_rows

    def add_new_row(self, row):
        q_new_row = """
            INSERT INTO 'Comments' VALUES(?, ?, ?)
        """
        print(q_new_row)
        data = (row.row_id, row.text, 0)
        print(data)
        self.db_cursor.execute(q_new_row, data)

        q_new_tree = f"""
            INSERT INTO TreePaths (ancestor, descendant, nearest_ancestor, level)
                SELECT ancestor, '{row.row_id}', '{row.parent_id}', {row.level} FROM TreePaths
                WHERE descendant = '{row.parent_id}'
                UNION ALL SELECT '{row.row_id}', '{row.row_id}', '{row.parent_id}', {row.level};
            """
        print(q_new_tree)

        self.db_cursor.execute(q_new_tree)

    def update_rows(self, rows):
        query = f"""
            UPDATE Comments
            SET text = ?
            WHERE geo_id = ?;
            """
        data = [(row.text, row.row_id) for row in rows]
        print(f"Will update following rows {data}")
        self.db_cursor.executemany(query, data)

    def delete_id(self, _id):
        query = f"""
            UPDATE Comments
            SET is_obsolete = 1
            WHERE geo_id in 
                (SELECT descendant FROM TreePaths
                    WHERE ancestor = ?)
            """
        self.db_cursor.execute(query, [_id])

    def get_obsolete_ids_in_id_list(self, ids_to_check):
        placeholder = '?'  # For SQLite. See DBAPI paramstyle.
        placeholders = ', '.join(placeholder for _ in ids_to_check)

        query = f"""
            SELECT geo_id FROM Comments
                WHERE is_obsolete = 1 AND geo_id IN ({placeholders})
            """
        self.db_cursor.execute(query, ids_to_check)
        obsolete_in_list = self.db_cursor.fetchall()
        print(f"obsolete_in_list is {obsolete_in_list}")
        cached_obsolete_ids = [t[0] for t in obsolete_in_list]
        return cached_obsolete_ids

    def sync_cache(self, rows_with_any_update, all_cached_ids):
        rows_with_text_update = []
        rows_became_obsolete = []
        for row in rows_with_any_update:
            if row.is_new:
                self.add_new_row(row)
            else:
                rows_with_text_update.append(row)
            if row.is_obsolete:
                rows_became_obsolete.append(row)

        self.update_rows(rows_with_text_update)

        for row in rows_became_obsolete:
            self.delete_id(row.row_id)

        self.db_con.commit()
        self.update_tree_view()

        obsolete_ids_in_cache = self.get_obsolete_ids_in_id_list(all_cached_ids)

        return obsolete_ids_in_cache
