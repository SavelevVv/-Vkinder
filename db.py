import sqlite3


class DB:
    def __init__(self):
        self.connection = sqlite3.connect("my_profiles.db")
        self._create_table_seen_person()

    def _create_table_seen_person(self):
        """create table seen_person"""
        cur = self.connection.cursor()
        cur.execute(
            """
                    CREATE TABLE IF NOT EXISTS
                    seen_person(
                        id integer PRIMARY KEY,
                        user_id text NOT NULL,
                        vk_id text NOT NULL
                    );
                """
        )
        cur.close()

    def insert(self, user_id, profile_id):
        """inserting data into the seen_users table"""
        cur = self.connection.cursor()
        cur.execute(
            """
                    INSERT
                    INTO seen_person (user_id, vk_id)
                    VALUES (%s, %s)
                """
            % (user_id, profile_id),
        )
        self.connection.commit()
        cur.close()

    def check_profile(self, user_id):
        cur = self.connection.cursor()
        cur.execute(
            """
                    SELECT s.vk_id
                    FROM seen_person AS s
                    WHERE user_id = '%s';
                """
            % user_id
        )
        _data = cur.fetchall()
        cur.close()
        return _data

    def delete(self, user_id):
        """
        delete table seen_person by cascade
        """
        cur = self.connection.cursor()
        cur.execute(
            """
                    DELETE
                    FROM seen_person
                    WHERE user_id = '%s';
            """
            % user_id
        )
        self.connection.commit()
        cur.close()


_my_db = DB()


def get_db():
    """
    return class DB for work with DB
    """
    return _my_db
