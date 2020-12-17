from json import dumps

from ll.util.helpers import hash_string
from ll.data.timbuctoo import Timbuctoo
from ll.util.config_db import db_conn, fetch_one

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql


class Collection:
    def __init__(self, graphql_endpoint, hsid, dataset_id, collection_id, timbuctoo_data=None):
        self._graphql_endpoint = graphql_endpoint
        self._hsid = hsid
        self._dataset_id = dataset_id
        self._collection_id = collection_id
        self._timbuctoo_data = timbuctoo_data

        self._table_data = None
        self._timbuctoo = Timbuctoo(self._graphql_endpoint, self._hsid)

    @property
    def table_data(self):
        if self._table_data:
            return self._table_data

        self._table_data = fetch_one('SELECT * FROM timbuctoo_tables '
                                     'WHERE graphql_endpoint = %s AND dataset_id = %s AND collection_id = %s',
                                     (self._graphql_endpoint, self._dataset_id, self._collection_id), dict=True)

        if not self._table_data:
            self.start_download()
            return self.table_data

        return self._table_data

    @property
    def table_name(self):
        return hash_string(self._graphql_endpoint + self._dataset_id + self._collection_id)

    @property
    def columns(self):
        return self.table_data['columns']

    @property
    def rows_downloaded(self):
        if self.table_data['update_finish_time'] is None or \
                self.table_data['update_finish_time'] < self.table_data['update_start_time']:
            return self.table_data['rows_count']

        return -1

    @property
    def timbuctoo_data(self):
        if not self._timbuctoo_data:
            self._timbuctoo_data = self._timbuctoo.datasets

        return self._timbuctoo_data

    @property
    def timbuctoo_dataset_and_collection(self):
        dataset = None
        collection = None

        for dataset_id, dataset_data in self.timbuctoo_data.items():
            if dataset_id == self._dataset_id:
                dataset = dataset_data
                for collection_id, collection_data in dataset_data['collections'].items():
                    if collection_id == self._collection_id:
                        collection = collection_data
                        break
                break

        return dataset, collection

    def start_download(self):
        (dataset, collection) = self.timbuctoo_dataset_and_collection
        if dataset and collection:
            columns = {'uri' if col_name == 'uri' else hash_string(col_name.lower()): col_info
                       for col_name, col_info in collection['properties'].items()}

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(psycopg2_sql.SQL('CREATE TABLE {} ({})').format(
                    psycopg2_sql.Identifier(self.table_name),
                    self.columns_sql(columns),
                ))

                cur.execute('''
                    INSERT INTO timbuctoo_tables (
                        "table_name", graphql_endpoint, hsid, dataset_id, collection_id, 
                        dataset_uri, dataset_name, title, description, 
                        collection_uri, collection_title, collection_shortened_uri, 
                        total, columns, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ''', (self.table_name, self._graphql_endpoint, self._hsid, self._dataset_id, self._collection_id,
                      dataset['uri'], dataset['name'], dataset['title'], dataset['description'],
                      collection['uri'], collection['title'], collection['shortenedUri'],
                      collection['total'], dumps(columns)))

    def update(self):
        (dataset, collection) = self.timbuctoo_dataset_and_collection
        if dataset and collection:
            columns = {'uri' if col_name == 'uri' else hash_string(col_name.lower()): col_info
                       for col_name, col_info in collection['properties'].items()}

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                    UPDATE timbuctoo_tables
                    SET dataset_uri = %s, dataset_name = %s, title = %s, description = %s, 
                        collection_uri = %s, collection_title = %s, collection_shortened_uri = %s,
                        total = %s, columns = %s
                    WHERE "table_name" = %s
                ''', (dataset['uri'], dataset['name'], dataset['title'], dataset['description'],
                      collection['uri'], collection['title'], collection['shortenedUri'],
                      collection['total'], dumps(columns), self.table_name))

    @staticmethod
    def columns_sql(columns):
        def column_sql(column_name, column_type):
            return psycopg2_sql.SQL('{col_name} {col_type}').format(
                col_name=psycopg2_sql.Identifier(column_name),
                col_type=psycopg2_sql.SQL(column_type),
            )

        columns_sqls = [column_sql('uri', 'text primary key')]
        for name, info in columns.items():
            if name != 'uri':
                column_name = name
                column_type = 'text[]' if info['isList'] else 'text'
                columns_sqls.append(column_sql(column_name, column_type))

        return psycopg2_sql.SQL(',\n').join(columns_sqls)

    @staticmethod
    def download_status():
        collections = {'downloaded': [], 'downloading': []}

        with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute('SELECT dataset_id, collection_id, total, rows_count FROM timbuctoo_tables')

            for table in cur:
                data_info = {
                    'dataset_id': table['dataset_id'],
                    'collection_id': table['collection_id'],
                    'total': table['total'],
                    'rows_count': table['rows_count'],
                }

                if table['total'] == table['rows_count']:
                    collections['downloaded'].append(data_info)
                else:
                    collections['downloading'].append(data_info)

        return collections
