from psycopg import sql
from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional, Dict, List

from lenticularlens.util.hasher import column_name_hash


class Property(BaseModel):
    id: str
    uri: str
    shortened_uri: str
    rows_count: int
    referenced: List[str]
    is_link: bool
    is_list: bool
    is_inverse: bool
    is_value_type: bool


class EntityType(BaseModel):
    id: str
    label: Optional[str] = None
    uri: str
    shortened_uri: str
    total: int
    status: str
    properties: Dict[str, Property] = {}

    @property
    def columns_sql(self):
        def column_sql(column_name: str, column_type: str):
            return sql.SQL('{col_name} {col_type}').format(
                col_name=sql.Identifier(column_name),
                col_type=sql.SQL(column_type),
            )

        columns_sqls = [column_sql('uri', 'text primary key')]
        for name, info in self.properties.items():
            if name != 'uri':
                column_name = column_name_hash(name)
                column_type = 'text[]' if info.is_list else 'text'
                columns_sqls.append(column_sql(column_name, column_type))

        return sql.SQL(',\n').join(columns_sqls)


class Dataset(BaseModel):
    id: str
    type: Literal['timbuctoo', 'sparql', 'rdf']
    name: Optional[str] = None
    title: str
    description: Optional[str] = None
    entity_types: Dict[str, EntityType] = {}
    model_config = ConfigDict(extra='allow')
