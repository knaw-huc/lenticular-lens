from lenticularlens.data.sparql.dataset import Dataset
from lenticularlens.data.entity_type import EntityType as BaseEntityType
from lenticularlens.util.hasher import table_name_hash


class EntityType(BaseEntityType):
    @staticmethod
    def start_download(sparql_endpoint: str, entity_type_id: str):
        datasets = Dataset.get_datasets_for_sparql(sparql_endpoint)
        dataset = datasets.get(sparql_endpoint, None)
        entity_type = dataset.entity_types.get(entity_type_id, None) if dataset is not None else None

        if dataset and entity_type:
            dataset_id = Dataset.generate_id(sparql_endpoint)
            table_name = EntityType.create_table_name(sparql_endpoint, entity_type_id)
            BaseEntityType._start_download(dataset_id, table_name, entity_type)

    @staticmethod
    def create_table_name(sparql_endpoint: str, entity_type_id: str):
        entity_type_id_split = entity_type_id.split('/')
        entity_id_slash = entity_type_id_split[len(entity_type_id_split) - 1]

        entity_id_slash_split = entity_id_slash.split('#')
        entity_id = entity_id_slash_split[len(entity_id_slash_split) - 1]

        full_name = sparql_endpoint + entity_type_id

        return table_name_hash('', sparql_endpoint, entity_id, full_name)
