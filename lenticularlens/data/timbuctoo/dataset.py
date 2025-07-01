from psycopg import rows
from pydantic import BaseModel
from typing import Dict, List
from urllib.parse import urlparse

from lenticularlens.data.timbuctoo.graphql import GraphQL
from lenticularlens.data.dataset import Dataset as BaseDataset, DatasetRef as BaseDatasetRef
from lenticularlens.data.dataset_info import Dataset as DatasetInfo
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import hash_string


class DatasetRef(BaseDatasetRef):
    graphql_endpoint: str
    timbuctoo_id: str


class Download(BaseModel):
    graphql_endpoint: str
    timbuctoo_id: str
    entity_type_id: str
    total: int
    rows_count: int


class Dataset(BaseDataset):
    graphql_endpoint: str
    timbuctoo_id: str

    def __init__(self, graphql_endpoint: str, timbuctoo_id: str):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * '
                        'FROM datasets '
                        'INNER JOIN timbuctoo ON datasets.dataset_id = timbuctoo.dataset_id '
                        'WHERE graphql_endpoint = %s '
                        'AND timbuctoo_id = %s', (graphql_endpoint, timbuctoo_id))
            super().__init__(**cur.fetchone())

    def get_dataset_ref(self, entity_type_id: str) -> DatasetRef:
        return DatasetRef(
            type='timbuctoo',
            graphql_endpoint=self.graphql_endpoint,
            timbuctoo_id=self.timbuctoo_id,
            entity_type_id=entity_type_id
        )

    @staticmethod
    def generate_id(graphql_endpoint: str, timbuctoo_id: str) -> str:
        endpoint = GraphQL.known_endpoints.get(graphql_endpoint, urlparse(graphql_endpoint).netloc)
        return hash_string(f"timbuctoo__{endpoint}__{timbuctoo_id}")

    @staticmethod
    def get_datasets_for_graphql(graphql_endpoint: str) -> Dict[str, DatasetInfo]:
        graphql = GraphQL(graphql_endpoint)
        datasets = graphql.datasets

        datasets_database = Dataset._from_database(graphql_endpoint)
        for dataset, dataset_data in datasets_database.items():
            if dataset not in datasets:
                datasets[dataset] = dataset_data.model_copy()
            else:
                for collection, collection_data in dataset_data.entity_types.items():
                    datasets[dataset].entity_types[collection] = collection_data.model_copy()

        return datasets

    @staticmethod
    def get_downloads() -> List[Download]:
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute("SELECT graphql_endpoint, timbuctoo_id, entity_type_id, total, rows_count "
                        "FROM entity_types "
                        "INNER JOIN datasets ON entity_types.dataset_id = datasets.dataset_id "
                        "INNER JOIN timbuctoo ON datasets.dataset_id = timbuctoo.dataset_id "
                        "WHERE entity_types.status = 'downloadable'")

            return [Download(**download_record) for download_record in cur]

    @staticmethod
    def _from_database(graphql_endpoint: str) -> Dict[str, DatasetInfo]:
        return BaseDataset._datasets_from_database(
            'timbuctoo',
            'INNER JOIN timbuctoo ON datasets.dataset_id = timbuctoo.dataset_id WHERE graphql_endpoint = %s',
            (graphql_endpoint,),
            'timbuctoo_id',
            ['graphql_endpoint', 'timbuctoo_id', 'prefix_mappings']
        )
