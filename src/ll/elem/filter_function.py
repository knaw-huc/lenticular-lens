from psycopg2 import sql

from ll.util.hasher import hash_string_min
from ll.util.helpers import get_json_from_file


class FilterFunction:
    _filter_functions = get_json_from_file('filter_functions.json')

    def __init__(self, function_obj, property):
        self.function_name = function_obj['type']
        self.property_field = property

        if self.function_name in self._filter_functions:
            self._function_info = self._filter_functions[self.function_name]
        else:
            raise NameError('Filter function %s is not defined' % self.function_name)

        if not self.extend:
            self.property_field.no_extend()

        self.parameters = {key: value for key, value in function_obj.items()
                           if key not in ['type', 'property']}

    @property
    def extend(self):
        return self.function_name != 'minimal_appearances' and self.function_name != 'maximum_appearances'

    @property
    def value(self):
        return self.parameters.get('value')

    @property
    def sql(self):
        template = self._function_info['sql_template']

        parameters = {key: sql.Literal(value) for key, value in self.parameters.items()}
        parameters['property'] = self.property_field.sql

        return sql.SQL(template).format(**parameters)

    @property
    def hash(self):
        return hash_string_min((self.property_field.hash, self.function_name, self.parameters))

    def __eq__(self, other):
        return isinstance(other, FilterFunction) and self.hash == other.hash

    def __hash__(self):
        return hash(self.hash)
