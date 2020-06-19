from inspect import cleandoc
from psycopg2 import sql as psycopg_sql

from ll.util.helpers import hash_string
from ll.job.conditions import Conditions


class Linkset:
    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._conditions = None

    @property
    def id(self):
        return self._data['id']

    @property
    def conditions(self):
        if not self._conditions:
            methods = self._data['methods']
            self._conditions = Conditions(methods['conditions'], methods['type'], self._job)
        return self._conditions

    @property
    def conditions_sql(self):
        return self.conditions.conditions_sql

    @property
    def is_association(self):
        return self._data.get('is_association', False)

    @property
    def properties(self):
        return self._data['properties']

    @property
    def index_sql(self):
        index_sqls = []

        for template in self.conditions.index_templates:
            if 'template' not in template:
                continue
            if 'before_index' in template and template['before_index']:
                index_sqls.append(template['before_index'])

        for matching_function in self.conditions.matching_functions:
            if 'template' not in matching_function.index_template:
                continue

            field_name = matching_function.index_template['field_name']
            template = matching_function.index_template['template']
            template_sql = psycopg_sql.SQL(template) \
                .format(target=psycopg_sql.Identifier(field_name), **matching_function.sql_parameters)
            table_name = 'target' if len(matching_function.targets) > 0 else 'source'

            index_sqls.append(psycopg_sql.SQL('CREATE INDEX ON {} USING {};').format(
                psycopg_sql.Identifier(table_name), template_sql
            ))

        return psycopg_sql.SQL('\n').join(index_sqls) if index_sqls else None

    @property
    def entity_type_selections(self):
        return self.sources + self.targets

    @property
    def similarity_fields_agg_sql(self):
        fields = {}
        fields_added = []

        for match_func in self.conditions.matching_functions:
            if match_func.similarity_sql:
                name = match_func.field_name

                # Add source and target values; if not done already
                if name not in fields_added:
                    fields_added.append(name)
                    fields[name] = match_func.similarity_sql.format(field_name=psycopg_sql.Identifier(name))

        fields_sql = [psycopg_sql.SQL('jsonb_object_agg({}, {})').format(psycopg_sql.Literal(name), sim)
                      for name, sim in fields.items()]

        return psycopg_sql.SQL(' || ').join(fields_sql) if fields_sql else psycopg_sql.SQL('NULL::jsonb')

    @property
    def sources(self):
        return self._data['sources']

    @property
    def targets(self):
        return self._data['targets'] if 'targets' in self._data else []

    @property
    def source_sql(self):
        return self._get_combined_entity_type_selections_sql('sources')

    @property
    def target_sql(self):
        return self._get_combined_entity_type_selections_sql('targets')

    def get_fields(self, keys=None, only_matching_fields=True):
        if not isinstance(keys, list):
            keys = ['sources', 'targets']

        # Regroup properties by entity-type selection instead of by method
        ets_properties = {}
        for matching_function in self.conditions.matching_functions:
            for key in keys:
                for internal_id, properties in getattr(matching_function, key).items():
                    for property in properties:
                        ets_internal_id = internal_id if only_matching_fields \
                            else property.entity_type_selection_internal_id

                        if ets_internal_id not in ets_properties:
                            ets_properties[ets_internal_id] = {}

                        props = ets_properties[ets_internal_id].get(matching_function.field_name, [])
                        props.append(property)

                        ets_properties[ets_internal_id][matching_function.field_name] = props

        return ets_properties

    def _get_combined_entity_type_selections_sql(self, key):
        properties = self.get_fields([key])

        sql = []
        for ets_internal_id, ets_properties in properties.items():
            joins = []
            property_fields = []

            for property_label, ets_method_properties in ets_properties.items():
                join_name = hash_string(property_label)

                joins.append(psycopg_sql.SQL('INNER JOIN {res} AS {join_name} ON target.uri = {join_name}.uri').format(
                    res=psycopg_sql.Identifier(ets_internal_id),
                    join_name=psycopg_sql.Identifier(join_name)
                ))

                if len(ets_method_properties) == 1:
                    property_fields.append(psycopg_sql.SQL('{join_name}.{property_field} AS {field_name}').format(
                        join_name=psycopg_sql.Identifier(join_name),
                        property_field=psycopg_sql.Identifier(ets_method_properties[0].hash),
                        field_name=psycopg_sql.Identifier(property_label)
                    ))
                else:
                    joins.append(psycopg_sql.SQL('CROSS JOIN unnest(ARRAY[{fields}]) AS {extended_field_name}').format(
                        fields=psycopg_sql.SQL(', ').join(
                            [psycopg_sql.SQL('{join_name}.{property_field}').format(
                                join_name=psycopg_sql.Identifier(join_name),
                                property_field=psycopg_sql.Identifier(prop.hash)
                            ) for prop in ets_method_properties]
                        ),
                        extended_field_name=psycopg_sql.Identifier(property_label + '_extended')
                    ))

                    property_fields.append(psycopg_sql.SQL('{extended_field_name} AS {field_name}').format(
                        extended_field_name=psycopg_sql.Identifier(property_label + '_extended'),
                        field_name=psycopg_sql.Identifier(property_label)
                    ))

            sql.append(
                psycopg_sql.SQL(cleandoc(
                    """SELECT DISTINCT {collection} AS collection, target.uri, {matching_fields}
                       FROM {res} AS target
                       {joins}"""
                )).format(
                    collection=psycopg_sql.Literal(ets_internal_id),
                    matching_fields=psycopg_sql.SQL(',\n           ').join(property_fields),
                    res=psycopg_sql.Identifier(ets_internal_id),
                    joins=psycopg_sql.SQL('\n').join(joins),
                )
            )

        return psycopg_sql.SQL('\nUNION ALL\n').join(sql)
