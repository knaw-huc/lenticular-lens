from psycopg2 import sql as psycopg2_sql
from common.helpers import get_json_from_file


class FilterFunction:
    def __init__(self, function_obj, property):
        self.function_name = function_obj['type']

        filter_functions = get_json_from_file('filter_functions.json')
        if self.function_name in filter_functions:
            self.function_info = filter_functions[self.function_name]
        else:
            raise NameError('Filter function %s is not defined' % self.function_name)

        self.parameters = {key: psycopg2_sql.Literal(value) for key, value in function_obj.items()
                           if key not in ['operator', 'type', 'property']}

        if 'operator' in function_obj and function_obj['operator'] in ['=', '!=', '<>', '<=', '>=']:
            self.parameters['operator'] = psycopg2_sql.SQL(function_obj['operator'])

        self.parameters['property'] = property.sql
        self.parameters['property__0'] = psycopg2_sql.Identifier(property.resource_label)
        self.parameters['property__1'] = psycopg2_sql.Identifier(property.prop_label)

    @property
    def sql(self):
        template = self.function_info['sql_template']
        return psycopg2_sql.SQL(template).format(**self.parameters)
