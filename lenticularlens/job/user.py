from json import dumps
from psycopg.rows import dict_row
from lenticularlens.util.config_db import conn_pool


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
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, name, email, user_data) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO 
                UPDATE SET name = %s, email = %s, user_data = %s
            """, (self.user_id,
                  self.name, self.email, dumps(self.user_data),
                  self.name, self.email, dumps(self.user_data)))

    def register_job(self, job_id, role):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO job_users (job_id, user_id, role)
                VALUES (%s, %s, %s)
            """, (job_id, self.user_id, role))

    def list_jobs(self):
        with conn_pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT jobs.job_id, job_title, job_description, job_link, created_at, updated_at, job_users.role
                FROM jobs
                INNER JOIN job_users
                ON jobs.job_id = job_users.job_id
                AND job_users.user_id = %s
            """, (self.user_id,))
            return cur.fetchall()
