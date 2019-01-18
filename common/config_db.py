import json
import os
import psycopg2
from psycopg2 import sql as psycopg2_sql


def config_db():
    return json.loads(os.environ['DATABASE_CONFIG'])


def db_conn():
    return psycopg2.connect(**config_db())


def run_query(query, args=None):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(query, args)
    result = cur.fetchone() if cur.description else None
    conn.commit()
    conn.close()
    return result


def table_exists(table_name):
    return run_query(psycopg2_sql.SQL("SELECT to_regclass({});").format(psycopg2_sql.Literal(table_name)))[0] is not None
