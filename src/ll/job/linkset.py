from inspect import cleandoc
from psycopg2 import sql as psycopg_sql

from ll.job.conditions import Conditions
from ll.util.helpers import get_sql_empty
from ll.util.hasher import hash_string_min


class Linkset:
    def __init__(self, data, job):
        self._data = data
        self._job = job
        self._conditions = None

    @property
    def id(self):
        return self._data['id']

    @property
    def threshold(self):
        return self._data['threshold']

    @property
    def is_association(self):
        return self._data.get('is_association', False)

    @property
    def properties(self):
        return self._data['properties']

    @property
    def entity_type_selections(self):
        return self.sources + self.targets + self.intermediates

    @property
    def conditions(self):
        if not self._conditions:
            methods = self._data['methods']
            self._conditions = Conditions(methods['conditions'], methods['type'], self._job)
        return self._conditions

    @property
    def similarity_fields(self):
        return self.conditions.similarity_fields

    @property
    def index_sql(self):
        return self.conditions.index_sql

    @property
    def conditions_sql(self):
        return self.conditions.conditions_sql

    @property
    def similarity_fields_agg_sql(self):
        return self.conditions.similarity_fields_agg_sql

    @property
    def similarity_logic_ops_sql(self):
        return self.conditions.similarity_logic_ops_sql

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
        return self.conditions.get_fields(keys, only_matching_fields)

    def _get_combined_entity_type_selections_sql(self, is_source=True):
        sql = []
        properties = self.get_fields(['sources'] if is_source else ['targets'])

        # Get the properties needed for the source or target per entity-type selection
        for ets_internal_id, ets_properties in properties.items():
            joins = []
            matching_fields = []
            props_not_null = []
            prev_fields = []
            prev_targets = {}

            # Then for get all properties from this entity-type selection required for a single matching function
            for property_label, ets_matching_func_props in ets_properties.items():
                matching_method = ets_matching_func_props['matching_method']
                ets_method_properties = ets_matching_func_props['properties']

                self._matching_methods_sql(ets_internal_id, matching_method, ets_method_properties, is_source, False,
                                           joins, matching_fields, props_not_null, prev_fields, prev_targets)
                self._matching_methods_sql(ets_internal_id, matching_method, ets_method_properties, is_source, True,
                                           joins, matching_fields, props_not_null, prev_fields, prev_targets)

            sql.append(
                psycopg_sql.SQL(cleandoc(
                    """ SELECT DISTINCT {collection} AS collection, target.uri, 
                                        {matching_fields}
                        FROM {res} AS target {joins}
                        WHERE {props_not_null}
                   """
                )).format(
                    collection=psycopg_sql.Literal(ets_internal_id),
                    matching_fields=psycopg_sql.SQL(',\n                ').join(matching_fields),
                    res=psycopg_sql.Identifier(ets_internal_id),
                    joins=get_sql_empty(psycopg_sql.SQL('\n').join(joins)),
                    props_not_null=psycopg_sql.SQL('\nOR ').join(props_not_null),
                )
            )

        return psycopg_sql.SQL('\nUNION ALL\n').join(sql)

    @staticmethod
    def _matching_methods_sql(ets_internal_id, matching_method, properties, is_source, is_normalized,
                              joins, matching_fields, props_not_null, prev_fields, prev_targets):
        field_name = matching_method.field_name
        if is_normalized:
            field_name += '_norm'

        props = [prop.prop_normalized if is_normalized else prop.prop_original
                 for prop in properties
                 if not is_normalized or prop.prop_normalized]
        if not props:
            return

        # In case of list matching, combine all values into a field
        if matching_method.list_threshold:
            target_field = psycopg_sql.SQL('{}.field_values') \
                .format(psycopg_sql.Identifier(field_name + '_extended'))

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
                     for prop in props]
                ),
                field_name=psycopg_sql.Identifier(field_name + '_extended')
            ))
        else:
            target = 'target' if not is_normalized else prev_targets[matching_method.field_name]

            # If the same combination of fields was used for another matching function before, then add a join
            if not is_normalized:
                fields = [prop.hash for prop in props]
                if any(all(elem in fields for elem in prev_field) for prev_field in prev_fields):
                    target = hash_string_min(field_name)
                    joins.append(
                        psycopg_sql.SQL('JOIN {res} AS {join_name} ON target.uri = {join_name}.uri').format(
                            res=psycopg_sql.Identifier(ets_internal_id),
                            join_name=psycopg_sql.Identifier(target)
                        )
                    )

                prev_fields.append(fields)
                prev_targets[field_name] = target

            # Default case: if we have just one property, just select that property field from the target
            target_field = psycopg_sql.SQL('{target}.{property_field}').format(
                target=psycopg_sql.Identifier(target),
                property_field=psycopg_sql.Identifier(props[0].hash)
            )

            # In case of multiple props, combine all values into a new field to use as a join
            if len(props) > 1:
                target_field = psycopg_sql.Identifier(field_name)

                joins.append(psycopg_sql.SQL('CROSS JOIN unnest(ARRAY[{fields}]) AS {field_name}').format(
                    fields=psycopg_sql.SQL(', ').join(
                        [psycopg_sql.SQL('{target}.{property_field}').format(
                            target=psycopg_sql.Identifier(target),
                            property_field=psycopg_sql.Identifier(prop.hash)
                        ) for prop in props]
                    ),
                    field_name=psycopg_sql.Identifier(field_name)
                ))

        # Now that we have determined the target field, add it to the list of matching fields
        matching_fields.append(psycopg_sql.SQL('{target_field} AS {field_name}').format(
            target_field=target_field,
            field_name=psycopg_sql.Identifier(field_name)
        ))

        # Add is not null or is not empty check
        if matching_method.list_threshold:
            props_not_null.append(psycopg_sql.SQL('cardinality({}) > 0').format(target_field))
        else:
            props_not_null.append(psycopg_sql.SQL('{} IS NOT NULL').format(target_field))

        # Add properties to do the intermediate dataset matching
        if matching_method.method_name == 'INTERMEDIATE':
            for intermediate_ets, intermediate_ets_props in matching_method.intermediates.items():
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
                    field_name=psycopg_sql.Identifier(field_name + '_intermediate')
                ))
