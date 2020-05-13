from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import hash_string, get_string_from_sql


class PropertyField:
    def __init__(self, data, parent_label=None, columns=None, transformers=None):
        self._data = data
        self._parent_label = parent_label
        self._columns = columns
        self._transformers = transformers if transformers else []
        self._extend = True

        self._hash = hash_string(get_string_from_sql(self.sql))

    def no_extend(self):
        self._extend = False

    @property
    def hash(self):
        return self._hash

    @property
    def absolute_property(self):
        if isinstance(self._data, list):
            property_array = self._data
        else:
            property_array = [self._data]

        property_array[len(property_array) - 1] = property_array[len(property_array) - 1].lower()
        property_array = list(map(hash_string, property_array))

        if self._parent_label and len(property_array) == 1:
            property_array.insert(0, self._parent_label)

        if len(property_array) == 2 and property_array[1] == hash_string('uri'):
            property_array[1] = 'uri'

        return property_array

    @property
    def entity_type_selection_label(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def prop_name(self):
        return self._data[1]

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
            sql = psycopg2_sql.SQL(cleandoc(
                """ LEFT JOIN unnest({table_name}.{column_name}) 
                    AS {column_name_expanded} ON true"""))

            return sql.format(
                table_name=psycopg2_sql.Identifier(self.entity_type_selection_label),
                column_name=psycopg2_sql.Identifier(self.prop_label),
                column_name_expanded=psycopg2_sql.Identifier(self.extended_prop_label)
            )

        return psycopg2_sql.SQL('')
