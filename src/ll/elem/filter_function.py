from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import get_json_from_file


class FilterFunction:
    def __init__(self, function_obj, property):
        self._function_name = function_obj['type']
        self._property = property

        filter_functions = get_json_from_file('filter_functions.json')
        if self._function_name in filter_functions:
            self._function_info = filter_functions[self._function_name]
        else:
            raise NameError('Filter function %s is not defined' % self._function_name)

        if not self.extend:
            self.property_field.no_extend()

        self._parameters = {key: psycopg2_sql.Literal(value) for key, value in function_obj.items()
                            if key not in ['type', 'property']}

        self._parameters['property'] = self.property_field.sql

    @property
    def property_field(self):
        return self._property

    @property
    def extend(self):
        return self._function_name != 'minimal_appearances' and self._function_name != 'maximum_appearances'

    @property
    def sql(self):
        template = self._function_info['sql_template']
        return psycopg2_sql.SQL(template).format(**self._parameters)
