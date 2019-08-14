from common.helpers import get_json_from_file, get_absolute_property, get_property_sql, get_extended_property_sql
from psycopg2 import sql as psycopg2_sql


class FilterFunction:
    def __init__(self, function_obj, parent_label, is_list):
        self.function_name = function_obj['type']

        filter_functions = get_json_from_file('filter_functions.json')
        if self.function_name in filter_functions:
            self.function_info = filter_functions[self.function_name]
        else:
            raise NameError('Filter function %s is not defined' % self.function_name)

        self.parameters = {key: psycopg2_sql.Literal(value) for key, value in function_obj.items()
                           if key not in ['operator', 'type']}

        if 'operator' in function_obj and function_obj['operator'] in ['=', '!=', '<>', '<=', '>=']:
            self.parameters['operator'] = psycopg2_sql.SQL(function_obj['operator'])

        absolute_property = get_absolute_property(function_obj['property'], parent_label)
        if absolute_property[0] != parent_label and 'sql_template_remote' in self.function_info:
            self.function_info['sql_template'] = self.function_info['sql_template_remote']
            self.parameters['__relation__remote_property'] = psycopg2_sql.Identifier(
                parent_label + '__' + absolute_property[0] + '__relation__remote_property'
            )
            self.parameters['__relation__remote_property__1'] = psycopg2_sql.Identifier(
                parent_label + '__' + absolute_property[0] + '__relation__remote_property__1'
            )
            self.parameters['__relation__local_property'] = psycopg2_sql.Identifier(
                parent_label + '__' + absolute_property[0] + '__relation__local_property'
            )
            self.parameters['__relation__local_property__1'] = psycopg2_sql.Identifier(
                parent_label + '__' + absolute_property[0] + '__relation__local_property__1'
            )

        self.parameters['property'] = get_extended_property_sql(absolute_property) \
            if is_list else get_property_sql(absolute_property)
        self.parameters['property__0'] = get_property_sql([absolute_property[0]])
        self.parameters['property__1'] = get_property_sql([absolute_property[1]])
        self.parameters['property__0__original_view'] = psycopg2_sql.Identifier(absolute_property[0] + '__original')

    @property
    def sql(self):
        template = self.function_info['sql_template']

        if self.parameters.get('invert', False):
            template = 'NOT ' + template

        sql = psycopg2_sql.SQL(template).format(**self.parameters)

        return sql
