from helpers import hash_string, get_json_from_file, PropertyField
import json
from psycopg2 import sql as psycopg2_sql
import re


class Conditions:
    def __init__(self, data, type):
        self.__data = data
        self.__type = type
        self.__conditions_list = None

    @property
    def conditions_list(self):
        if not self.__conditions_list:
            self.__conditions_list = []
            for idx, item in enumerate(self.__data):
                if 'conditions' in item and 'type' in item:
                    self.__conditions_list.append(Conditions(item['conditions'], item['type']))
                else:
                    self.__conditions_list.append(self.MatchingFunction(item))

        return self.__conditions_list

    @property
    def conditions_sql(self):
        filter_sqls = []
        for condition in self.__conditions_list:
            if isinstance(condition, self.MatchingFunction):
                filter_sqls.append(condition.sql.format(field_name=psycopg2_sql.Identifier(condition.field_name)))
            else:
                filter_sqls.append(condition.conditions_sql)

        return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % self.__type).join(filter_sqls))

    @property
    def index_templates(self):
        return [matching_function.index_template for matching_function in self.matching_functions]

    @property
    def matching_functions(self):
        matching_functions = []
        for condition in self.conditions_list:
            if isinstance(condition, self.MatchingFunction):
                matching_functions.append(condition)
            else:
                matching_functions += condition.matching_functions

        return matching_functions

    class MatchingFunction:
        def __init__(self, function_obj):
            self.function_obj = function_obj
            self.__data = function_obj
            self.__sources = []
            self.__targets = []

            self.field_name = hash_string(json.dumps(function_obj))

            self.function_name = function_obj['method_name']
            self.parameters = function_obj['method_value']

            matching_functions = get_json_from_file('matching_functions.json')
            if self.function_name in matching_functions:
                self.function_info = matching_functions[self.function_name]
                if 'similarity' in function_obj:
                    self.function_info['similarity'] = function_obj['similarity']
            else:
                raise NameError('Matching function %s is not defined' % self.function_name)

        @property
        def before_alignment(self):
            return self.function_info.get('before_alignment', '')

        @property
        def index_template(self):
            if 'index_using' not in self.function_info:
                return {}

            before_index = self.function_info.get('before_index', None)
            if before_index:
                before_index = self.format_template(before_index)

            return {
                'template': self.function_info['index_using'],
                'field_name': self.field_name,
                'before_index': before_index,
            }

        @property
        def similarity_sql(self):
            if 'similarity' not in self.function_info or not self.function_info['similarity']:
                return None

            template = self.function_info['similarity']
            if isinstance(self.function_info['similarity'], str):
                template = re.sub(r'{source}', 'source.{{field_name}}', template)
                template = re.sub(r'{target}', 'target.{{field_name}}', template)
                template = self.format_template(template)

            return psycopg2_sql.SQL(str(template))

        @property
        def sql(self):
            def hash_match_group(match):
                return hash_string(match.group(1))

            template = self.function_info['sql_template']

            template = re.sub(r'{source}', 'source.{{field_name}}', template)
            template = re.sub(r'{target}', 'target.{{field_name}}', template)
            template = self.format_template(template)
            template = re.sub(r'__hash\(([^)]*)\)', hash_match_group, template)

            return psycopg2_sql.SQL(str(template))

        @property
        def sources(self):
            if not self.__sources:
                self.__sources = self.get_resources('sources')

            return self.__sources

        @property
        def targets(self):
            if not self.__targets:
                self.__targets = self.get_resources('targets')

            return self.__targets
        
        def format_template(self, template, **additional_params):
            if isinstance(self.parameters, dict):
                return template.format(**self.parameters, **additional_params)
            return template.format(*self.parameters)

        def get_resources(self, resources_key):
            resources = {}
            for resource_index, resource in self.__data[resources_key].items():
                resources[resource_index] = []
                for property_field in resource:
                    # Add method's default transformers
                    property_field['transformers'] =\
                        self.function_info.get('transformers', []) + property_field.get('transformers', [])

                    resources[resource_index].append(PropertyField(property_field))

            return resources
