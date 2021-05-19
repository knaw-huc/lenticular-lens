from psycopg2 import sql
from inspect import cleandoc

from ll.util.config_db import db_conn
from ll.elem.matching_method import MatchingMethod


def temp_update(job, type, id):
    spec = job.get_spec_by_id(id, type)
    sim_fields_sqls = MatchingMethod.get_similarity_fields_sqls(spec.matching_methods)

    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql.SQL(cleandoc(
            """ DROP INDEX IF EXISTS {schema}.{cluster_idx};
            
                ALTER TABLE {schema}.{table}
                ALTER COLUMN cluster_id TYPE integer USING NULL;
                
                ALTER TABLE {schema}.{table}
                RENAME COLUMN similarity TO similarities;
                
                ALTER TABLE {schema}.{table}
                ADD COLUMN similarity numeric NULL;
    
                UPDATE {schema}.{table}
                SET similarity = (
                    SELECT similarity
                    FROM (VALUES (similarities)) AS similarities
                    {sim_fields_sql}
                    CROSS JOIN LATERAL coalesce({sim_logic_ops_sql}, 1) AS similarity
                );
    
                CREATE INDEX ON {schema}.{table} USING btree (cluster_id);
                CREATE INDEX ON {schema}.{table} USING btree (similarity);
    
                ANALYZE {schema}.{table};
            """
        )).format(
            cluster_idx=sql.Identifier(job.table_name(spec.id) + '_cluster_id_idx'),
            schema=sql.Identifier('linksets' if type == 'linkset' else 'lenses'),
            table=sql.Identifier(job.table_name(spec.id)),
            sim_fields_sql=sql.SQL('\n').join(sim_fields_sqls),
            sim_logic_ops_sql=spec.similarity_logic_ops_sql
        ))
