from psycopg import rows
from datetime import datetime
from pydantic import BaseModel
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Dict

from lenticularlens.data.dataset import Dataset
from lenticularlens.util.hasher import hash_string_min
from lenticularlens.util.config_db import conn_pool

if TYPE_CHECKING:
    from lenticularlens.data.property import Property


class EntityType(BaseModel):
    dataset: Dataset
    entity_type_id: str
    table_name: str
    label: Optional[str]
    uri: str
    shortened_uri: str
    total: int
    rows_count: int
    cursor: Optional[str]
    create_time: datetime
    update_start_time: Optional[datetime]
    last_push_time: Optional[datetime]
    update_finish_time: Optional[datetime]
    uri_prefix_mappings: Dict[str, str]
    dynamic_uri_prefix_mappings: Dict[str, str]

    def __init__(self, dataset: Dataset, entity_type_id: str, data: Optional[dict] = None):
        if data is not None:
            super().__init__(dataset=dataset, **data)
        else:
            with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
                cur.execute('SELECT * FROM entity_types WHERE dataset_id = %s AND entity_type_id = %s',
                            (dataset.dataset_id, entity_type_id))
                super().__init__(dataset=dataset, entity_type_id=entity_type_id, **cur.fetchone())

    @property
    def alias(self) -> str:
        return hash_string_min(self.table_name)

    @cached_property
    def properties(self) -> Dict[str, 'Property']:
        from lenticularlens.data.property import Property

        with (conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur):
            cur.execute('SELECT * FROM entity_type_properties WHERE dataset_id = %s AND entity_type_id = %s',
                        (self.dataset.dataset_id, self.entity_type_id))
            return {data['property_id']: Property(self, data['property_id'], data)
                    for data in cur.fetchall()}

    @property
    def prefix_info(self) -> (str | None, str | None):
        prefix = self.shortened_uri[:self.shortened_uri.index(':')] \
            if self.uri != self.shortened_uri and ':' in self.shortened_uri else None
        prefix_uri = self.dataset.prefix_mappings[prefix] \
            if prefix and prefix in self.dataset.prefix_mappings else None

        return prefix, prefix_uri

    @property
    def is_downloaded(self) -> bool:
        return self.update_finish_time is not None and self.update_finish_time >= self.update_start_time

    @property
    def rows_downloaded(self) -> int:
        return self.rows_count \
            if self.update_finish_time is None or self.update_finish_time < self.update_start_time \
            else -1

    def get_entity_type(self, entity_type_id: str) -> Optional['EntityType']:
        return self.dataset.entity_types.get(entity_type_id)

    @property
    def hash(self):
        return hash_string_min((self.dataset.dataset_id, self.entity_type_id))

    def __str__(self):
        return str(self.dataset.dataset_id) + ' - ' + self.entity_type_id

    def __eq__(self, other):
        return isinstance(other, EntityType) and hash(self) == hash(other)

    def __hash__(self):
        return hash(self.hash)
