from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql

from common.helpers import hash_string, get_json_from_file, get_string_from_sql


class PropertyField:
    def __init__(self, data, parent_label=None, columns=None, transformers=None):
        self.__data = data
        self.parent_label = parent_label
        self.columns = columns

        if transformers and len(transformers) > 0:
            white_list = get_json_from_file("transformers.json")
            self.transformers = [transformer for transformer in transformers if transformer in white_list]
        else:
            self.transformers = []

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

        return property_array

    @property
    def resource_label(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def extended_prop_label(self):
        return hash_string('.'.join(self.absolute_property)) + '_extended'

    @property
    def is_list(self):
        if self.columns and self.prop_label in self.columns:
            return self.columns[self.prop_label]['LIST']

        return False

    @property
    def sql(self):
        absolute_property = [self.extended_prop_label, 'value'] if self.is_list else self.absolute_property
        sql = psycopg2_sql.SQL('.').join(map(psycopg2_sql.Identifier, absolute_property))

        for transformer in self.transformers[::-1]:
            sql = psycopg2_sql.SQL('%s({})' % transformer).format(sql)

        return sql

    @property
    def left_join(self):
        if self.is_list:
            sql = psycopg2_sql.SQL(cleandoc(
                """ LEFT JOIN jsonb_array_elements_text({table_name}.{column_name}) 
                    AS {column_name_expanded} ON true"""))

            return sql.format(
                table_name=psycopg2_sql.Identifier(self.resource_label),
                column_name=psycopg2_sql.Identifier(self.prop_label),
                column_name_expanded=psycopg2_sql.Identifier(self.extended_prop_label)
            )

        return psycopg2_sql.SQL('')
