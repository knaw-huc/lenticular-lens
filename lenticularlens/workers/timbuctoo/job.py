from json import dumps
from uuid import uuid4
from psycopg import sql, rows
from unicodedata import normalize

from lenticularlens.workers.job import WorkerJob
from lenticularlens.data.timbuctoo.graphql import GraphQL
from lenticularlens.util.hasher import column_name_hash
from lenticularlens.util.config_db import conn_pool, fetch_many
from lenticularlens.util.prefix_builder import get_uri_local_name, get_namespace_prefix
from lenticularlens.workers.write_data_helper import write_data_helper


class TimbuctooJob(WorkerJob):
    def __init__(self, table_name, graphql_endpoint, timbuctoo_id, entity_type_id,
                 prefix_mappings, cursor, rows_count, rows_per_page):
        self._table_name = table_name
        self._graphql_endpoint = graphql_endpoint
        self._timbuctoo_id = timbuctoo_id
        self._entity_type_id = entity_type_id
        self._prefix_mappings = prefix_mappings
        self._cursor = cursor
        self._rows_count = rows_count
        self._rows_per_page = rows_per_page
        self._uri_prefix_mappings = {}
        self._uri_prefixes = set()
        self._columns = {}

        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * FROM entity_type_properties '
                        'INNER JOIN entity_types '
                        'ON entity_type_properties.entity_type_id = entity_types.entity_type_id '
                        'WHERE "table_name" = %s', (self._table_name,))
            self._columns = {row['column_name']: row for row in cur}

        super().__init__(self.run_process)

    @staticmethod
    def format_query(column_info):
        if column_info['property_id'] == 'uri':
            return ''

        result = ''
        if column_info['is_value_type']:
            result = '... on Value { value } '
        if column_info['is_link']:
            result += '... on Entity { uri }'  # It might be both a value and a link
        if column_info['is_list']:
            result = 'items { ' + result + ' }'

        return '{ ' + result + ' }'

    @staticmethod
    def extract_value(value):
        if not value:
            return value

        if isinstance(value, str):
            return normalize('NFC', value.strip())

        if 'items' in value and value['items']:
            return [TimbuctooJob.extract_value(item) for item in value['items']]

        if 'value' in value:
            return normalize('NFC', value['value'].strip())

        if 'uri' in value:
            return normalize('NFC', value['uri'].strip())

        return None

    def run_process(self):
        self.download()
        self.determine_prefix_mappings()

    def download(self):
        total_insert = 0

        while total_insert == 0 or self._cursor:
            columns = [self._columns[name]['property_id'] + self.format_query(self._columns[name])
                       for name in self._columns]

            query = """
                query fetch($cursor: ID) {{
                    dataSets {{
                        {dataset} {{
                            {list_id}(cursor: $cursor, count: {count}) {{
                                nextCursor
                                items {{
                                    uri
                                    {columns}
                                }}
                            }}
                        }}
                    }}
                }}
            """.format(
                dataset=self._timbuctoo_id,
                list_id=self._entity_type_id + 'List',
                count=self._rows_per_page,
                columns="\n".join(columns)
            )

            query_result = GraphQL(self._graphql_endpoint).fetch(query, {'cursor': self._cursor})
            if not query_result:
                return

            query_result = query_result['dataSets'][self._timbuctoo_id][self._entity_type_id + 'List']

            # Property names can be too long for column names in Postgres, so shorten them
            # We use hashing, because that keeps the column names unique and uniform
            results = [
                {column_name_hash(name): self.extract_value(item[name]) for name in item}
                for item in query_result['items']
            ]

            total_insert = write_data_helper(self._db_conn, self._cursor, query_result['nextCursor'],
                                             self._table_name, self._rows_count, total_insert, results)
            self._cursor = query_result['nextCursor']

    def determine_prefix_mappings(self):
        with self._db_conn.cursor(name=uuid4().hex) as cur:
            cur.execute(sql.SQL('SELECT uri FROM entity_types_data.{}').format(sql.Identifier(self._table_name)))

            for uri in fetch_many(cur):
                mapping_found = False
                for prefix, prefix_uri in self._prefix_mappings.items():
                    if uri[0].startswith(prefix_uri):
                        mapping_found = True
                        if prefix not in self._uri_prefix_mappings:
                            self._uri_prefix_mappings[prefix] = prefix_uri
                        break

                if not mapping_found:
                    uri_prefix = uri[0].replace(get_uri_local_name(uri[0]), '')
                    if uri_prefix != 'urn:' and not get_uri_local_name(uri_prefix).isnumeric():
                        self._uri_prefixes.add(uri_prefix)

    def on_finish(self):
        if self._cursor is None:
            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(sql.SQL('ANALYZE entity_types_data.{}').format(sql.Identifier(self._table_name)))

                cur.execute(
                    'UPDATE entity_types '
                    'SET uri_prefix_mappings = %s, dynamic_uri_prefix_mappings = %s, update_finish_time = now() '
                    'WHERE "table_name" = %s', (dumps(self._uri_prefix_mappings), dumps({
                        get_namespace_prefix(namespace): namespace
                        for namespace in self._uri_prefixes
                    }), self._table_name,))
