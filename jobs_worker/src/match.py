from conditions import Conditions
from helpers import hash_string, PropertyField
from psycopg2 import sql as psycopg_sql


class Match:
    def __init__(self, data):
        data['sources'] = self.objectify_matching_fields(data['sources'])
        if 'targets' in data:
            data['targets'] = self.objectify_matching_fields(data['targets'])

        self.__data = data

        if 'targets' not in self.__data:
            self.__data['conditions']['items'].insert(0, {'matching_field': '__uri', 'method': '>', 'similarity': None})

    @property
    def conditions(self):
        return Conditions(self.__data['conditions'])

    @property
    def conditions_sql(self):
        return self.conditions.conditions_sql

    @property
    def index_sql(self):
        index_sqls = []
        for template in self.conditions.index_templates:
            if 'before_index' in template and template['before_index']:
                index_sqls.append(psycopg_sql.SQL(template['before_index']))

            resources = self.targets if len(self.targets) > 0 else self.sources
            for resource in resources:
                resource_field_name = template['field_name'][2::]\
                    if template['field_name'].startswith('__')\
                    else resource['matching_fields'][template['field_name']].hash

                template_sql = psycopg_sql.SQL(template['template']).format(
                    target=psycopg_sql.Identifier(resource_field_name))

                index_sqls.append(psycopg_sql.SQL('CREATE INDEX ON {} USING {};').format(
                    psycopg_sql.Identifier(hash_string(resource['resource'])), template_sql))

        return psycopg_sql.SQL('\n').join(index_sqls)

    @property
    def materialize(self):
        return 'materialize' not in self.meta or self.meta['materialize'] is True

    @property
    def meta(self):
        return self.__data.get('meta', {})

    @property
    def name(self):
        return hash_string(self.__data['label'])

    @property
    def resources(self):
        return self.sources + self.targets

    @property
    def similarity_fields_sql(self):
        fields = []

        for condition in self.conditions.conditions_list:
            if condition.similarity_sql:
                fields.append(psycopg_sql.SQL('{field} AS {field_name}')
                                 .format(
                                    field=condition.similarity_sql,
                                    field_name=psycopg_sql.Identifier(condition.raw_field_name + '_similarity')
                ))

        return psycopg_sql.SQL(',\n       ').join(fields)

    @property
    def source_sql(self):
        return self.get_combined_resources_sql(self.sources)

    @property
    def target_sql(self):
        return self.get_combined_resources_sql(self.targets) if 'targets' in self.__data else self.source_sql

    @property
    def sources(self):
        return self.__data['sources']

    @property
    def targets(self):
        return self.__data['targets'] if 'targets' in self.__data else []

    @staticmethod
    def objectify_matching_fields(resources):
        for resource in resources:
            matching_fields = {}
            for matching_field in resource['matching_fields']:
                matching_fields[matching_field['label']] = PropertyField(matching_field, hash_string(resource['resource']))
            resource['matching_fields'] = matching_fields

        return resources

    def get_combined_resources_sql(self, resources):
        resources_sql = []

        for resource in resources:
            matching_fields = []
            for field_name, matching_field in resource['matching_fields'].items():
                matching_fields.append(psycopg_sql.SQL('{matching_field} AS {field_name}')\
                                          .format(
                                            matching_field=psycopg_sql.Identifier(matching_field.hash),
                                            field_name=psycopg_sql.Identifier(hash_string(field_name))))
            matching_fields_sql = psycopg_sql.SQL(',\n           ').join(matching_fields)

            resources_sql.append(psycopg_sql.SQL("""
    SELECT uri,
           {matching_fields}
    FROM {resource_label}
"""
                                         )
                                    .format(
                                        matching_fields=matching_fields_sql,
                                        resource_label=psycopg_sql.Identifier(hash_string(resource['resource']))
            ))

        return psycopg_sql.SQL('    UNION ALL').join(resources_sql)

    def get_matching_fields(self, resource_label=None):
        matching_fields = {}

        for resource in self.resources:
            if resource_label is None or hash_string(resource['resource']) == resource_label:
                for matching_field in resource['matching_fields'].values():
                    if matching_field.hash not in matching_fields:
                        matching_fields[matching_field.hash] = matching_field

        return matching_fields
