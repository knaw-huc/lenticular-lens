from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import get_json_from_file


class FilterFunction:
    def __init__(self, function_obj, property):
        function_name = function_obj['type']

        self._negate = False
        if function_name.startswith('not_'):
            self._negate = True
            function_name = function_name[4:]

        filter_functions = get_json_from_file('filter_functions.json')
        if function_name in filter_functions:
            self._function_info = filter_functions[function_name]
        else:
            raise NameError('Filter function %s is not defined' % function_name)

        if function_name == 'minimal_appearances' or function_name == 'maximum_appearances':
            property.no_extend()

        self._parameters = {key: psycopg2_sql.Literal(value) for key, value in function_obj.items()
                            if key not in ['type', 'property']}

        self._parameters['property'] = property.sql

    @property
    def sql(self):
        template = self._function_info['sql_template']
        if self._negate:
            template = 'NOT (' + template + ')'

        return psycopg2_sql.SQL(template).format(**self._parameters)
