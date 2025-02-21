from psycopg import rows
from pydantic import BaseModel
from typing import List, Optional

from lenticularlens.data.dataset import Dataset
from lenticularlens.data.entity_type import EntityType
from lenticularlens.util.config_db import conn_pool


class Property(BaseModel):
    entity_type: EntityType
    property_id: str
    column_name: str
    uri: str
    shortened_uri: str
    rows_count: int
    referenced: List[str]
    is_link: bool
    is_list: bool
    is_inverse: bool
    is_value_type: bool

    def __init__(self, entity_type: EntityType, property_id: str, data: Optional[dict] = None):
        if data is not None:
            super().__init__(entity_type=entity_type, **data)
        else:
            with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
                cur.execute('SELECT * FROM entity_type_properties '
                            'WHERE dataset_id = %s AND entity_type_id = %s AND property_id = %s',
                            (self.entity_type.dataset.dataset_id, self.entity_type.entity_type_id, property_id))
                super().__init__(entity_type=entity_type, **cur.fetchone())
