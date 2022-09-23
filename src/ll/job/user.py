from json import dumps
from ll.util.config_db import db_conn


class User:
    def __init__(self, user_data):
        self.user_data = user_data

    @property
    def user_id(self):
        return self.user_data.get('sub')

    @property
    def name(self):
        return self.user_data.get('nickname')

    @property
    def email(self):
        return self.user_data.get('email')

    def persist_data(self):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, name, email, user_data) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO 
                UPDATE SET name = %s, email = %s, user_data = %s
            """, (self.user_id,
                  self.name, self.email, dumps(self.user_data),
                  self.name, self.email, dumps(self.user_data)))
