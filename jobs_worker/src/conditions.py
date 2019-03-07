from helpers import hash_string, get_json_from_file
from psycopg2 import sql as psycopg2_sql
import re


class Conditions:
    def __init__(self, data):
        self.__data = data

    @property
    def conditions_list(self):
        conditions_list = self.r_conditions_list(self.__data)

        return conditions_list

    def r_conditions_list(self, condition):
        if 'type' in condition:
            return [self.r_conditions_list(item) for item in condition['items']]

        return self.MatchingFunction(condition)

    @property
    def conditions_sql(self):
        return self.r_conditions_sql(self.__data)

    def r_conditions_sql(self, condition):
        if 'type' in condition and condition['type'] in ['AND', 'OR']:
            filter_sqls = map(self.r_conditions_sql, condition['items'])
            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % condition['type']).join(filter_sqls))

        return self.MatchingFunction(condition).sql

    @property
    def index_templates(self):
        return self.r_index_templates(self.__data)

    def r_index_templates(self, condition):
        if 'type' in condition:
            return [self.r_index_templates(item) for item in condition['items'] if item]

        return self.MatchingFunction(condition).index_template

    class MatchingFunction:
        def __init__(self, function_obj):
            self.raw_field_name = function_obj['matching_field']
            self.field_name =\
                self.raw_field_name[2::] if self.raw_field_name.startswith('__')\
                else hash_string(self.raw_field_name)

            if isinstance(function_obj['method'], str):
                self.function_name = function_obj['method']
                self.parameters = []
            else:
                for function_name, parameters in function_obj['method'].items():
                    self.function_name = function_name
                    self.parameters = parameters

            matching_functions = get_json_from_file('matching_functions.json')
            if self.function_name in matching_functions:
                self.function_info = matching_functions[self.function_name]
                if 'similarity' in function_obj:
                    self.function_info['similarity'] = function_obj['similarity']
            else:
                raise NameError('Matching function %s is not defined' % self.function_name)

        @property
        def index_template(self):
            if 'index_using' not in self.function_info:
                return {}

            before_index = self.function_info.get('before_index', None)
            if before_index:
                for index, parameter in enumerate(self.parameters):
                    before_index = re.sub('%%%i__hash' % (index + 1), hash_string(str(parameter)), before_index)
                    before_index = re.sub('%%%i' % (index + 1), str(parameter), before_index)

            return {
                'template': self.function_info['index_using'],
                'field_name': self.raw_field_name,
                'before_index': before_index,
            }

        @property
        def similarity_sql(self):
            if 'similarity' not in self.function_info or not self.function_info['similarity']:
                return None

            template = self.function_info['similarity']
            if isinstance(self.function_info['similarity'], str):
                template = re.sub(r'{source}', 'source.{field_name}', template)
                template = re.sub(r'{target}', 'target.{field_name}', template)
                for index, parameter in enumerate(self.parameters):
                    template = re.sub('%%%i' % (index + 1), str(parameter), template)

            return psycopg2_sql.SQL(str(template)).format(field_name=psycopg2_sql.Identifier(self.field_name))

        @property
        def sql(self):
            template = self.function_info['sql_template']
            for index, parameter in enumerate(self.parameters):
                template = re.sub('%%%i__hash' % (index + 1), hash_string(str(parameter)), template)
                template = re.sub('%%%i' % (index + 1), str(parameter), template)

            template = re.sub(r'{source}', 'source.{field_name}', template)
            template = re.sub(r'{target}', 'target.{field_name}', template)

            sql = psycopg2_sql.SQL(template).format(field_name=psycopg2_sql.Identifier(self.field_name))

            return sql
