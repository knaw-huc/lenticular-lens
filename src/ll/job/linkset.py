from inspect import cleandoc
from psycopg2 import sql as psycopg_sql

from ll.util.hasher import hash_string_min
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

    # @property
    # def similarity_sql(self):
    #     return self.conditions.similarity_sql
    #
    # @property
    # def similarity_fields(self):
    #     return self.conditions.similarity_fields

    @property
    def is_association(self):
        return self._data.get('is_association', False)

    @property
    def properties(self):
        return self._data['properties']

    @property
    def index_sql(self):
        index_sqls = []
        for matching_function in self.conditions.matching_functions:
            if matching_function.index_sql:
                index_sqls.append(matching_function.index_sql)

        return psycopg_sql.SQL('\n').join(index_sqls) if index_sqls else None

    @property
    def entity_type_selections(self):
        return self.sources + self.targets + self.intermediates

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
                    fields[name] = match_func.similarity_sql

        fields_sql = [psycopg_sql.SQL('{}, array_agg({})').format(psycopg_sql.Literal(name), sim)
                      for name, sim in fields.items()]

        return psycopg_sql.SQL('jsonb_build_object({})').format(psycopg_sql.SQL(', ').join(fields_sql)) \
            if fields_sql else psycopg_sql.SQL('NULL::jsonb')

    @property
    def sources(self):
        return self._data['sources']

    @property
    def targets(self):
        return self._data['targets']

    @property
    def intermediates(self):
        return self._data['intermediates']

    @property
    def source_sql(self):
        return self._get_combined_entity_type_selections_sql(is_source=True)

    @property
    def target_sql(self):
        return self._get_combined_entity_type_selections_sql(is_source=False)

    def get_fields(self, keys=None, only_matching_fields=True):
        if not isinstance(keys, list):
            keys = ['sources', 'targets', 'intermediates']

        # Regroup properties by entity-type selection instead of by method
        ets_properties = {}
        for matching_function in self.conditions.matching_functions:
            for key in keys:
                for internal_id, properties in getattr(matching_function, key).items():
                    if key == 'sources' or key == 'targets':
                        for property in properties:
                            self._set_field(internal_id, property, matching_function,
                                            ets_properties, only_matching_fields)
                    else:
                        self._set_field(internal_id, properties['source'], matching_function,
                                        ets_properties, only_matching_fields)
                        self._set_field(internal_id, properties['target'], matching_function,
                                        ets_properties, only_matching_fields)

        return ets_properties

    @staticmethod
    def _set_field(internal_id, property, matching_function, ets_properties, only_matching_fields):
        ets_internal_id = internal_id if only_matching_fields \
            else property.entity_type_selection_internal_id

        if ets_internal_id not in ets_properties:
            ets_properties[ets_internal_id] = {}

        if matching_function.field_name not in ets_properties[ets_internal_id]:
            ets_properties[ets_internal_id][matching_function.field_name] = {
                'matching_function': matching_function,
                'properties': []
            }

        props = ets_properties[ets_internal_id][matching_function.field_name]['properties']
        props.append(property)

    def _get_combined_entity_type_selections_sql(self, is_source=True):
        sql = []
        properties = self.get_fields(['sources'] if is_source else ['targets'])

        # Get the properties needed for the source or target per entity-type selection
        for ets_internal_id, ets_properties in properties.items():
            joins = []
            matching_fields = []
            props_not_null = []
            prev_fields = []

            # Then for get all properties from this entity-type selection required for a single matching function
            for property_label, ets_matching_func_props in ets_properties.items():
                matching_func = ets_matching_func_props['matching_function']
                ets_method_properties = ets_matching_func_props['properties']

                # In case of list matching, combine all values into a field
                if matching_func.list_threshold:
                    target_field = psycopg_sql.SQL('{}.field_values') \
                        .format(psycopg_sql.Identifier(property_label + '_extended'))

                    # matching_fields.append(psycopg_sql.SQL('{target_field}.field_counts AS {field_name}').format(
                    #     target_field=psycopg_sql.Identifier(property_label + '_counts'),
                    #     field_name=psycopg_sql.Identifier(property_label + '_count')
                    # ))

                    joins.append(psycopg_sql.SQL(cleandoc('''
                        LEFT JOIN (
                            SELECT uri, ARRAY(	                            
                                SELECT DISTINCT x
                                FROM unnest({fields}) AS x
                                WHERE x IS NOT NULL
                            ) AS field_values
                            FROM {res}
                            GROUP BY uri
                        ) AS {field_name}
                        ON {field_name}.uri = target.uri                    
                    ''')).format(
                        res=psycopg_sql.Identifier(ets_internal_id),
                        fields=psycopg_sql.SQL(' || ').join(
                            [psycopg_sql.SQL('array_agg({})').format(psycopg_sql.Identifier(prop.hash))
                             for prop in ets_method_properties]
                        ),
                        # field_name=psycopg_sql.Identifier(property_label + '_counts')
                        field_name=psycopg_sql.Identifier(property_label + '_extended')
                    ))

                    # joins.append(psycopg_sql.SQL(cleandoc('''
                    #     LEFT JOIN (
                    #         SELECT uri, (
                    #             SELECT count(DISTINCT x)
                    #             FROM unnest({fields}) AS x
                    #             WHERE x IS NOT NULL
                    #         ) AS field_counts
                    #         FROM {res}
                    #         GROUP BY uri
                    #     ) AS {field_name}
                    #     ON {field_name}.uri = target.uri
                    # ''')).format(
                    #     res=psycopg_sql.Identifier(ets_internal_id),
                    #     fields=psycopg_sql.SQL(' || ').join(
                    #         [psycopg_sql.SQL('array_agg({})').format(psycopg_sql.Identifier(prop.hash))
                    #          for prop in ets_method_properties]
                    #     ),
                    #     field_name=psycopg_sql.Identifier(property_label + '_counts')
                    # ))
                else:
                    # If the same combination of fields was used for another matching function before, then add a join
                    target = 'target'
                    fields = [prop.hash for prop in ets_method_properties]
                    if any(all(elem in fields for elem in prev_field) for prev_field in prev_fields):
                        target = hash_string_min(property_label)
                        joins.append(
                            psycopg_sql.SQL('JOIN {res} AS {join_name} ON target.uri = {join_name}.uri').format(
                                res=psycopg_sql.Identifier(ets_internal_id),
                                join_name=psycopg_sql.Identifier(target)
                            )
                        )

                    prev_fields.append(fields)
                    target_field = psycopg_sql.SQL('{target}.{property_field}').format(
                        target=psycopg_sql.Identifier(target),
                        property_field=psycopg_sql.Identifier(ets_method_properties[0].hash)
                    )

                    # In case of multiple properties, combine all values into a new field to use as a join
                    if len(ets_method_properties) > 1:
                        target_field = psycopg_sql.Identifier(property_label)

                        joins.append(psycopg_sql.SQL('CROSS JOIN unnest(ARRAY[{fields}]) AS {field_name}').format(
                            fields=psycopg_sql.SQL(', ').join(
                                [psycopg_sql.SQL('{target}.{property_field}').format(
                                    target=psycopg_sql.Identifier(target),
                                    property_field=psycopg_sql.Identifier(prop.hash)
                                ) for prop in ets_method_properties]
                            ),
                            field_name=psycopg_sql.Identifier(property_label)
                        ))

                matching_fields.append(psycopg_sql.SQL('{target_field} AS {field_name}').format(
                    target_field=target_field,
                    field_name=psycopg_sql.Identifier(property_label)
                ))

                if matching_func.list_threshold:
                    props_not_null.append(psycopg_sql.SQL('cardinality({}) > 0').format(target_field))
                else:
                    props_not_null.append(psycopg_sql.SQL('{} IS NOT NULL').format(target_field))

                if matching_func.method_name == 'INTERMEDIATE':
                    for intermediate_ets, intermediate_ets_props in matching_func.intermediates.items():
                        target = hash_string_min(intermediate_ets)
                        intermediate_field = intermediate_ets_props['source'] \
                            if is_source else intermediate_ets_props['target']

                        joins.append(
                            psycopg_sql.SQL('''
                                LEFT JOIN {ets} AS {join_name} 
                                ON {target_field} = {join_name}.{intermediate_field}
                            ''').format(
                                ets=psycopg_sql.Identifier(intermediate_ets),
                                join_name=psycopg_sql.Identifier(target),
                                target_field=target_field,
                                intermediate_field=psycopg_sql.Identifier(intermediate_field.hash)
                            )
                        )

                        matching_fields.append(psycopg_sql.SQL('{join_name}.uri AS {field_name}').format(
                            join_name=psycopg_sql.Identifier(target),
                            field_name=psycopg_sql.Identifier(property_label + '_intermediate')
                        ))

            sql.append(
                psycopg_sql.SQL(cleandoc(
                    """SELECT DISTINCT {collection} AS collection, target.uri, 
                                       {matching_fields}
                       FROM {res} AS target
                       {joins}
                       WHERE {props_not_null}"""
                )).format(
                    collection=psycopg_sql.Literal(ets_internal_id),
                    matching_fields=psycopg_sql.SQL(',\n                ').join(matching_fields),
                    res=psycopg_sql.Identifier(ets_internal_id),
                    joins=psycopg_sql.SQL('\n').join(joins),
                    props_not_null=psycopg_sql.SQL('\n  OR ').join(props_not_null),
                )
            )

        return psycopg_sql.SQL('\nUNION ALL\n').join(sql)
