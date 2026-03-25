from logging import getLogger
from typing import Any, TypedDict

from psycopg import Cursor

from lenticularlens.workers.job import WorkerJob
from lenticularlens.data.sparql.sparql import SPARQL
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import column_name_hash
from lenticularlens.util.prefix_builder import qname

log = getLogger(__name__)


class PropertyInfo(TypedDict):
    is_inverse: bool
    count: int
    is_link: bool
    is_value_type: bool
    is_list: bool
    referenced: list[str]


class SPARQLPropertiesJob(WorkerJob):
    def __init__(self, dataset_id, entity_type_id, sparql_endpoint):
        self._dataset_id = dataset_id
        self._entity_type_id = entity_type_id
        self._sparql_endpoint = sparql_endpoint

        super().__init__(self.run_sparql_query)

    def run_sparql_query(self):
        sparql = SPARQL(self._sparql_endpoint)

        log.info(f'Try to obtain properties and their counts from {self._sparql_endpoint}')
        properties_data = sparql.get_class_properties_counts_and_types(self._entity_type_id, False)
        log.info(f'Obtained properties and their counts from {self._sparql_endpoint}!')

        log.info(f'Try to obtain inverse properties and their counts from {self._sparql_endpoint}')
        inverse_properties_data = sparql.get_class_properties_counts_and_types(self._entity_type_id, True)
        log.info(f'Obtained inverse properties and their counts from {self._sparql_endpoint}!')

        properties = dict()
        for inverse in [False, True]:
            for property_data in (inverse_properties_data if inverse else properties_data):
                property = property_data.get('property').value

                log.info(f'Try to obtain is list from {self._sparql_endpoint} for property {property} inverse {inverse}')
                is_list = sparql.get_class_property_is_list(self._entity_type_id, property, inverse)[0]
                log.info(f'Obtained is list from {self._sparql_endpoint} for property {property} inverse {inverse}!')

                value_classes = []
                if property_data.get('hasIRIs').value == 'true' or property_data.get('hasBlankNodes').value == 'true':
                    log.info(f'Try to obtain value classes from {self._sparql_endpoint} for property {property} inverse {inverse}')
                    value_classes = sparql.get_class_property_value_classes(self._entity_type_id, property, inverse)
                    log.info(f'Obtained value classes from {self._sparql_endpoint} for property {property} inverse {inverse}!')

                properties[property] = PropertyInfo(
                    is_inverse=inverse,
                    count=int(property_data.get('count').value),
                    is_link=property_data.get('hasIRIs').value == 'true' or property_data.get('hasBlankNodes').value == 'true',
                    is_value_type=property_data.get('hasLiterals').value == 'true',
                    is_list=is_list.get('isList').value == 'true',
                    referenced=[value_class.get('valueClass').value for value_class in value_classes]
                )

        with conn_pool.connection() as conn, conn.cursor() as cur:
            for [property, property_data] in properties.items():
                self.insert_properties_data(property, property_data, cur)

            cur.execute("UPDATE entity_types SET status = 'finished' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def insert_properties_data(self, property: str, property_data: PropertyInfo, cur: Cursor[Any]):
        property_id = ('inv_' if property_data['is_inverse'] else '') + property
        shortened_uri, _prefix, _name = qname(property)

        cur.execute('''
                    INSERT INTO entity_type_properties (dataset_id, entity_type_id, property_id, column_name,
                                                        uri, shortened_uri, rows_count, referenced,
                                                        is_link, is_list, is_inverse, is_value_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (self._dataset_id, self._entity_type_id, property_id, column_name_hash(property_id),
                          property, shortened_uri, property_data['count'], property_data['referenced'],
                          property_data['is_link'], property_data['is_list'],
                          property_data['is_inverse'], property_data['is_value_type']))

    def on_exception(self):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'failed' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))

    def on_kill(self, reset):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("UPDATE entity_types SET status = 'waiting' "
                        "WHERE dataset_id = %s AND entity_type_id = %s", (self._dataset_id, self._entity_type_id))
