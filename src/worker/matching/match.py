from inspect import cleandoc
from psycopg2 import sql as psycopg_sql

from common.helpers import hash_string
from worker.matching.conditions import Conditions


class Match:
    def __init__(self, data, config):
        self.__data = data
        self.config = config
        self.__conditions = None

    @property
    def before_alignment(self):
        sqls = []

        for matching_function in self.conditions.matching_functions:
            if matching_function.before_alignment:
                sqls.append(psycopg_sql.SQL(matching_function.before_alignment))

        return psycopg_sql.SQL('\n').join(sqls)

    @property
    def conditions(self):
        if not self.__conditions:
            methods = self.__data['methods']
            self.__conditions = Conditions(methods['conditions'], methods['type'], self.config)
        return self.__conditions

    @property
    def conditions_sql(self):
        return self.conditions.conditions_sql

    @property
    def id(self):
        return self.__data.get('id', '')

    @property
    def is_association(self):
        return self.__data.get('is_association', False)

    @property
    def index_sql(self):
        index_sqls = []

        for template in self.conditions.index_templates:
            if 'template' not in template:
                continue
            if 'before_index' in template and template['before_index']:
                index_sqls.append(psycopg_sql.SQL(template['before_index']))

        for matching_function in self.conditions.matching_functions:
            if 'template' not in matching_function.index_template:
                continue

            resources = matching_function.targets if len(matching_function.targets) > 0 else matching_function.sources
            for resource_name, resource in resources.items():
                for property_field in resource:
                    resource_field_name = matching_function.index_template['field_name'][2::] \
                        if matching_function.index_template['field_name'].startswith('__') \
                        else property_field.hash

                    template = matching_function.index_template['template']
                    if matching_function.parameters:
                        template = matching_function.format_template(template, target='{target}')

                    template_sql = psycopg_sql.SQL(template).format(target=psycopg_sql.Identifier(resource_field_name))

                    index_sqls.append(psycopg_sql.SQL('CREATE INDEX ON {} USING {};').format(
                        psycopg_sql.Identifier(hash_string(resource_name)), template_sql
                    ))

        return psycopg_sql.SQL('\n').join(index_sqls)

    @property
    def match_against(self):
        return self.__data.get('match_against', None)

    @property
    def match_against_sql(self):
        if self.match_against:
            match_table = 'linkset_' + self.config.job_id + '_' + str(self.match_against)

            sql = psycopg_sql.SQL(cleandoc('''
                AND EXISTS (
                    SELECT 1
                    FROM {match_name} AS in_set 
                    WHERE in_set.source_uri IN (source.uri, target.uri) 
                    AND in_set.target_uri IN (source.uri, target.uri) 
                    LIMIT 1
                )'''))

            return sql.format(match_name=psycopg_sql.Identifier(match_table))

        return psycopg_sql.SQL('')

    @property
    def materialize(self):
        return self.meta.get('materialize', True)

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
    def similarity_fields_agg_sql(self):
        fields = []
        fields_added = []

        for matching_function in self.conditions.matching_functions:
            if matching_function.similarity_sql:
                field_name = psycopg_sql.Identifier(matching_function.field_name)

                # Add source and target values; if not done already
                if field_name not in fields_added:
                    fields_added.append(field_name)
                    fields.append(psycopg_sql.SQL('array_agg({})').format(
                        matching_function.similarity_sql.format(field_name=field_name)
                    ))

        return psycopg_sql.SQL(' || ').join(fields)

    @property
    def source_sql(self):
        return self.get_combined_resources_sql('sources', self.name + '_source_count')

    @property
    def target_sql(self):
        return self.get_combined_resources_sql('targets', self.name + '_target_count') \
            if 'targets' in self.__data else self.source_sql

    @property
    def sources(self):
        return self.__data['sources']

    @property
    def targets(self):
        return self.__data['targets'] if 'targets' in self.__data else []

    def get_combined_resources_sql(self, resources_key, sequence_key):
        resources_properties = self.get_fields([resources_key])

        resources_sql = []

        for resource_label, resource_properties in resources_properties.items():
            property_fields = []
            for property_label, resource_method_properties in resource_properties.items():
                if len(resource_method_properties) == 1:
                    property_field = psycopg_sql.Identifier(resource_method_properties[0].hash)
                else:
                    property_field = psycopg_sql.SQL('unnest(ARRAY[{}])').format(psycopg_sql.SQL(', ').join(
                        [psycopg_sql.Identifier(resource_property.hash)
                         for resource_property in resource_method_properties]
                    ))

                property_fields.append(psycopg_sql.SQL('{property_field} AS {field_name}').format(
                    property_field=property_field,
                    field_name=psycopg_sql.Identifier(property_label)
                ))

            property_fields_sql = psycopg_sql.SQL(',\n           ').join(property_fields)

            resources_sql.append(
                psycopg_sql.SQL(cleandoc(
                    """SELECT DISTINCT {collection} AS collection, uri, {matching_fields}
                       FROM {resource_label}
                       WHERE nextval({sequence}) != 0"""
                )).format(
                    collection=psycopg_sql.Literal(resource_label),
                    matching_fields=property_fields_sql,
                    resource_label=psycopg_sql.Identifier(resource_label),
                    sequence=psycopg_sql.Literal(sequence_key)
                )
            )

        return psycopg_sql.SQL('\nUNION ALL\n').join(resources_sql)

    def get_fields(self, resources_keys=None, only_matching_fields=True):
        if not isinstance(resources_keys, list):
            resources_keys = ['sources', 'targets']

        # Regroup properties by resource instead of by method
        resources_properties = {}
        for matching_function in self.conditions.matching_functions:
            for resources_key in resources_keys:
                for resource_label, resource_properties in getattr(matching_function, resources_key).items():
                    for resource_property in resource_properties:
                        res_label = hash_string(resource_label) if only_matching_fields \
                            else resource_property.resource_label

                        if res_label not in resources_properties:
                            resources_properties[res_label] = {}

                        props = resources_properties[res_label].get(matching_function.field_name, [])
                        props.append(resource_property)

                        resources_properties[res_label][matching_function.field_name] = props

        return resources_properties
