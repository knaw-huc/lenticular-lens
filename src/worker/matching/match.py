from worker.matching.conditions import Conditions
from common.helpers import hash_string
from psycopg2 import sql as psycopg_sql


class Match:
    def __init__(self, data):
        self.__data = data
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
            self.__conditions = Conditions(self.__data['conditions'], self.__data['type'])
        return self.__conditions

    @property
    def conditions_sql(self):
        return self.conditions.conditions_sql

    @property
    def id(self):
        return str(self.__data.get('id', ''))

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
                    resource_field_name = matching_function.index_template['field_name'][2::]\
                        if matching_function.index_template['field_name'].startswith('__')\
                        else property_field.hash

                    template =\
                        matching_function.format_template(matching_function.index_template['template'], target='{target}')\
                        if matching_function.parameters else\
                        matching_function.index_template['template']

                    template_sql = psycopg_sql.SQL(template).format(
                        target=psycopg_sql.Identifier(resource_field_name))

                    index_sqls.append(psycopg_sql.SQL('CREATE INDEX ON {} USING {};').format(
                        psycopg_sql.Identifier(hash_string(resource_name)), template_sql))

        return psycopg_sql.SQL('\n').join(index_sqls)

    @property
    def matches_dependencies(self):
        dependencies = []

        for matching_function in self.conditions.matching_functions:
            if matching_function.function_name == 'IS_IN_SET':
                dependencies += str(matching_function.parameters['alignment']['value'])

        return dependencies

    @property
    def materialize(self):
        return self.meta.get('materialize', True)

    @property
    def meta(self):
        return self.__data.get('meta', {})

    @property
    def name(self):
        return hash_string(self.name_original)

    @property
    def name_original(self):
        return self.__data['label']

    @property
    def resources(self):
        return self.sources + self.targets

    @property
    def similarity_fields_sql(self):
        fields = []
        fields_added = []

        for matching_function in self.conditions.matching_functions:
            if matching_function.similarity_sql:
                field_name = psycopg_sql.Identifier(matching_function.field_name)

                # Add source and target values; if not done already
                if field_name not in fields_added:
                    fields_added.append(field_name)

                    fields.append(psycopg_sql.SQL('source.{field_name} AS {source_field_name}').format(
                        field_name=field_name,
                        source_field_name=psycopg_sql.Identifier(f'source_{matching_function.field_name}')
                    ))

                    fields.append(psycopg_sql.SQL('target.{field_name} AS {target_field_name}').format(
                        field_name=field_name,
                        target_field_name=psycopg_sql.Identifier(f'target_{matching_function.field_name}')
                    ))

                    # Add similarity field
                    fields.append(psycopg_sql.SQL('{field} AS {field_name}').format(
                        field=matching_function.similarity_sql.format(field_name=field_name),
                        field_name=psycopg_sql.Identifier(matching_function.field_name + '_similarity')
                    ))

                cluster_field = matching_function.similarity_sql.format(field_name=field_name)

        # This is a temporary way to select the similarity of the last matching method for the clustering
        fields.append(psycopg_sql.SQL('{} AS __cluster_similarity').format(cluster_field))

        return psycopg_sql.SQL(',\n       ').join(fields)

    @property
    def source_sql(self):
        return self.get_combined_resources_sql('sources')

    @property
    def target_sql(self):
        return self.get_combined_resources_sql('targets') if 'targets' in self.__data else self.source_sql

    @property
    def sources(self):
        return self.__data['sources']

    @property
    def targets(self):
        return self.__data['targets'] if 'targets' in self.__data else []

    def get_combined_resources_sql(self, resources_key):
        resources_properties = self.get_matching_fields([resources_key])

        resources_sql = []

        for resource_label, resource_properties in resources_properties.items():
            property_fields = []
            for property_label, resource_method_properties in resource_properties.items():
                property_field = psycopg_sql.Identifier(resource_method_properties[0].hash)\
                    if len(resource_method_properties) == 1\
                    else psycopg_sql.SQL('unnest(ARRAY[{}])').format(
                        psycopg_sql.SQL(', ').join([
                            psycopg_sql.Identifier(resource_property.hash)
                            for resource_property in resource_method_properties]))
                property_fields.append(psycopg_sql.SQL('{property_field} AS {field_name}')
                                       .format(
                                            property_field=property_field,
                                            field_name=psycopg_sql.Identifier(property_label)))

            property_fields_sql = psycopg_sql.SQL(',\n           ').join(property_fields)

            resources_sql.append(psycopg_sql.SQL("""
    SELECT DISTINCT {collection} AS collection,
           uri,
           {matching_fields}
    FROM {resource_label}
""").format(
                collection=psycopg_sql.Literal(resource_label),
                matching_fields=property_fields_sql,
                resource_label=psycopg_sql.Identifier(resource_label)
            ))

        return psycopg_sql.SQL('    UNION ALL').join(resources_sql)

    def get_matching_fields(self, resources_keys=None):
        import sys
        if not isinstance(resources_keys, list):
            resources_keys = ['sources', 'targets']

        # Regroup properties by resource instead of by method
        # resources_properties = {hash_string(resource_name): {} for resource_name in getattr(self, 'sources') + getattr(self, 'targets')}
        resources_properties = {}
        for matching_function in self.conditions.matching_functions:
            for resources_key in resources_keys:
                for resource_label, resource_properties in getattr(matching_function, resources_key).items():
                    resource_label = hash_string(resource_label)
                    if resource_label not in resources_properties:
                        resources_properties[resource_label] = {}

                    resources_properties[resource_label][matching_function.field_name] = \
                        resources_properties[resource_label].get(matching_function.field_name, []) + resource_properties

        # print(resources_properties, file=sys.stderr)
        return resources_properties

        # resources_properties = {
        #     'Resource label': {
        #         'value_n': [
        #             Property,
        #         ],
        #     },
        # }
