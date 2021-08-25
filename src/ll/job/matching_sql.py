import locale

from psycopg2 import sql
from inspect import cleandoc

from ll.job.joins import Joins
from ll.elem.matching_method import MatchingMethod

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
        for entity_type_selection in self._linkset.all_entity_type_selections:
            random = '\nORDER BY RANDOM()' if entity_type_selection.random else ''
            limit = sql.SQL(') AS x%s\nLIMIT %i' % (random, entity_type_selection.limit)) \
                if entity_type_selection.limit > -1 else sql.SQL('')

            prepare_sqls = []
            matching_fields_sqls = [sql.SQL('{}.uri').format(sql.Identifier(entity_type_selection.alias))]

            matching_methods_props = entity_type_selection.get_fields(self._linkset)
            for matching_method_prop in matching_methods_props:
                if matching_method_prop.prepare_sql:
                    prepare_sqls.append(matching_method_prop.prepare_sql)

            for property_field in \
                    {mm_prop.prop_original for mm_prop in matching_methods_props}.union(
                        {mm_prop.prop_normalized for mm_prop in matching_methods_props if mm_prop.prop_normalized}):
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
                table_name=sql.Identifier(entity_type_selection.collection.table_name),
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
                
                CREATE INDEX ON source USING hash (uri);
                ANALYZE source;
            """
        ) + '\n').format(
            self._get_combined_entity_type_selections_sql(self._linkset.get_fields(['sources']), is_source=True))

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
                CREATE MATERIALIZED VIEW target AS 
                {};
                
                CREATE INDEX ON target USING hash (uri);
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
        similarities_sqls, source_intermediates_sqls, target_intermediates_sqls = [], [], []
        for matching_method in self._linkset.matching_methods:
            field_name = matching_method.field_name
            if matching_method.similarity_sql:
                similarities_sqls.append(sql.SQL('{}, {}')
                                         .format(sql.Literal(field_name), matching_method.similarity_sql))

            if matching_method.is_intermediate:
                source_intermediates_sqls \
                    .append(sql.SQL('{}, array_agg(DISTINCT source.{})')
                            .format(sql.Literal(field_name), sql.Identifier(field_name + '_intermediate')))
                target_intermediates_sqls \
                    .append(sql.SQL('{}, array_agg(DISTINCT target.{})')
                            .format(sql.Literal(field_name), sql.Identifier(field_name + '_intermediate')))

        conditions_sql = self._linkset.with_matching_methods_recursive(
            lambda sqls, operator, fuzzy, threshold: sql.SQL('({})').format(sql.SQL('\n%s ' % operator).join(sqls)),
            lambda matching_method: matching_method.sql
        )

        if self._linkset.use_counter:
            conditions_sql = sql.Composed([conditions_sql, sql.SQL("\nAND increment_counter('linkset_count')")])

        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS linkset CASCADE;
                CREATE MATERIALIZED VIEW linkset AS 
                SELECT CASE WHEN source.uri < target.uri THEN source.uri ELSE target.uri END AS source_uri,
                       CASE WHEN source.uri < target.uri THEN target.uri ELSE source.uri END AS target_uri,
                       CASE WHEN every(source.uri < target.uri) THEN 'source_target'::link_order
                            WHEN every(target.uri < source.uri) THEN 'target_source'::link_order
                            ELSE 'both'::link_order END AS link_order,
                       array_agg(DISTINCT source.collection) AS source_collections,
                       array_agg(DISTINCT target.collection) AS target_collections,
                       {source_intermediates} AS source_intermediates,
                       {target_intermediates} AS target_intermediates,
                       {similarities} AS similarities
                FROM source
                JOIN target ON source.uri != target.uri
                AND {conditions}
                GROUP BY source_uri, target_uri;
            """
        ) + '\n').format(
            linkset=sql.Identifier(self._job.table_name(self._linkset.id)),
            source_intermediates=sql.SQL('jsonb_build_object({})').format(sql.SQL(', ').join(source_intermediates_sqls)) \
                if source_intermediates_sqls else sql.SQL('NULL::jsonb'),
            target_intermediates=sql.SQL('jsonb_build_object({})').format(sql.SQL(', ').join(target_intermediates_sqls)) \
                if target_intermediates_sqls else sql.SQL('NULL::jsonb'),
            similarities=sql.SQL('jsonb_build_object({})').format(sql.SQL(', ').join(similarities_sqls)) \
                if similarities_sqls else sql.SQL('NULL::jsonb'),
            conditions=conditions_sql
        )

    def generate_match_linkset_finish_sql(self):
        sim_fields_sqls = MatchingMethod.get_similarity_fields_sqls(self._linkset.matching_methods)

        sim_matching_methods_conditions_sqls = [match_method.similarity_threshold_sql
                                                for match_method in self._linkset.matching_methods
                                                if match_method.similarity_threshold_sql]

        sim_grouping_conditions_sqls = [sql.SQL('{similarity} >= {threshold}').format(
            similarity=similarity,
            threshold=sql.Literal(threshold)
        ) for (threshold, similarity) in self._linkset.similarity_logic_ops_sql_per_threshold]

        sim_condition_sql = get_sql_empty(sql.Composed([
            sql.SQL('WHERE '), sql.SQL(' AND ')
                .join(sim_matching_methods_conditions_sqls + sim_grouping_conditions_sqls)]),
            flag=sim_matching_methods_conditions_sqls or sim_grouping_conditions_sqls)

        return sql.SQL(cleandoc(
            """ DROP TABLE IF EXISTS linksets.{linkset} CASCADE;
                CREATE TABLE linksets.{linkset} AS
                SELECT linkset.*, similarity
                FROM linkset
                {sim_fields_sql}
                CROSS JOIN LATERAL coalesce({sim_logic_ops_sql}, 1) AS similarity 
                {sim_condition_sql};
                
                ALTER TABLE linksets.{linkset}
                ADD PRIMARY KEY (source_uri, target_uri),
                ADD COLUMN cluster_id integer,
                ADD COLUMN cluster_hash_id char(15),
                ADD COLUMN valid link_validity DEFAULT 'unchecked' NOT NULL,
                ADD COLUMN motivation text;

                ALTER TABLE linksets.{linkset} ADD COLUMN sort_order serial;

                CREATE INDEX ON linksets.{linkset} USING hash (source_uri);
                CREATE INDEX ON linksets.{linkset} USING hash (target_uri);
                CREATE INDEX ON linksets.{linkset} USING hash (valid);

                CREATE INDEX ON linksets.{linkset} USING btree (cluster_id);
                CREATE INDEX ON linksets.{linkset} USING btree (similarity);
                CREATE INDEX ON linksets.{linkset} USING btree (sort_order);

                ANALYZE linksets.{linkset};
            """
        ) + '\n').format(
            linkset=sql.Identifier(self._job.table_name(self._linkset.id)),
            sim_fields_sql=sql.SQL('\n').join(sim_fields_sqls),
            sim_logic_ops_sql=self._linkset.similarity_logic_ops_sql,
            sim_condition_sql=sim_condition_sql
        )

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
            joins, matching_fields = [], []

            # Then for get all properties from this entity-type selection required for a single matching function
            for ets_index, (property_label, ets_matching_func_props) in enumerate(ets_properties.items()):
                matching_method = ets_matching_func_props['matching_method']
                ets_method_properties = ets_matching_func_props['properties']

                MatchingSql._matching_methods_sql(ets_id, matching_method, ets_method_properties,
                                                  is_source, joins, matching_fields, ets_index)

            sqls.append(
                sql.SQL(cleandoc(""" 
                    SELECT {collection} AS collection, target.uri, 
                           {matching_fields}
                    FROM (SELECT DISTINCT uri FROM {res}) AS target {joins}
               """)).format(
                    collection=sql.Literal(int(ets_id)),
                    matching_fields=sql.SQL(',\n       ').join(matching_fields),
                    res=sql.Identifier(hash_string_min(ets_id)),
                    joins=get_sql_empty(sql.SQL('\n').join(joins)),
                )
            )

        return sql.SQL('\nUNION ALL\n').join(sqls)

    @staticmethod
    def _matching_methods_sql(ets_id, matching_method, properties, is_source, joins, matching_fields, ets_index):
        target = 'target' + str(ets_index)

        field_name_org = matching_method.field_name
        field_name_norm = field_name_org + '_norm'

        props_org = [prop.prop_original for prop in properties]
        props_norm = [prop.prop_normalized for prop in properties if prop.prop_normalized]

        # In case of list matching, combine all values into a field
        if matching_method.is_list_match:
            field_norm = sql.SQL('')
            if props_norm:
                field_norm = sql.SQL(cleandoc('''
                     , ARRAY(
                        SELECT {field_name_norm}
                        FROM unnest({fields_org}, {fields_norm}) AS x ({field_name_org}, {field_name_norm})
                        WHERE {field_name_org} IS NOT NULL
                        GROUP BY {field_name_org}, {field_name_norm}
                    ) AS {field_name_norm}
                ''')).format(
                    field_name_org=sql.Identifier(field_name_org),
                    field_name_norm=sql.Identifier(field_name_norm),
                    fields_org=sql.SQL(' || ').join([
                        sql.SQL('array_agg({})').format(sql.Identifier(prop.hash)) for prop in props_org]),
                    fields_norm=sql.SQL(' || ').join([
                        sql.SQL('array_agg({})').format(sql.Identifier(prop.hash)) for prop in props_norm]),
                )

            joins.append(sql.SQL(cleandoc('''
                LEFT JOIN (
                    SELECT uri, ARRAY(
                        SELECT {field_name_org}
                        FROM unnest({fields_org}) AS {field_name_org}
                        WHERE {field_name_org} IS NOT NULL
                        GROUP BY {field_name_org}
                    ) AS {field_name_org} {field_norm}
                    FROM {res}
                    GROUP BY uri
                ) AS {target}
                ON target.uri = {target}.uri
            ''')).format(
                fields_org=sql.SQL(' || ').join([
                    sql.SQL('array_agg({})').format(sql.Identifier(prop.hash)) for prop in props_org]),
                field_name_org=sql.Identifier(field_name_org),
                field_norm=field_norm,
                res=sql.Identifier(hash_string_min(ets_id)),
                target=sql.Identifier(target)
            ))
        # Otherwise combine all values into a new field to use as a join
        else:
            if len(props_org) == 1:
                field_template = '{field_org} AS {field_name_org}'
                if props_norm:
                    field_template += ', {field_norm} AS {field_name_norm}'

                fields_sql = sql.SQL(field_template).format(
                    field_org=sql.Identifier(props_org[0].hash),
                    field_name_org=sql.Identifier(field_name_org),
                    field_norm=sql.Identifier(props_norm[0].hash) if props_norm else sql.SQL(''),
                    field_name_norm=sql.Identifier(field_name_norm) if props_norm else sql.SQL(''),
                )

                lateral_sql = sql.SQL('')
            else:
                field_template = '{field_name_org}' if not props_norm else '{field_name_org}, {field_name_norm}'

                fields_sql = sql.SQL(field_template).format(
                    field_name_org=sql.Identifier(field_name_org),
                    field_name_norm=sql.Identifier(field_name_norm) if props_norm else sql.SQL(''),
                )

                join_template = ', LATERAL unnest(ARRAY[{fields_org}]) AS {field_name_org}' if not props_norm else \
                    ', LATERAL unnest(ARRAY[{fields_org}], ARRAY[{fields_norm}]) AS x ({field_name_org}, {field_name_norm})'

                lateral_sql = sql.SQL(join_template).format(
                    fields_org=sql.SQL(', ').join([sql.Identifier(prop.hash) for prop in props_org]),
                    field_name_org=sql.Identifier(field_name_org),
                    fields_norm=sql.SQL(', ').join(
                        [sql.Identifier(prop.hash) for prop in props_norm]) if props_norm else sql.SQL(''),
                    field_name_norm=sql.Identifier(field_name_norm) if props_norm else sql.SQL(''),
                )

            joins.append(sql.SQL(cleandoc('''
                LEFT JOIN (
                    SELECT DISTINCT uri, {fields}
                    FROM {res}{lateral}
                ) AS {target}
                ON target.uri = {target}.uri AND {target}.{field_name_org} IS NOT NULL
            ''')).format(
                fields=fields_sql,
                res=sql.Identifier(hash_string_min(ets_id)),
                lateral=lateral_sql,
                target=sql.Identifier(target),
                field_name_org=sql.Identifier(field_name_org),
            ))

        # Now that we have determined the target fields, add them to the list of matching fields
        matching_fields.append(sql.SQL('{target}.{field} AS {field}').format(
            target=sql.Identifier(target), field=sql.Identifier(field_name_org)))
        if props_norm:
            matching_fields.append(sql.SQL('{target}.{field} AS {field}').format(
                target=sql.Identifier(target), field=sql.Identifier(field_name_norm)))

        # Add properties to do the intermediate dataset matching
        if matching_method.is_intermediate:
            for intermediate_ets, intermediate_ets_props in matching_method.intermediates.items():
                intermediate_res = hash_string_min(intermediate_ets)
                intermediate_target = 'intermediate' + str(ets_index)
                intermediate_fields = intermediate_ets_props['source' if is_source else 'target']

                intermediate_match_sqls = [
                    sql.SQL('{target}.{field_name} = {intermediate_target}.{intermediate_field}').format(
                        target=sql.Identifier(target),
                        field_name=sql.Identifier(field_name_org),
                        intermediate_target=sql.Identifier(intermediate_target),
                        intermediate_field=sql.Identifier(intermediate_field.prop_original.hash)
                    )
                    for intermediate_field in intermediate_fields
                ]

                joins.append(
                    sql.SQL(cleandoc('''
                        LEFT JOIN {intermediate_res} AS {intermediate_target}
                        ON {match_sqls}
                    ''')).format(
                        intermediate_res=sql.Identifier(intermediate_res),
                        intermediate_target=sql.Identifier(intermediate_target),
                        match_sqls=sql.SQL(' OR ').join(intermediate_match_sqls)
                    )
                )

                matching_fields.append(sql.SQL('{join_name}.uri AS {field_name}').format(
                    join_name=sql.Identifier(intermediate_target),
                    field_name=sql.Identifier(field_name_org + '_intermediate')
                ))
