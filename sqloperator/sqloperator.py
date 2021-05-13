import sqlite3
import os
from kivymd.app import MDApp
app = MDApp.get_running_app()


class SqlOperator:
    def __init__(self):
        self.storage_dir = os.path.join(
            getattr(app, 'user_data_dir'), 'database')
        if not os.path.isdir(self.storage_dir):
            os.makedirs(self.storage_dir)
        self.PATH = os.path.join(self.storage_dir, 'user_db.db')
        self.create_tables()

    def create_tables(self):
        users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            salt TEXT NOT NULL,
            avatar TEXT NOT NULL,
            key TEXT NOT NULL
        )
        """
        accounts = """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY NOT NULL,
            user INTEGER NOT NULL,
            name TEXT NOT NULL,
            pinned BOOLEAN NOT NULL,
            FOREIGN KEY (user) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        passwords = """
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY NOT NULL,
            user INTEGER NOT NULL,
            account INTEGER NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            strength TEXT NOT NULL,
            color TEXT NOT NULL,
            FOREIGN KEY (user) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (account) REFERENCES accounts (id) ON DELETE CASCADE
        )
        """

        self.execute_query(users)
        self.execute_query(accounts)
        self.execute_query(passwords)

        columns = [i[1]
                   for i in self.execute_read_query("PRAGMA table_info (users)")]
        if columns != ['id', 'name', 'salt', 'avatar', 'key']:
            self.execute_query("DROP TABLE IF EXISTS users")
            self.create_tables()

        columns = [i[1] for i in self.execute_read_query(
            "PRAGMA table_info (accounts)")]
        if columns != ['id', 'user', 'name', 'pinned']:
            self.execute_query("DROP TABLE IF EXISTS accounts")
            self.create_tables()

        columns = [i[1] for i in self.execute_read_query(
            "PRAGMA table_info (passwords)")]
        if columns != ['id', 'user', 'account', 'username', 'password', 'strength', 'color']:
            self.execute_query("DROP TABLE IF EXISTS passwords")
            self.create_tables()

    def create_connection(self):
        if not os.path.isdir(self.storage_dir):
            os.makedirs(self.storage_dir)
        connection = None
        try:
            connection = sqlite3.connect(self.PATH, timeout=10)
        except BaseException as e:
            app.logger.error('App: ' + str(e))
        return connection

    def execute_query(self, query, values=()):
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query, values)
            connection.commit()
            connection.close()
            return True
        except BaseException as e:
            app.logger.error('App: ' + str(e))
            connection.close()
            return False

    def execute_read_query(self, query, values=()):
        connection = self.create_connection()
        cursor = connection.cursor()
        result = None
        try:
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(query, values)
            result = cursor.fetchall()
            connection.commit()
            connection.close()
            return result
        except BaseException as e:
            app.logger.error('App: ' + str(e))
            connection.close()
