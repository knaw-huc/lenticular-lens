from helpers import hash_string, get_json_from_file, PropertyField
import json
from psycopg2 import sql as psycopg2_sql
import re


class Conditions:
    def __init__(self, data):
        self.__data = data
        self.__conditions_list = None

        self.conditions_list

    @property
    def conditions_list(self):
        if not self.__conditions_list:
            self.__conditions_list = self.r_conditions_list(self.__data)

        return self.__conditions_list

    def r_conditions_list(self, condition):
        if 'type' in condition:
            items = []
            for index, item in enumerate(condition['items']):
                condition['items'][index] = self.r_conditions_list(item)
                items.append(condition['items'][index])

            return items

        return self.MatchingFunction(condition)

    @property
    def conditions_sql(self):
        return self.r_conditions_sql(self.__data)

    def r_conditions_sql(self, condition):
        if not isinstance(condition, self.MatchingFunction) and 'type' in condition and condition['type'] in ['AND', 'OR']:

            filter_sqls = []
            for condition_item in condition['items']:
                filter_sqls.append(self.r_conditions_sql(condition_item))

            return psycopg2_sql.SQL('({})').format(psycopg2_sql.SQL(' %s ' % condition['type']).join(filter_sqls))

        return condition.sql.format(field_name=psycopg2_sql.Identifier(condition.field_name))

    @property
    def index_templates(self):
        return [condition.index_template for condition in self.conditions_list]

    class MatchingFunction:
        def __init__(self, function_obj):
            self.function_obj = function_obj
            self.__data = function_obj
            self.__sources = []
            self.__targets = []

            self.field_name = hash_string(json.dumps(function_obj))

            if isinstance(function_obj['method'], str):
                self.function_name = function_obj['method']
                self.parameters = ()
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
