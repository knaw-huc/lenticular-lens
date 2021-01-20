import locale

from psycopg2 import sql
from inspect import cleandoc
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
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
        ])

    def generate_entity_type_selection_sql(self):
        entity_type_selections_sql = []
        for entity_type_selection in self._job.entity_type_selections_required_for_linkset(self._linkset.id):
            entity_type_selections_sql.append(sql.SQL(cleandoc(
                """ DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
                    CREATE MATERIALIZED VIEW {view_name} AS
                    {pre}SELECT DISTINCT {matching_fields}
                    FROM timbuctoo.{table_name} AS {view_name}{joins}{wheres}{limit};
                    
                    ANALYZE {view_name};
                """
            ) + '\n').format(
                pre=sql.SQL('SELECT * FROM (') if entity_type_selection.limit > -1 else sql.SQL(''),
                view_name=sql.Identifier(entity_type_selection.internal_id),
                matching_fields=entity_type_selection.matching_fields_sql(self._linkset),
                table_name=sql.Identifier(entity_type_selection.table_name),
                joins=get_sql_empty(entity_type_selection.joins(self._linkset).sql),
                wheres=get_sql_empty(entity_type_selection.where_sql),
                limit=get_sql_empty(entity_type_selection.limit_sql),
            ))

        return sql.Composed(entity_type_selections_sql)

    def generate_match_source_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS source CASCADE;
                CREATE MATERIALIZED VIEW source AS 
                {};
                
                CREATE INDEX ON source (uri);
                ANALYZE source;
            """
        ) + '\n').format(self._linkset.source_sql)

    def generate_match_target_sql(self):
        return sql.SQL(cleandoc(
            """ DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
                CREATE MATERIALIZED VIEW target AS 
                {};
                
                CREATE INDEX ON target (uri);
                ANALYZE target;
            """
        ) + '\n').format(self._linkset.target_sql)

    def generate_match_index_and_sequence_sql(self):
        sequence_sql = sql.SQL(cleandoc(
            """ DROP SEQUENCE IF EXISTS linkset_count CASCADE;
                CREATE SEQUENCE linkset_count MINVALUE 1;
            """) + '\n')

        if self._linkset.index_sql:
            return sql.SQL('\n').join([self._linkset.index_sql, sequence_sql])

        return sequence_sql

    def generate_match_linkset_sql(self):
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
                JOIN target ON (source.uri != target.uri)
                AND {conditions}
                AND increment_counter('linkset_count')
                GROUP BY source_uri, target_uri
            """
        )).format(
            similarities=self._linkset.similarity_fields_agg_sql,
            conditions=self._linkset.conditions_sql
        )

        if self._linkset.similarity_fields and (self._linkset.threshold or self._linkset.similarity_threshold_sqls):
            sim_fields_sql = [sql.SQL('{} numeric[]').format(sql.Identifier(sim_field))
                              for sim_field in self._linkset.similarity_fields]

            sim_conditions = self._linkset.similarity_threshold_sqls
            if self._linkset.threshold:
                sim_conditions.append(sql.SQL('{sim_logic_ops_sql} >= {threshold}').format(
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
                sim_fields_sql=sql.SQL(', ').join(sim_fields_sql),
                sim_conditions=sql.SQL(' AND ').join(sim_conditions)
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
