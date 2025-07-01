from random import choices
from itertools import groupby
from string import ascii_lowercase
from unicodedata import normalize

from psycopg import sql, rows

from lenticularlens.workers.job import WorkerJob
from lenticularlens.workers.write_data_helper import write_data_helper
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.util.config_db import conn_pool


class SPARQLJob(WorkerJob):
    def __init__(self, table_name, sparql_endpoint, entity_type_id, cursor, rows_count, rows_per_page):
        self._table_name = table_name
        self._sparql_endpoint = sparql_endpoint
        self._entity_type_id = entity_type_id
        self._cursor = int(cursor) if cursor is not None else 0
        self._rows_count = rows_count
        self._rows_per_page = rows_per_page
        self._endpoint = SPARQL(sparql_endpoint)
        self._columns = {}

        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT entity_type_properties.* '
                        'FROM entity_type_properties '
                        'INNER JOIN entity_types '
                        'ON entity_type_properties.entity_type_id = entity_types.entity_type_id '
                        'WHERE "table_name" = %s', (self._table_name,))
            self._columns = {''.join(choices(ascii_lowercase, k=15)): row for row in cur}

        super().__init__(self.run_process)

    @staticmethod
    def format_sparql_query(id, uri, is_inverse):
        return f'OPTIONAL {{ ?{id} <{uri}> ?uri . }} ' if is_inverse else \
            f'OPTIONAL {{ ?uri <{uri}> ?{id} . }} '

    @staticmethod
    def format_value(results, id, is_list):
        values = [normalize('NFC', str(result.get(id)).strip())
                  for result in results
                  if result.get(id) is not None]

        return None if len(values) == 0 else list(set(values)) if is_list else values[0]

    def run_process(self):
        total_insert = 0

        while total_insert == 0 or self._cursor:
            single_value_columns = [(id, cols)
                                    for (id, cols) in self._columns.items()
                                    if not cols['is_list']]

            query = f"""
                SELECT ?uri {" ".join('?' + id for (id, cols) in single_value_columns)}
                WHERE {{
                    ?uri a <{self._entity_type_id}> .
                    {'\n'.join(self.format_sparql_query(id, cols['uri'], cols['is_inverse'])
                               for (id, cols) in single_value_columns)}
                }}
                LIMIT {self._rows_per_page} OFFSET {self._cursor}       
            """

            query_result = self._endpoint.fetch(query)
            if not query_result:
                self._cursor = None
                return

            next_cursor = self._cursor + len(query_result)
            results = {
                str(results.get('uri')): {
                    'uri': str(results.get('uri')),
                    **{cols['column_name']: self.format_value([results], id, cols['is_list'])
                       for (id, cols) in single_value_columns}}
                for results in query_result
            }

            for (id, cols) in self._columns.items():
                if cols['is_list']:
                    query = f"""
                        SELECT ?uri ?{id}
                        WHERE {{
                            VALUES ?uri {{{' '.join('<' + uri + '>' for uri in results.keys())}}}
                            {self.format_sparql_query(id, cols['uri'], cols['is_inverse'])}
                        }}
                    """

                    query_result = self._endpoint.fetch(query)
                    for uri, query_results in groupby(query_result, lambda x: str(x.get('uri'))):
                        results[uri][cols['column_name']] = self.format_value(query_results, id, cols['is_list'])

            total_insert = write_data_helper(self._db_conn, self._cursor, next_cursor,
                                             self._table_name, self._rows_count, total_insert, list(results.values()))
            self._cursor = next_cursor

    def on_finish(self):
        if self._cursor is None:
            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(sql.SQL('ANALYZE entity_types_data.{}').format(sql.Identifier(self._table_name)))
                cur.execute('UPDATE entity_types SET cursor = NULL, update_finish_time = now() WHERE "table_name" = %s',
                            (self._table_name,))
