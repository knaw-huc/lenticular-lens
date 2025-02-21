from abc import abstractmethod
from psycopg import rows
from pydantic import BaseModel
from functools import cached_property
from typing import TYPE_CHECKING, Literal, Optional, Dict

from lenticularlens.util.config_db import conn_pool
from lenticularlens.util.hasher import hash_string_min

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

    def __str__(self):
        return self.dataset_id

    def __eq__(self, other):
        return isinstance(other, Dataset) and hash(self) == hash(other)

    def __hash__(self):
        return hash(self.hash)
