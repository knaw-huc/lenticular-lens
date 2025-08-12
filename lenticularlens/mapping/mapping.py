from hashlib import md5
from json import loads, dumps
from urllib.request import urlopen
from typing import Literal, Optional

from psycopg import rows
from psycopg.errors import UniqueViolation
from pydantic import BaseModel

from lenticularlens.mapping.jsonld import create_mapping
from lenticularlens.util.config_db import conn_pool


class Mapping(BaseModel):
    mapping_id: str
    mapping_type: Literal['jsonld']
    source: str
    mapping: Optional[dict[str, str]]

    def __init__(self, mapping_id: str):
        with conn_pool.connection() as conn, conn.cursor(row_factory=rows.dict_row) as cur:
            cur.execute('SELECT * FROM mappings WHERE mapping_id = %s', (mapping_id,))
            super().__init__(**cur.fetchone())

    @property
    def map(self) -> dict[str, str]:
        if self.mapping is None:
            if self.mapping_type == 'jsonld':
                self.mapping = create_mapping(loads(self.source))

            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute("UPDATE mappings SET mapping = %s WHERE mapping_id = %s",
                            (dumps(self.mapping), self.mapping_id))

        return self.mapping

    @staticmethod
    def add(mapping_type: Literal['jsonld'], url: Optional[str] = None, file: Optional[bytes] = None) -> str:
        if file:
            mapping_id = md5(file).hexdigest()
            source = file.decode('utf-8')
        elif url:
            mapping_id = url
            with urlopen(url) as response:
                source = response.read().decode('utf-8')
        else:
            raise ValueError('Either file or url must be provided.')

        try:
            with conn_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mappings (mapping_id, mapping_type, source) VALUES (%s, %s, %s)",
                    (mapping_id, mapping_type, source),
                )

            return mapping_id
        except UniqueViolation:
            return mapping_id
