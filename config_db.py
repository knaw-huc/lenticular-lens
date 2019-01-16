from configparser import ConfigParser
import psycopg2
from psycopg2 import sql as psycopg2_sql


def config_db(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


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
