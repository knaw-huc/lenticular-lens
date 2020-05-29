from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import hash_string, get_string_from_sql


class PropertyField:
    def __init__(self, data, job=None, parent_label=None, columns=None, transformers=None):
        self._data = data if isinstance(data, list) else [data]
        self._data[len(self._data) - 1] = self._data[len(self._data) - 1].lower()

        self._parent_label = parent_label
        self._transformers = transformers if transformers else []

        ets = job.get_entity_type_selection_by_internal_id(self.entity_type_selection_internal_id) if job else None
        self._columns = ets.columns if ets else columns

        self._extend = True
        self._hash = None

    def no_extend(self):
        self._extend = False

    @property
    def hash(self):
        if not self._hash:
            self._hash = hash_string(get_string_from_sql(self.sql))
        return self._hash

    @property
    def absolute_property(self):
        if self._parent_label and len(self._data) == 1:
            property_array = [self._parent_label, self._data[0]]
        else:
            property_array = self._data.copy()

        if len(property_array) == 2 and property_array[1] != 'uri':
            property_array[1] = hash_string(property_array[1])

        return property_array

    @property
    def entity_type_selection_internal_id(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def prop_name(self):
        return self._data[1] if len(self._data) == 2 else self._data[0]

    @property
    def extended_prop_label(self):
        return hash_string('.'.join(self.absolute_property)) + '_extended'

    @property
    def is_list(self):
        if self._columns and self.prop_label in self._columns:
            return self._columns[self.prop_label]['isList']

        return False

    @property
    def sql(self):
        absolute_property = [self.extended_prop_label] if self._extend and self.is_list else self.absolute_property
        sql = psycopg2_sql.SQL('.').join(map(psycopg2_sql.Identifier, absolute_property))

        for transformer in self._transformers:
            template_sql = psycopg2_sql.SQL(transformer['transformer_info']['sql_template'])
            sql_parameters = {key: psycopg2_sql.Literal(value) for (key, value) in transformer['parameters'].items()}
            sql = template_sql.format(property=sql, **sql_parameters)

        return sql

    @property
    def left_join(self):
        if self.is_list:
            sql = psycopg2_sql.SQL('LEFT JOIN UNNEST({table_name}.{column_name}) AS {column_name_expanded} ON true')

            return sql.format(
                table_name=psycopg2_sql.Identifier(self.entity_type_selection_internal_id),
                column_name=psycopg2_sql.Identifier(self.prop_label),
                column_name_expanded=psycopg2_sql.Identifier(self.extended_prop_label)
            )

        return psycopg2_sql.SQL('')
