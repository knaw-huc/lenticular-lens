import collections

from psycopg2 import sql as psycopg2_sql
from common.helpers import is_property_object, get_property_sql, get_absolute_property, get_json_from_file


class SqlFunction:
    def __init__(self, function_obj, parent_label=None):
        self.parent_label = parent_label
        for function_name, parameters in function_obj.items():
            self.function_name = function_name
            self.parameters = {}
            if isinstance(parameters, list):
                self.parameters['list_values'] = psycopg2_sql.SQL(', ') \
                    .join([self.get_value_sql(parameter) for parameter in parameters])
            elif isinstance(parameters, collections.Mapping):
                if is_property_object(parameters):
                    self.parameters['parameter'] = \
                        get_property_sql(get_absolute_property(parameters['property'], self.parent_label))
                else:
                    for key, value in parameters.items():
                        self.parameters[key] = self.get_value_sql(value)
            else:
                self.parameters['parameter'] = psycopg2_sql.Literal(parameters)

        self.is_aggregate = self.function_name.startswith('AGG_')

        sql_functions = get_json_from_file('sql_functions.json')
        if self.function_name in sql_functions:
            self.sql_template = sql_functions[self.function_name]
        else:
            raise NameError('SQL function %s is not defined' % self.function_name)

    def get_value_sql(self, value):
        if isinstance(value, collections.Mapping):
            if is_property_object(value):
                return get_property_sql(get_absolute_property(value['property'], self.parent_label))

            return SqlFunction(value, self.parent_label).sql

        return psycopg2_sql.Literal(value)

    @property
    def sql(self):
        template = self.sql_template
        sql = psycopg2_sql.SQL(template).format(**self.parameters)

        return sql
