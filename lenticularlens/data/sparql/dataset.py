from psycopg import rows
from pydantic import BaseModel
from typing import Dict, List

from lenticularlens.data.dataset import Dataset as BaseDataset, DatasetRef as BaseDatasetRef
from lenticularlens.data.dataset_info import Dataset as DatasetInfo
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import hash_string


class DatasetRef(BaseDatasetRef):
    sparql_endpoint: str


class Download(BaseModel):
    sparql_endpoint: str
    entity_type_id: str
    total: int
    rows_count: int


class Dataset(BaseDataset):
    sparql_endpoint: str

    def __init__(self, sparql_endpoint: str):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * '
                        'FROM datasets '
                        'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id '
                        'WHERE sparql_endpoint = %s', (sparql_endpoint,))
            super().__init__(**cur.fetchone())

    def get_dataset_ref(self, entity_type_id: str) -> DatasetRef:
        return DatasetRef(
            type='sparql',
            sparql_endpoint=self.sparql_endpoint,
            entity_type_id=entity_type_id
        )

    @staticmethod
    def generate_id(sparql_endpoint: str) -> str:
        return hash_string(f"sparql__{sparql_endpoint}")

    @staticmethod
    def get_datasets_for_sparql(sparql_endpoint: str) -> Dict[str, DatasetInfo]:
        return Dataset._from_database(sparql_endpoint)

    @staticmethod
    def load_datasets_for_sparql(sparql_endpoint: str):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            dataset_id = Dataset.generate_id(sparql_endpoint)

            cur.execute('''
                INSERT INTO datasets (dataset_id, dataset_type, title) VALUES (%s, 'sparql', %s)
                ON CONFLICT (dataset_id) DO NOTHING
            ''', (dataset_id, sparql_endpoint))

            cur.execute('''
                INSERT INTO sparql (dataset_id, sparql_endpoint, status) VALUES (%s, %s, 'waiting')
                ON CONFLICT (dataset_id) DO UPDATE SET status = 'waiting'
            ''', (dataset_id, sparql_endpoint))

    @staticmethod
    def get_downloads() -> List[Download]:
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute("SELECT sparql_endpoint, entity_type_id, total, rows_count "
                        "FROM entity_types "
                        "INNER JOIN datasets ON entity_types.dataset_id = datasets.dataset_id "
                        "INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id "
                        "WHERE entity_types.status = 'downloadable'")

            return [Download(**download_record) for download_record in cur]

    @staticmethod
    def _from_database(sparql_endpoint: str) -> Dict[str, DatasetInfo]:
        return BaseDataset._datasets_from_database(
            'sparql',
            'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id WHERE sparql_endpoint = %s',
            (sparql_endpoint,),
            'sparql_endpoint',
            ['sparql_endpoint', 'status']
        )
