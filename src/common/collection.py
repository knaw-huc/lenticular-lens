from json import dumps

from common.config_db import db_conn
from common.helpers import hash_string

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql


class Collection:
    def __init__(self, graphql_endpoint, hsid, dataset_id, collection_id, dataset_name,
                 title, description, collection_info):
        self.graphql_endpoint = graphql_endpoint
        self.hsid = hsid
        self.dataset_id = dataset_id
        self.collection_id = collection_id
        self.dataset_name = dataset_name
        self.title = title
        self.description = description
        self.total = collection_info['total']
        self.properties = collection_info['properties']
        self._table_data = None

    @property
    def columns_sql(self):
        def column_sql(column_name, column_type):
            return psycopg2_sql.SQL('{col_name} {col_type}').format(
                col_name=psycopg2_sql.Identifier(column_name),
                col_type=psycopg2_sql.SQL(column_type),
            )

        columns_sqls = [column_sql('uri', 'text primary key')]
        for name, info in self.columns.items():
            column_name = name
            column_type = 'text[]' if info['isList'] else 'text'
            columns_sqls.append(column_sql(column_name, column_type))

        return psycopg2_sql.SQL(',\n').join(columns_sqls)

    @property
    def columns(self):
        return {hash_string(col_name.lower()): col_info for col_name, col_info in self.properties.items()}

    @property
    def rows_downloaded(self):
        if self.table_data['update_finish_time'] is None or \
                self.table_data['update_finish_time'] < self.table_data['update_start_time']:
            return self.table_data['rows_count']

        return -1

    @property
    def table_name(self):
        if self.hsid:
            return hash_string(self.graphql_endpoint + self.hsid + self.dataset_id + self.collection_id)

        return hash_string(self.graphql_endpoint + self.dataset_id + self.collection_id)

    @property
    def table_data(self):
        if self._table_data:
            return self._table_data

        with db_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM timbuctoo_tables '
                            'WHERE graphql_endpoint = %s AND dataset_id = %s AND collection_id = %s',
                            (self.graphql_endpoint, self.dataset_id, self.collection_id))
                self._table_data = cur.fetchone()

            if not self._table_data:
                with conn.cursor() as cur:
                    cur.execute(psycopg2_sql.SQL('CREATE TABLE {} ({})').format(
                        psycopg2_sql.Identifier(self.table_name),
                        self.columns_sql,
                    ))

                with conn.cursor() as cur:
                    cur.execute('''
                        INSERT INTO timbuctoo_tables (
                            "table_name", graphql_endpoint, hsid, dataset_id, collection_id, 
                            dataset_name, title, description, total, columns, create_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                    ''', (self.table_name, self.graphql_endpoint, self.hsid, self.dataset_id, self.collection_id,
                          self.dataset_name, self.title, self.description, self.total, dumps(self.properties)))

                conn.commit()

                return self.table_data

        return self._table_data
