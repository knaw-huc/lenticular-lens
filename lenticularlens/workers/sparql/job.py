from typing import Iterable
from random import choices
from itertools import groupby
from string import ascii_lowercase
from unicodedata import normalize

from psycopg import sql, rows
from SPARQLWrapper.SmartWrapper import Value

from lenticularlens.workers.job import WorkerJob
from lenticularlens.workers.write_data_helper import write_data_helper
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.util.config_db import conn_pool


class SPARQLJob(WorkerJob):
    def __init__(self, table_name, sparql_endpoint, entity_type_id, cursor, rows_count, rows_per_page):
        self._table_name = table_name
        self._sparql_endpoint = sparql_endpoint
        self._entity_type_id = entity_type_id
        self._cursor = cursor
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
        return f'OPTIONAL {{ ?{id} <{uri}> ?uri . }} ' if is_inverse else f'OPTIONAL {{ ?uri <{uri}> ?{id} . }} '

    @staticmethod
    def format_value(results: Iterable[dict[str, Value]], id: str, is_list: bool) -> str | list[str] | None:
        values = [normalize('NFC', result.get(id).value.strip())
                  for result in results
                  if result.get(id) is not None]

        return None if len(values) == 0 else list(set(values)) if is_list else values[0]

    @staticmethod
    def format_sparql_uri(uri: Value) -> str:
        return f'<{uri.value}>' if uri.type == 'uri' else f'_:{uri.value}'

    def run_process(self):
        total_insert = 0
        use_filter_paging = self._cursor is None or not self._cursor.isnumeric()

        match_type_clause = f"?uri a <{self._entity_type_id}> ." \
            if self._entity_type_id != 'http://www.w3.org/2000/01/rdf-schema#Resource' else \
            f"MINUS {{ ?uri a ?type . }}"

        single_value_columns = [(id, cols)
                                for (id, cols) in self._columns.items()
                                if not cols['is_list']]
        list_value_columns   = [(id, cols)
                                for (id, cols) in self._columns.items()
                                if cols['is_list']]

        while total_insert == 0 or self._cursor:
            cursor = str(self._rows_per_page) \
                if not use_filter_paging and self._cursor is not None and not self._cursor.isnumeric() \
                else self._cursor

            query = f"""
                SELECT ?uri {" ".join('?' + id for (id, cols) in single_value_columns)}
                WHERE {{
                    {match_type_clause}
                    {'\n'.join(self.format_sparql_query(id, cols['uri'], cols['is_inverse'])
                               for (id, cols) in single_value_columns)}
                    {f'FILTER (?uri > {cursor})' if cursor is not None and use_filter_paging else ''}
                }}
                ORDER BY ?uri 
                LIMIT {self._rows_per_page} {f'OFFSET {cursor}' if not use_filter_paging else ''}
            """

            query_result = self._endpoint.fetch(query)
            if not query_result:
                total_written = self._rows_count + total_insert
                if use_filter_paging and total_written == self._rows_per_page:
                    use_filter_paging = False
                    continue

                self._cursor = None
                return

            next_cursor = self.format_sparql_uri(query_result[-1].get('uri')) \
                if use_filter_paging else str(int(cursor) + len(query_result))

            results = {
                results.get('uri').value: {
                    'uri': results.get('uri').value,
                    **{cols['column_name']: self.format_value([results], id, cols['is_list'])
                       for (id, cols) in single_value_columns}}
                for results in query_result
            }

            for (id, cols) in list_value_columns:
                values = ' '.join(self.format_sparql_uri(results.get('uri')) for results in query_result)

                query = f"""
                    SELECT ?uri ?{id}
                    WHERE {{
                        VALUES ?uri {{{ values }}}
                        {self.format_sparql_query(id, cols['uri'], cols['is_inverse'])}
                    }}
                """

                list_query_result = self._endpoint.fetch(query)
                for uri, query_results in groupby(list_query_result, lambda x: x.get('uri').value):
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
