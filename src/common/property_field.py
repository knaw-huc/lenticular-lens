import collections

from psycopg2 import sql as psycopg2_sql
from common.sql_function import SqlFunction
from common.helpers import hash_string, get_json_from_file, \
    get_absolute_property, get_property_sql, get_extended_property_sql, get_string_from_sql


class PropertyField:
    def __init__(self, data):
        self.is_aggregate = False
        self.__data = data
        self.__hash = None
        self.__transformers = None

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = hash_string(get_string_from_sql(self.sql(False)))

        return self.__hash

    @property
    def label(self):
        return self.__data['label']

    @property
    def absolute_property(self):
        return get_absolute_property(self.__data['property'])

    @property
    def resource_label(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def transformers(self):
        if not self.__transformers:
            if 'transformers' in self.__data:
                white_list = get_json_from_file("transformers.json")

                self.__transformers = [transformer for transformer in self.__data['transformers'] if
                                       transformer in white_list]
                for transformer in self.__data['transformers']:
                    if transformer not in white_list:
                        raise self.TransformerUnknown('Transformer "%s" is not whitelisted.' % transformer)
            else:
                self.__transformers = []

        return self.__transformers

    def sql(self, is_list):
        if 'property' in self.__data:
            sql = get_extended_property_sql(get_absolute_property(self.__data['property'])) \
                if is_list else get_property_sql(get_absolute_property(self.__data['property']))
        elif isinstance(self.__data['value'], collections.Mapping):
            sql_function = SqlFunction(self.__data['value'])
            self.is_aggregate = sql_function.is_aggregate
            sql = sql_function.sql
        else:
            sql = psycopg2_sql.Literal(self.__data['value'])

        for transformer in self.transformers[::-1]:
            sql = psycopg2_sql.SQL('%s({})' % transformer).format(sql)

        return sql

    class TransformerUnknown(ValueError):
        """This means the transformer is not whitelisted"""
