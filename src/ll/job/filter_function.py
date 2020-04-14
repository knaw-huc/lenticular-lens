from psycopg2 import sql as psycopg2_sql
from ll.util.helpers import get_json_from_file


class FilterFunction:
    def __init__(self, function_obj, property):
        function_name = function_obj['type']

        filter_functions = get_json_from_file('filter_functions.json')
        if function_name in filter_functions:
            self._function_info = filter_functions[function_name]
        else:
            raise NameError('Filter function %s is not defined' % function_name)

        self._parameters = {key: psycopg2_sql.Literal(value) for key, value in function_obj.items()
                            if key not in ['operator', 'type', 'property']}

        if 'operator' in function_obj and function_obj['operator'] in ['=', '!=', '<>', '<=', '>=']:
            self._parameters['operator'] = psycopg2_sql.SQL(function_obj['operator'])

        self._parameters['property'] = property.sql
        self._parameters['property__0'] = psycopg2_sql.Identifier(property.entity_type_selection_label)
        self._parameters['property__1'] = psycopg2_sql.Identifier(property.prop_label)

    @property
    def sql(self):
        template = self._function_info['sql_template']
        return psycopg2_sql.SQL(template).format(**self._parameters)
