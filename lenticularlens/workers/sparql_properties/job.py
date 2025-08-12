from rdflib import Graph

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
        properties_data = sparql.get_class_properties(self._entity_type_id)

        with conn_pool.connection() as conn, conn.cursor() as cur:
            if properties_data:
                for property_data in properties_data:
                    property = str(property_data.get('property'))
                    referenced = [ref for ref in str(property_data.get('valueClasses')).split(' | ') if ref]
                    rows_count = int(property_data.get('count'))
                    is_link = len(referenced) > 0
                    is_list = bool(property_data.get('isList'))
                    is_inverse = bool(property_data.get('isInverse'))
                    is_value_type = bool(property_data.get('hasLiterals'))
                    property_id = ('inv_' if is_inverse else '') + property
                    shortened_uri = SPARQLPropertiesJob.graph.namespace_manager.qname(property)

                    cur.execute('''
                        INSERT INTO entity_type_properties (dataset_id, entity_type_id, property_id, column_name,
                                                            uri, shortened_uri, rows_count, referenced,
                                                            is_link, is_list, is_inverse, is_value_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (self._dataset_id, self._entity_type_id, property_id, column_name_hash(property_id),
                          property, shortened_uri, rows_count, referenced, is_link, is_list, is_inverse,
                          is_value_type))

                cur.execute("UPDATE entity_types SET status = 'finished' "
                            "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))
            else:
                cur.execute("UPDATE entity_types SET status = 'failed' "
                            "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def on_exception(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'failed' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def on_kill(self, reset):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'waiting' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))
