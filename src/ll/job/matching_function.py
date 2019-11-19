import re
import json

from psycopg2 import sql as psycopg2_sql

from ll.job.property_field import PropertyField
from ll.util.helpers import hash_string, get_json_from_file


class MatchingFunction:
    transformers = get_json_from_file('transformers.json')
    matching_functions = get_json_from_file('matching_functions.json')

    def __init__(self, function_obj, config):
        self.function_obj = function_obj
        self.__data = function_obj
        self.__config = config
        self.__sources = []
        self.__targets = []

        self.field_name = hash_string(json.dumps(function_obj))

        self.function_name = function_obj['method_name']
        self.parameters = function_obj['method_value']

        if self.function_name in self.matching_functions:
            self.function_info = self.matching_functions[self.function_name]
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
            before_index = psycopg2_sql.SQL(before_index)

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
            template = re.sub(r'{source}', 'source.{field_name}', template)
            template = re.sub(r'{target}', 'target.{field_name}', template)

        return psycopg2_sql.SQL(str(template))

    @property
    def sql(self):
        template = self.function_info['sql_template']
        template = re.sub(r'{source}', 'source.{field_name}', template)
        template = re.sub(r'{target}', 'target.{field_name}', template)

        return psycopg2_sql.SQL(template)

    @property
    def sql_parameters(self):
        return {key: psycopg2_sql.Literal(value) for (key, value) in self.parameters.items()}

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

    def get_resources(self, resources_key):
        resources = {}
        for resource_index, resource in self.__data[resources_key].items():
            resources[resource_index] = []
            for field in resource:
                field_transformers = field.get('transformers', [])

                for transformer in field_transformers:
                    if transformer['name'] in self.transformers:
                        transformer['transformer_info'] = self.transformers[transformer['name']]
                    else:
                        raise NameError('Transformer %s is not defined' % transformer['name'])

                columns = self.__config.get_resource_by_label(hash_string(field['property'][0])).columns
                property_field = PropertyField(field['property'], columns=columns, transformers=field_transformers)

                resources[resource_index].append(property_field)

        return resources
