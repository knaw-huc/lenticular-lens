from json import dumps
from common.config_db import db_conn
from common.helpers import hash_string
from common.timbuctoo import Timbuctoo
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql


class Collection:
    def __init__(self, dataset_id, collection_id, columns):
        self.collection_id = collection_id
        self.dataset_id = dataset_id
        self.graph_columns = columns

    @property
    def columns_sql(self):
        def column_sql(column_name, column_type):
            return psycopg2_sql.SQL('{col_name} {col_type}').format(
                col_name=psycopg2_sql.Identifier(column_name),
                col_type=psycopg2_sql.SQL(column_type),
            )

        columns_sqls = []
        for name, info in self.columns.items():
            if info['name'] == 'uri':
                columns_sqls.append(column_sql('uri', 'text primary key'))

            column_name = name
            column_type = 'jsonb' if info['LIST'] else 'text'
            columns_sqls.append(column_sql(column_name, column_type))

        return psycopg2_sql.SQL(',\n').join(columns_sqls)

    @property
    def columns(self):
        return Timbuctoo.columns(self.graph_columns)

    @property
    def rows_downloaded(self):
        return self.table_data['rows_count']\
            if self.table_data['update_finish_time'] is None or self.table_data['update_finish_time'] < self.table_data['update_start_time']\
            else -1

    @property
    def table_name(self):
        return hash_string(self.dataset_id + self.collection_id)

    @property
    def table_data(self):
        with db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")
                cur.execute('SELECT * FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
                                   (self.dataset_id, self.collection_id))
                table_data = cur.fetchone()

            if not table_data:
                with conn.cursor() as cur:
                    cur.execute(psycopg2_sql.SQL('CREATE TABLE {} ({})').format(
                        psycopg2_sql.Identifier(self.table_name),
                        self.columns_sql,
                    ))

                with conn.cursor() as cur:
                    cur.execute(
                        '''INSERT INTO timbuctoo_tables
                            ("table_name", dataset_id, collection_id, columns, create_time)
                            VALUES (%s, %s, %s, %s, now())''',
                        (self.table_name, self.dataset_id, self.collection_id, dumps(self.columns)))

                conn.commit()

                return self.table_data

        return table_data
