from lenticularlens.data.timbuctoo.dataset import Dataset
from lenticularlens.data.timbuctoo.graphql import GraphQL
from lenticularlens.data.entity_type import EntityType as BaseEntityType
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import table_name_hash


class EntityType(BaseEntityType):
    @staticmethod
    def start_download(graphql_endpoint: str, timbuctoo_id: str, entity_type_id: str):
        datasets = Dataset.get_datasets_for_graphql(graphql_endpoint)

        dataset = datasets.get(timbuctoo_id, None)
        entity_type = dataset.entity_types.get(entity_type_id, None) if dataset is not None else None

        if dataset and entity_type:
            dataset_id = Dataset.generate_id(graphql_endpoint, timbuctoo_id)
            table_name = EntityType.create_table_name(graphql_endpoint, timbuctoo_id, entity_type_id)

            BaseEntityType._insert_into_database(dataset_id, table_name, dataset, entity_type)
            BaseEntityType._start_download(dataset_id, table_name, entity_type)

            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO timbuctoo (dataset_id, graphql_endpoint, timbuctoo_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (dataset_id) DO NOTHING
                ''', (dataset_id, graphql_endpoint, timbuctoo_id))

    @staticmethod
    def create_table_name(graphql_endpoint: str, timbuctoo_id: str, entity_type_id: str):
        user, dataset_name = timbuctoo_id.split('__', 1)
        prefix = GraphQL.known_endpoints[graphql_endpoint] + '_' if graphql_endpoint in GraphQL.known_endpoints else ''

        collection_id_split = entity_type_id.split('__')
        collection_id = collection_id_split[len(collection_id_split) - 1]

        full_name = graphql_endpoint + timbuctoo_id + collection_id

        return table_name_hash(prefix, dataset_name, collection_id, full_name)
