from json import dumps
from psycopg import sql

from lenticularlens.data.timbuctoo.dataset import Dataset
from lenticularlens.data.timbuctoo.graphql import GraphQL
from lenticularlens.data.entity_type import EntityType as BaseEntityType
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import table_name_hash, column_name_hash


class EntityType(BaseEntityType):
    @staticmethod
    def start_download(graphql_endpoint: str, timbuctoo_id: str, entity_type_id: str):
        datasets = Dataset.get_datasets_for_graphql(graphql_endpoint)

        dataset = datasets.get(timbuctoo_id, None)
        entity_type = dataset.entity_types.get(entity_type_id, None) if dataset is not None else None

        if dataset and entity_type:
            dataset_id = Dataset.generate_id(graphql_endpoint, timbuctoo_id)
            table_name = EntityType.create_table_name(graphql_endpoint, timbuctoo_id, entity_type_id)

            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(sql.SQL('DROP TABLE IF EXISTS entity_types_data.{name}; '
                                    'CREATE TABLE entity_types_data.{name} ({columns_sql})').format(
                    name=sql.Identifier(table_name),
                    columns_sql=entity_type.columns_sql,
                ))

                cur.execute('''
                            INSERT INTO datasets (dataset_id, dataset_type, title, description, prefix_mappings)
                            VALUES (%s, 'timbuctoo', %s, %s, %s)
                            ON CONFLICT (dataset_id) DO NOTHING
                            ''', (dataset_id, dataset.title, dataset.description, dumps(dataset.prefix_mappings)))

                cur.execute('''
                            INSERT INTO timbuctoo (dataset_id, graphql_endpoint, timbuctoo_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (dataset_id) DO NOTHING
                            ''', (dataset_id, graphql_endpoint, timbuctoo_id))

                cur.execute('''
                            INSERT INTO entity_types (dataset_id, entity_type_id, "table_name",
                                                      label, uri, shortened_uri, total, create_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                            ''', (dataset_id, entity_type_id, table_name,
                                  entity_type.label, entity_type.uri, entity_type.shortened_uri, entity_type.total))

                for name, property in entity_type.properties.items():
                    cur.execute('''
                                INSERT INTO entity_type_properties (dataset_id, entity_type_id, property_id,
                                                                    column_name,
                                                                    uri, shortened_uri, rows_count, referenced,
                                                                    is_link, is_list, is_inverse, is_value_type)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ''', (dataset_id, entity_type_id, name, column_name_hash(name),
                                      property.uri, property.shortened_uri, property.rows_count, property.referenced,
                                      property.is_link, property.is_list, property.is_inverse, property.is_value_type))

    @staticmethod
    def create_table_name(graphql_endpoint: str, timbuctoo_id: str, entity_type_id: str):
        user, dataset_name = timbuctoo_id.split('__', 1)
        prefix = GraphQL.known_endpoints[graphql_endpoint] + '_' if graphql_endpoint in GraphQL.known_endpoints else ''

        collection_id_split = entity_type_id.split('__')
        collection_id = collection_id_split[len(collection_id_split) - 1]

        full_name = graphql_endpoint + timbuctoo_id + collection_id

        return table_name_hash(prefix, dataset_name, collection_id, full_name)
