from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import hash_string, get_string_from_sql


class PropertyField:
    def __init__(self, data, parent_label=None, columns=None, transformers=None):
        self.__data = data
        self.parent_label = parent_label
        self.columns = columns
        self.transformers = transformers if transformers else []

        self.__hash = hash_string(get_string_from_sql(self.sql))

    @property
    def hash(self):
        return self.__hash

    @property
    def absolute_property(self):
        if isinstance(self.__data, list):
            property_array = self.__data
        else:
            property_array = [self.__data]

        property_array[len(property_array) - 1] = property_array[len(property_array) - 1].lower()
        property_array = list(map(hash_string, property_array))

        if self.parent_label and len(property_array) == 1:
            property_array.insert(0, self.parent_label)

        if len(property_array) == 2 and property_array[1] == hash_string('uri'):
            property_array[1] = 'uri'

        return property_array

    @property
    def resource_label(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def prop_name(self):
        return self.__data[1]

    @property
    def extended_prop_label(self):
        return hash_string('.'.join(self.absolute_property)) + '_extended'

    @property
    def is_list(self):
        if self.columns and self.prop_label in self.columns:
            return self.columns[self.prop_label]['isList']

        return False

    @property
    def sql(self):
        absolute_property = [self.extended_prop_label] if self.is_list else self.absolute_property
        sql = psycopg2_sql.SQL('.').join(map(psycopg2_sql.Identifier, absolute_property))

        for transformer in self.transformers:
            template_sql = psycopg2_sql.SQL(transformer['transformer_info']['sql_template'])
            sql_parameters = {key: psycopg2_sql.Literal(value) for (key, value) in transformer['parameters'].items()}
            sql = template_sql.format(property=sql, **sql_parameters)

        return sql

    @property
    def left_join(self):
        if self.is_list:
            sql = psycopg2_sql.SQL(cleandoc(
                """ LEFT JOIN unnest({table_name}.{column_name}) 
                    AS {column_name_expanded} ON true""") + '\n')

            return sql.format(
                table_name=psycopg2_sql.Identifier(self.resource_label),
                column_name=psycopg2_sql.Identifier(self.prop_label),
                column_name_expanded=psycopg2_sql.Identifier(self.extended_prop_label)
            )

        return psycopg2_sql.SQL('')
