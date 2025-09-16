from typing import Any

from psycopg import Cursor
from rdflib import Graph
from rdflib.query import ResultRow

from lenticularlens.workers.job import WorkerJob
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import column_name_hash


class SPARQLPropertiesJob(WorkerJob):
    graph = Graph()

    def __init__(self, dataset_id, entity_type_id, sparql_endpoint):
        self._dataset_id = dataset_id
        self._entity_type_id = entity_type_id
        self._sparql_endpoint = sparql_endpoint

        super().__init__(self.run_sparql_query)

    def run_sparql_query(self):
        sparql = SPARQL(self._sparql_endpoint)
        properties_data = sparql.get_class_properties(self._entity_type_id, False)
        inverse_properties_data = sparql.get_class_properties(self._entity_type_id, True)

        with conn_pool.connection() as conn, conn.cursor() as cur:
            if properties_data or inverse_properties_data:
                for property_data in properties_data:
                    self.insert_properties_data(property_data, False, cur)

                for property_data in inverse_properties_data:
                    self.insert_properties_data(property_data, True, cur)

                cur.execute("UPDATE entity_types SET status = 'finished' "
                            "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))
            else:
                cur.execute("UPDATE entity_types SET status = 'failed' "
                            "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def insert_properties_data(self, property_data: ResultRow, is_inverse: bool, cur: Cursor[Any]):
        property = str(property_data.get('property'))
        referenced = [ref for ref in str(property_data.get('valueClasses')).split(' | ') if ref]
        rows_count = int(property_data.get('count'))
        is_link = len(referenced) > 0
        is_list = bool(property_data.get('isList'))
        is_value_type = bool(property_data.get('hasLiterals'))
        property_id = ('inv_' if is_inverse else '') + property

        try:
            ns_manager = SPARQLPropertiesJob.graph.namespace_manager
            prefix, namespace, name = ns_manager.compute_qname(property, generate=False)
            shortened_uri = ':'.join((prefix, name))
        except KeyError:
            shortened_uri = property

        cur.execute('''
            INSERT INTO entity_type_properties (dataset_id, entity_type_id, property_id, column_name,
                                                uri, shortened_uri, rows_count, referenced,
                                                is_link, is_list, is_inverse, is_value_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (self._dataset_id, self._entity_type_id, property_id, column_name_hash(property_id),
              property, shortened_uri, rows_count, referenced, is_link, is_list, is_inverse, is_value_type))

    def on_exception(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'failed' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def on_kill(self, reset):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'waiting' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))
