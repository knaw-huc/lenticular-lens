from psycopg import rows
from pydantic import BaseModel
from typing import Dict, List, Optional

from lenticularlens.data.dataset import Dataset as BaseDataset, DatasetRef as BaseDatasetRef
from lenticularlens.data.dataset_info import Dataset as DatasetInfo
from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import hash_string


class DatasetRef(BaseDatasetRef):
    sparql_endpoint: str
    graph: Optional[str]


class Download(BaseModel):
    sparql_endpoint: str
    graph: Optional[str]
    entity_type_id: str
    total: int
    rows_count: int


class Dataset(BaseDataset):
    sparql_endpoint: str
    graph: Optional[str]
    authorization: Optional[str]

    def __init__(self, sparql_endpoint: str, graph: Optional[str]):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            if graph is not None:
                cur.execute('SELECT * '
                            'FROM datasets '
                            'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id '
                            'WHERE sparql_endpoint = %s AND graph = %s', (sparql_endpoint, graph))
            else:
                cur.execute('SELECT * '
                            'FROM datasets '
                            'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id '
                            'WHERE sparql_endpoint = %s AND graph IS NULL', (sparql_endpoint,))
            super().__init__(**cur.fetchone())

    def get_dataset_ref(self, entity_type_id: str) -> DatasetRef:
        return DatasetRef(
            type='sparql',
            sparql_endpoint=self.sparql_endpoint,
            graph=self.graph,
            entity_type_id=entity_type_id
        )

    @staticmethod
    def generate_id(sparql_endpoint: str, graph: Optional[str]) -> str:
        return hash_string(f"sparql__{sparql_endpoint}" if graph is None else f"sparql__{sparql_endpoint}__{graph}")

    @staticmethod
    def get_datasets_for_sparql(sparql_endpoint: str, graph: Optional[str]) -> Dict[str, DatasetInfo]:
        return Dataset._from_database(sparql_endpoint, graph)

    @staticmethod
    def load_datasets_for_sparql(sparql_endpoint: str, graph: Optional[str] = None,
                                 authorization: Optional[str] = None):
        with conn_pool.connection() as conn, conn.cursor() as cur:
            dataset_id = Dataset.generate_id(sparql_endpoint, graph)

            cur.execute('''
                INSERT INTO datasets (dataset_id, dataset_type, title) VALUES (%s, 'sparql', %s)
                ON CONFLICT (dataset_id) DO NOTHING
            ''', (dataset_id, sparql_endpoint))

            cur.execute('''
                INSERT INTO sparql (dataset_id, sparql_endpoint, graph, authorization, status) 
                VALUES (%s, %s, %s, %s, 'waiting')
                ON CONFLICT (dataset_id) DO UPDATE SET status = 'waiting'
            ''', (dataset_id, sparql_endpoint, graph, authorization))

    @staticmethod
    def get_downloads() -> List[Download]:
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute("SELECT sparql_endpoint, graph, entity_type_id, total, rows_count "
                        "FROM entity_types "
                        "INNER JOIN datasets ON entity_types.dataset_id = datasets.dataset_id "
                        "INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id "
                        "WHERE entity_types.status = 'downloadable'")

            return [Download(**download_record) for download_record in cur]

    @staticmethod
    def _from_database(sparql_endpoint: str, graph: Optional[str]) -> Dict[str, DatasetInfo]:
        return BaseDataset._datasets_from_database(
            'sparql',
            'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id WHERE sparql_endpoint = %s AND graph = %s' \
                if graph is not None else \
                'INNER JOIN sparql ON datasets.dataset_id = sparql.dataset_id WHERE sparql_endpoint = %s AND graph IS NULL',
            (sparql_endpoint, graph) if graph is not None else (sparql_endpoint,),
            'sparql_endpoint',
            ['sparql_endpoint', 'status']
        )
