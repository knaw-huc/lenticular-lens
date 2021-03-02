import locale

from psycopg2 import sql
from inspect import cleandoc

from ll.job.joins import Joins
from ll.util.hasher import hash_string_min
from ll.util.helpers import get_string_from_sql, get_sql_empty

locale.setlocale(locale.LC_ALL, '')


class MatchingSql:
    def __init__(self, job, id):
        self._job = job
        self._linkset = job.get_linkset_spec_by_id(id)

    def generate_schema_sql(self):
        schema_name_sql = sql.Identifier(self._job.schema_name(self._linkset.id))

        return sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET search_path TO "$user", {}, public;\n').format(schema_name_sql),
        ])

    def generate_entity_type_selection_sql(self):
        entity_type_selections_sql = []
        for entity_type_selection in self._linkset.entity_type_selections:
            random = '\nORDER BY RANDOM()' if entity_type_selection.random else ''
            limit = sql.SQL(') AS x%s\nLIMIT %i' % (random, entity_type_selection.limit)) \
                if entity_type_selection.limit > -1 else sql.SQL('')

            prepare_sqls = []
            matching_fields_sqls = [sql.SQL('{}.uri').format(sql.Identifier(entity_type_selection.alias))]

            for matching_method_prop in entity_type_selection.get_fields(self._linkset):
                if matching_method_prop.prepare_sql:
                    prepare_sqls.append(matching_method_prop.prepare_sql)

                for property_field in [matching_method_prop.prop_original, matching_method_prop.prop_normalized]:
                    if property_field:
                        matching_fields_sqls.append(sql.SQL('{matching_field} AS {name}').format(
                            matching_field=property_field.sql,
                            name=sql.Identifier(property_field.hash)
                        ))

            joins = Joins()
            joins.set_joins_for_props(entity_type_selection.properties_for_matching(self._linkset))

            where_sql = entity_type_selection.filters_sql
            if where_sql:
                where_sql = sql.SQL('WHERE {}').format(where_sql)

            ets_sql = sql.SQL(cleandoc(
                """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
                    CREATE MATERIALIZED VIEW {view_name} AS
                    {pre}SELECT DISTINCT {matching_fields}
                    FROM timbuctoo.{table_name} AS {view_name}{joins}{wheres}{limit};
                    
                    ANALYZE {view_name};
                """
            ) + '\n').format(
                pre=sql.SQL('SELECT * FROM (') if entity_type_selection.limit > -1 else sql.SQL(''),
                view_name=sql.Identifier(entity_type_selection.alias),
                matching_fields=sql.SQL(',\n       ').join(matching_fields_sqls),
                table_name=sql.Identifier(entity_type_selection.table_name),
                joins=get_sql_empty(joins.sql),
                wheres=get_sql_empty(where_sql),
                limit=get_sql_empty(limit),
            )

            if prepare_sqls:
                ets_sql = sql.Composed([sql.SQL('\n').join(prepare_sqls), sql.SQL('\n'), ets_sql])

            entity_type_selections_sql.append(ets_sql)

        return sql.Composed(entity_type_selections_sql)

    def generate_match_source_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS source CASCADE;
                CREATE MATERIALIZED VIEW source AS 
                {};
                
                CREATE INDEX ON source (uri);
                ANALYZE source;
            """
        ) + '\n').format(
            self._get_combined_entity_type_selections_sql(self._linkset.get_fields(['sources']), is_source=True))

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
                CREATE MATERIALIZED VIEW target AS 
                {};
                
                CREATE INDEX ON target (uri);
                ANALYZE target;
            """
        ) + '\n').format(
            self._get_combined_entity_type_selections_sql(self._linkset.get_fields(['targets']), is_source=False))

    def generate_match_index_and_sequence_sql(self):
        sequence_sql = sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS linkset_count CASCADE;
                CREATE SEQUENCE linkset_count MINVALUE 1;
            """) + '\n')

        index_sqls = [matching_method.index_sql
                      for matching_method in self._linkset.matching_methods
                      if matching_method.index_sql]

        if index_sqls:
            return sql.SQL('\n').join([sql.SQL('\n').join(index_sqls), sequence_sql])

        return sequence_sql

    def generate_match_linkset_sql(self):
        fields_sqls = []
        fields_added = set()
        for matching_method in self._linkset.matching_methods:
            if matching_method.similarity_sql:
                name = matching_method.field_name

                # Add source and target values; if not done already
                if name not in fields_added:
                    fields_added.add(name)
                    fields_sqls.append(sql.SQL('{}, array_agg(DISTINCT {})')
                                       .format(sql.Literal(name), matching_method.similarity_sql))

        conditions_sql = self._linkset.with_matching_methods_recursive(
            lambda sqls, operator, fuzzy: sql.SQL('({})').format(sql.SQL('\n%s ' % operator).join(sqls)),
            lambda matching_method: matching_method.sql
        )

        if self._linkset.use_counter:
            conditions_sql = sql.Composed([conditions_sql, sql.SQL("\nAND increment_counter('linkset_count')")])

        linkset_sql = sql.SQL(cleandoc(
            """ SELECT CASE WHEN source.uri < target.uri THEN source.uri ELSE target.uri END AS source_uri,
                       CASE WHEN source.uri < target.uri THEN target.uri ELSE source.uri END AS target_uri,
                       CASE WHEN every(source.uri < target.uri) THEN 'source_target'::link_order
                            WHEN every(target.uri < source.uri) THEN 'target_source'::link_order
                            ELSE 'both'::link_order END AS link_order,
                       array_agg(DISTINCT source.collection) AS source_collections,
                       array_agg(DISTINCT target.collection) AS target_collections,
                       {similarities} AS similarity
                FROM source
                JOIN target ON source.uri != target.uri
                AND {conditions}
                GROUP BY source_uri, target_uri
            """
        )).format(
            similarities=sql.SQL('jsonb_build_object({})').format(sql.SQL(', ').join(fields_sqls)) \
                if fields_sqls else sql.SQL('NULL::jsonb'),
            conditions=conditions_sql
        )

        sim_conditions_sqls = [match_method.similarity_threshold_sql
                               for match_method in self._linkset.matching_methods
                               if match_method.similarity_threshold_sql]

        if self._linkset.similarity_fields and (self._linkset.threshold or sim_conditions_sqls):
            sim_fields_sqls = [sql.SQL('{} numeric[]').format(sql.Identifier(sim_field))
                               for sim_field in self._linkset.similarity_fields]

            if self._linkset.threshold:
                sim_conditions_sqls.append(sql.SQL('{sim_logic_ops_sql} >= {threshold}').format(
                    sim_logic_ops_sql=self._linkset.similarity_logic_ops_sql,
                    threshold=sql.Literal(self._linkset.threshold)
                ))

            return sql.SQL(cleandoc(
                """ DROP TABLE IF EXISTS linksets.{linkset} CASCADE;
                    CREATE TABLE linksets.{linkset} AS
                    SELECT linkset.*
                    FROM (
                        {linkset_sql}
                    ) AS linkset
                    CROSS JOIN LATERAL jsonb_to_record(similarity) 
                    AS sim({sim_fields_sql})
                    WHERE {sim_conditions};
                """
            ) + '\n').format(
                linkset=sql.Identifier(self._job.table_name(self._linkset.id)),
                linkset_sql=linkset_sql,
                sim_fields_sql=sql.SQL(', ').join(sim_fields_sqls),
                sim_conditions=sql.SQL(' AND ').join(sim_conditions_sqls)
            )

        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS linksets.{linkset} CASCADE;
                CREATE TABLE linksets.{linkset} AS
                {linkset_sql};
            """
        ) + '\n').format(
            linkset=sql.Identifier(self._job.table_name(self._linkset.id)),
            linkset_sql=linkset_sql
        )

    def generate_match_linkset_finish_sql(self):
        return sql.SQL(cleandoc(
            """ ALTER TABLE linksets.{linkset}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id text,
                ADD COLUMN valid link_validity DEFAULT 'not_validated';

                ALTER TABLE linksets.{linkset} ADD COLUMN sort_order serial;

                CREATE INDEX ON linksets.{linkset} USING hash (source_uri);
                CREATE INDEX ON linksets.{linkset} USING hash (target_uri);
                CREATE INDEX ON linksets.{linkset} USING hash (cluster_id);
                CREATE INDEX ON linksets.{linkset} USING hash (valid);
                CREATE INDEX ON linksets.{linkset} USING btree (sort_order);

                ANALYZE linksets.{linkset};
            """) + '\n').format(linkset=sql.Identifier(self._job.table_name(self._linkset.id)))

    @property
    def sql_string(self):
        sql_str = get_string_from_sql(self.generate_schema_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_entity_type_selection_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_match_source_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_match_target_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_match_index_and_sequence_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_sql())
        sql_str += '\n'
        sql_str += get_string_from_sql(self.generate_match_linkset_finish_sql())

        return sql_str

    @staticmethod
    def _get_combined_entity_type_selections_sql(properties, is_source):
        sqls = []

        # Get the properties needed for the source or target per entity-type selection
        for ets_id, ets_properties in properties.items():
            joins, matching_fields, props_not_null = [], [], []

            # Then for get all properties from this entity-type selection required for a single matching function
            for ets_index, (property_label, ets_matching_func_props) in enumerate(ets_properties.items()):
                matching_method = ets_matching_func_props['matching_method']
                ets_method_properties = ets_matching_func_props['properties']

                MatchingSql._matching_methods_sql(ets_id, matching_method, ets_method_properties,
                                                  is_source, joins, matching_fields, props_not_null, ets_index)

            sqls.append(
                sql.SQL(cleandoc(
                    """ SELECT DISTINCT {collection} AS collection, target.uri, 
                                        {matching_fields}
                        FROM {res} AS target {joins}
                        WHERE {props_not_null}
                   """
                )).format(
                    collection=sql.Literal(int(ets_id)),
                    matching_fields=sql.SQL(',\n                ').join(matching_fields),
                    res=sql.Identifier(hash_string_min(ets_id)),
                    joins=get_sql_empty(sql.SQL('\n').join(joins)),
                    props_not_null=sql.SQL('\nAND ').join(props_not_null),
                )
            )

        return sql.SQL('\nUNION ALL\n').join(sqls)

    @staticmethod
    def _matching_methods_sql(ets_id, matching_method, properties,
                              is_source, joins, matching_fields, props_not_null, ets_index):
        field_name_org = matching_method.field_name
        field_name_norm = field_name_org + '_norm'

        props_org = [prop.prop_original for prop in properties]
        props_norm = [prop.prop_normalized for prop in properties if prop.prop_normalized]

        for is_normalized in (False, True):
            field_name = field_name_norm if is_normalized else field_name_org
            props = props_norm if is_normalized else props_org

            if not props:
                break

            # In case of list matching, combine all values into a field
            if matching_method.is_list_match:
                target_field = sql.SQL('{}.field_values') \
                    .format(sql.Identifier(field_name + '_extended'))

                joins.append(sql.SQL(cleandoc('''
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
                    res=sql.Identifier(hash_string_min(ets_id)),
                    fields=sql.SQL(' || ').join(
                        [sql.SQL('array_agg({})').format(sql.Identifier(prop.hash))
                         for prop in props]
                    ),
                    field_name=sql.Identifier(field_name + '_extended')
                ))
            else:
                target = 'target'

                # Add a join for this particular field if it is not the first one (first one will be used as 'from')
                if ets_index > 0:
                    target += str(ets_index)

                    if not is_normalized:
                        joins.append(
                            sql.SQL('INNER JOIN {res} AS {join_name} ON target.uri = {join_name}.uri').format(
                                res=sql.Identifier(hash_string_min(ets_id)),
                                join_name=sql.Identifier(target)
                            )
                        )

                # Default case: if we have just one property, just select that property field from the target
                target_field = sql.SQL('{target}.{property_field}').format(
                    target=sql.Identifier(target),
                    property_field=sql.Identifier(props[0].hash)
                )

                # In case of multiple props, combine all values into a new field to use as a join
                if len(props) > 1:
                    target_field = sql.Identifier(field_name)

                    if not is_normalized:
                        if props_norm:
                            joins.append(
                                sql.SQL('CROSS JOIN unnest(ARRAY[{fields_org}], ARRAY[{fields_norm}]) \n'
                                        'AS {join_name}({field_name_org}, {field_name_norm})').format(
                                    fields_org=sql.SQL(', ').join(
                                        [sql.SQL('{target}.{property_field}').format(
                                            target=sql.Identifier(target),
                                            property_field=sql.Identifier(prop.hash)
                                        ) for prop in props_org]
                                    ),
                                    fields_norm=sql.SQL(', ').join(
                                        [sql.SQL('{target}.{property_field}').format(
                                            target=sql.Identifier(target),
                                            property_field=sql.Identifier(prop.hash)
                                        ) for prop in props_norm]
                                    ),
                                    join_name=sql.Identifier('join_' + target),
                                    field_name_org=sql.Identifier(field_name_org),
                                    field_name_norm=sql.Identifier(field_name_norm)
                                )
                            )
                        else:
                            joins.append(
                                sql.SQL('CROSS JOIN unnest(ARRAY[{fields_org}]) \n'
                                        'AS {field_name_org}').format(
                                    fields_org=sql.SQL(', ').join(
                                        [sql.SQL('{target}.{property_field}').format(
                                            target=sql.Identifier(target),
                                            property_field=sql.Identifier(prop.hash)
                                        ) for prop in props_org]
                                    ),
                                    field_name_org=sql.Identifier(field_name_org),
                                )
                            )

            if target_field:
                # Now that we have determined the target field, add it to the list of matching fields
                matching_fields.append(sql.SQL('{target_field} AS {field_name}').format(
                    target_field=target_field,
                    field_name=sql.Identifier(field_name)
                ))

                # Add is not null or is not empty check
                if matching_method.is_list_match:
                    props_not_null.append(sql.SQL('cardinality({}) > 0').format(target_field))
                else:
                    props_not_null.append(sql.SQL('{} IS NOT NULL').format(target_field))

                # Add properties to do the intermediate dataset matching
                if matching_method.method_name == 'INTERMEDIATE':
                    for intermediate_ets, intermediate_ets_props in matching_method.intermediates.items():
                        intermediate_res = hash_string_min(intermediate_ets)
                        intermediate_target = 'intermediate' + str(ets_index)
                        intermediate_field = intermediate_ets_props['source'].prop_original \
                            if is_source else intermediate_ets_props['target'].prop_original

                        joins.append(
                            sql.SQL(cleandoc('''
                                LEFT JOIN {intermediate_res} AS {intermediate_target}
                                ON {target_field} = {intermediate_target}.{intermediate_field}
                            ''')).format(
                                intermediate_res=sql.Identifier(intermediate_res),
                                intermediate_target=sql.Identifier(intermediate_target),
                                target_field=target_field,
                                intermediate_field=sql.Identifier(intermediate_field.hash)
                            )
                        )

                        matching_fields.append(sql.SQL('{join_name}.uri AS {field_name}').format(
                            join_name=sql.Identifier(intermediate_target),
                            field_name=sql.Identifier(field_name + '_intermediate')
                        ))
