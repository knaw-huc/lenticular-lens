from json import dumps
from uuid import uuid4
from psycopg import sql
from unicodedata import normalize

from ll.util.hasher import column_name_hash
from ll.util.config_db import conn_pool, fetch_many
from ll.util.prefix_builder import get_uri_local_name, get_namespace_prefix

from ll.worker.job import WorkerJob
from ll.data.timbuctoo import Timbuctoo


class TimbuctooJob(WorkerJob):
    def __init__(self, table_name, graphql_endpoint, dataset_id, collection_id,
                 prefix_mappings, columns, cursor, rows_count, rows_per_page):
        self._table_name = table_name
        self._graphql_endpoint = graphql_endpoint
        self._dataset_id = dataset_id
        self._collection_id = collection_id
        self._prefix_mappings = prefix_mappings
        self._columns = columns
        self._cursor = cursor
        self._rows_count = rows_count
        self._rows_per_page = rows_per_page
        self._uri_prefix_mappings = {}
        self._uri_prefixes = set()

        super().__init__(self.run_process)

    @staticmethod
    def format_query(column_info):
        if column_info['name'] == 'uri':
            return ''

        result = ''
        if column_info['isValueType']:
            result = '... on Value { value } '
        if column_info['isLink']:
            result += '... on Entity { uri }'  # It might be both a value and a link
        if column_info['isList']:
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
            columns = [self._columns[name]['name'] + self.format_query(self._columns[name]) for name in self._columns]

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
                dataset=self._dataset_id,
                list_id=self._collection_id + 'List',
                count=self._rows_per_page,
                columns="\n".join(columns)
            )

            query_result = Timbuctoo(self._graphql_endpoint).fetch_graph_ql(query, {'cursor': self._cursor})
            if not query_result:
                return

            query_result = query_result['dataSets'][self._dataset_id][self._collection_id + 'List']

            # Property names can be too long for column names in Postgres, so make them shorter
            # We use hashing, because that keeps the column names unique and uniform
            results = [
                {column_name_hash(name): self.extract_value(item[name]) for name in item}
                for item in query_result['items']
            ]

            with self._db_conn.cursor() as cur:
                cur.execute('SET search_path TO "$user", timbuctoo, public; '
                            'LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;')

                # Check if the data we have is still the data that is expected to be inserted
                if self._cursor:
                    cur.execute('''
                        SELECT 1
                        FROM timbuctoo_tables
                        WHERE "table_name" = %s AND next_page = %s
                    ''', (self._table_name, self._cursor))
                else:
                    cur.execute('''
                        SELECT 1
                        FROM timbuctoo_tables
                        WHERE "table_name" = %s AND next_page IS NULL
                        AND (update_finish_time IS NULL OR update_finish_time < update_start_time)
                    ''', (self._table_name,))

                if cur.fetchone() != (1,):
                    raise Exception('This is weird... '
                                    'Someone else updated the job for table %s '
                                    'while I was fetching data.' % self._table_name)

                cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(self._table_name)))
                table_rows = cur.fetchone()[0]

                if table_rows != self._rows_count + total_insert:
                    raise Exception('Table %s has %i rows, expected %i. Quitting job.'
                                    % (self._table_name, table_rows, self._rows_count + total_insert))

                if len(results) > 0:
                    with cur.copy(sql.SQL('COPY {} ({}) FROM STDIN').format(
                            sql.Identifier(self._table_name),
                            sql.SQL(', ').join([sql.Identifier(column) for column in results[0].keys()])
                    )) as copy:
                        for result in results:
                            copy.write_row(list(result.values()))

                    total_insert += len(results)
                    cur.execute('''
                        UPDATE timbuctoo_tables
                        SET last_push_time = now(), next_page = %s, rows_count = %s
                        WHERE "table_name" = %s
                    ''', (query_result['nextCursor'], table_rows + len(results), self._table_name))

                self._db_conn.commit()

            self._cursor = query_result['nextCursor']

    def determine_prefix_mappings(self):
        with self._db_conn.cursor(name=uuid4().hex) as cur:
            cur.execute(sql.SQL('SELECT uri FROM timbuctoo.{}').format(sql.Identifier(self._table_name)))

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
                cur.execute(sql.SQL('ANALYZE timbuctoo.{}').format(sql.Identifier(self._table_name)))

                cur.execute(
                    'UPDATE timbuctoo_tables '
                    'SET uri_prefix_mappings = %s, dynamic_uri_prefix_mappings = %s, update_finish_time = now() '
                    'WHERE "table_name" = %s', (dumps(self._uri_prefix_mappings), dumps({
                        get_namespace_prefix(namespace): namespace
                        for namespace in self._uri_prefixes
                    }), self._table_name,))

    def watch_process(self):
        pass

    def watch_kill(self):
        pass

    def on_kill(self, reset):
        pass

    def on_exception(self):
        pass
