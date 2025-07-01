from abc import abstractmethod
from psycopg import rows
from psycopg.rows import dict_row
from pydantic import BaseModel
from functools import cached_property
from typing import TYPE_CHECKING, Literal, Optional, Dict, List, Sequence

from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import hash_string_min
from lenticularlens.data.dataset_info import Dataset as DatasetInfo, EntityType, Property

if TYPE_CHECKING:
    from lenticularlens.data.entity_type import EntityType


class DatasetRef(BaseModel):
    type: str
    entity_type_id: str


class Dataset(BaseModel):
    dataset_id: str
    dataset_type: Literal['timbuctoo', 'sparql', 'rdf']
    title: str
    description: Optional[str] = None
    prefix_mappings: Dict[str, str]

    @cached_property
    def entity_types(self) -> Dict[str, 'EntityType']:
        from lenticularlens.data.entity_type import EntityType

        with (conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur):
            cur.execute('SELECT * FROM entity_types WHERE dataset_id = %s', (self.dataset_id,))
            return {data['entity_type_id']: EntityType(self, data['entity_type_id'], data)
                    for data in cur.fetchall()}

    @property
    def hash(self) -> str:
        return hash_string_min(self.dataset_id)

    @abstractmethod
    def get_dataset_ref(self, entity_type_id: str) -> DatasetRef:
        pass

    @staticmethod
    def _datasets_from_database(type: Literal['timbuctoo', 'sparql', 'rdf'], join: str, params: Sequence[str],
                                dataset_id_column: str, columns: List[str]) -> Dict[str, DatasetInfo]:
        with conn_pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT entity_type_properties.* '
                        'FROM entity_type_properties '
                        'INNER JOIN entity_types ON entity_type_properties.entity_type_id = entity_types.entity_type_id '
                        'INNER JOIN datasets ON entity_types.dataset_id = datasets.dataset_id '
                        f'{join}', params)

            properties = {}
            for table in cur:
                key = (table['dataset_id'], table['entity_type_id'])
                if not key in properties:
                    properties[key] = {}

                properties[key][table['property_id']] = Property(id=table['property_id'], **table)

            cur.execute('SELECT * '
                        'FROM entity_types '
                        'INNER JOIN datasets ON entity_types.dataset_id = datasets.dataset_id '
                        f'{join}', params)

            datasets = {}
            for table in cur:
                if not table[dataset_id_column] in datasets:
                    datasets[table[dataset_id_column]] = DatasetInfo(
                        type=type,
                        title=table['title'],
                        description=table['description'],
                        **{col: table[col] for col in columns},
                    )

                properties_key = (table['dataset_id'], table['entity_type_id'])
                if properties_key in properties:
                    datasets[table[dataset_id_column]].entity_types[table['entity_type_id']] = EntityType(
                        id=table['entity_type_id'],
                        **table,
                        downloaded=True,
                        properties=properties[properties_key]
                    )

            return datasets

    def __str__(self):
        return self.dataset_id

    def __eq__(self, other):
        return isinstance(other, Dataset) and hash(self) == hash(other)

    def __hash__(self):
        return hash(self.hash)
