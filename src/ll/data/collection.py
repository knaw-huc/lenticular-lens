from json import dumps
from psycopg2 import sql, extras

from ll.data.timbuctoo import Timbuctoo
from ll.util.config_db import db_conn
from ll.util.hasher import table_name_hash, column_name_hash, hash_string_min


class Collection:
    def __init__(self, graphql_endpoint, dataset_id, collection_id, timbuctoo_data=None, dataset_table_data=None):
        self.graphql_endpoint = graphql_endpoint
        self.dataset_id = dataset_id
        self.collection_id = collection_id

        self._timbuctoo_data = timbuctoo_data
        self._dataset_table_data = dataset_table_data

        self._timbuctoo = Timbuctoo(self.graphql_endpoint)

    @property
    def dataset_table_data(self):
        if self._dataset_table_data:
            return self._dataset_table_data

        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM timbuctoo_tables WHERE graphql_endpoint = %s AND dataset_id = %s',
                        (self.graphql_endpoint, self.dataset_id))
            self._dataset_table_data = {table_data['collection_id']: table_data for table_data in cur.fetchall()}

        return self._dataset_table_data

    @property
    def table_data(self):
        if self.collection_id not in self.dataset_table_data:
            self.start_download()
            return self.table_data

        return self.dataset_table_data[self.collection_id]

    @property
    def table_name(self):
        return table_name_hash(self.graphql_endpoint, self.dataset_id, self.collection_id)

    @property
    def alias(self):
        return hash_string_min(self.table_name)

    @property
    def columns(self):
        return self.table_data['columns']

    @property
    def uri_prefix_mappings(self):
        return self.table_data['uri_prefix_mappings']

    @property
    def prefix_info(self):
        uri = self.table_data['collection_uri']
        short_uri = self.table_data['collection_shortened_uri']

        prefix = short_uri[:short_uri.index(':')] if uri != short_uri and ':' in short_uri else None
        prefix_uri = self.table_data['prefix_mappings'][prefix] \
            if prefix and prefix in self.table_data['prefix_mappings'] else None

        return prefix, prefix_uri

    @property
    def is_downloaded(self):
        if self.collection_id not in self.dataset_table_data:
            return False

        return self.table_data['update_finish_time'] \
               and self.table_data['update_finish_time'] >= self.table_data['update_start_time']

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
            if dataset_id == self.dataset_id:
                dataset = dataset_data
                for collection_id, collection_data in dataset_data['collections'].items():
                    if collection_id == self.collection_id:
                        collection = collection_data
                        break
                break

        return dataset, collection

    def start_download(self):
        (dataset, collection) = self.timbuctoo_dataset_and_collection
        if dataset and collection:
            columns = {column_name_hash(col_name): col_info
                       for col_name, col_info in collection['properties'].items()}

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(sql.SQL('CREATE TABLE timbuctoo.{} ({})').format(
                    sql.Identifier(self.table_name),
                    self.columns_sql(columns),
                ))

                cur.execute('''
                    INSERT INTO timbuctoo_tables (
                        "table_name", graphql_endpoint, dataset_id, collection_id, 
                        dataset_uri, dataset_name, title, description, 
                        collection_uri, collection_title, collection_shortened_uri, 
                        total, columns, prefix_mappings, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ''', (self.table_name, self.graphql_endpoint, self.dataset_id, self.collection_id,
                      dataset['uri'], dataset['name'], dataset['title'], dataset['description'],
                      collection['uri'], collection['title'], collection['shortenedUri'],
                      collection['total'], dumps(columns), dumps(dataset['prefixMappings'])))

    def update(self):
        (dataset, collection) = self.timbuctoo_dataset_and_collection
        if dataset and collection:
            columns = {column_name_hash(col_name): col_info for col_name, col_info in collection['properties'].items()}

            with db_conn() as conn, conn.cursor() as cur:
                cur.execute('''
                    UPDATE timbuctoo_tables
                    SET dataset_uri = %s, dataset_name = %s, title = %s, description = %s, 
                        collection_uri = %s, collection_title = %s, collection_shortened_uri = %s,
                        total = %s, columns = %s, prefix_mappings = %s
                    WHERE "table_name" = %s
                ''', (dataset['uri'], dataset['name'], dataset['title'], dataset['description'],
                      collection['uri'], collection['title'], collection['shortenedUri'],
                      collection['total'], dumps(columns), dumps(dataset['prefixMappings']), self.table_name))

    def get_collection_by_id(self, collection_id):
        return Collection(self.graphql_endpoint, self.dataset_id, collection_id,
                          self._timbuctoo_data, self._dataset_table_data)

    @staticmethod
    def columns_sql(columns):
        def column_sql(column_name, column_type):
            return sql.SQL('{col_name} {col_type}').format(
                col_name=sql.Identifier(column_name),
                col_type=sql.SQL(column_type),
            )

        columns_sqls = [column_sql('uri', 'text primary key')]
        for name, info in columns.items():
            if name != 'uri':
                column_name = name
                column_type = 'text[]' if info['isList'] else 'text'
                columns_sqls.append(column_sql(column_name, column_type))

        return sql.SQL(',\n').join(columns_sqls)

    @staticmethod
    def download_status():
        collections = {'downloaded': [], 'downloading': []}

        with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
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

    def __eq__(self, other):
        return isinstance(other, Collection) and hash(self) == hash(other)

    def __hash__(self):
        return hash(self.graphql_endpoint) ^ hash(self.dataset_id) ^ hash(self.collection_id)

    def __eq__(self, other):
        return isinstance(other, Collection) and hash(self) == hash(other)

    def __hash__(self):
        return hash(self.graphql_endpoint) ^ hash(self.dataset_id) ^ hash(self.collection_id)
