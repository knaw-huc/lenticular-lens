from common.config_db import db_conn
from common.helpers import hash_string
from os.path import join
import pickle
from psycopg2 import sql as psycopg2_sql


def get_cluster_data(clustering_id, cluster_id):
    print('Reading file')
    from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
    with open(join(CLUSTER_SERIALISATION_DIR, f'{clustering_id}-1.txt'), 'rb') as clusters_file:
        clusters_data = pickle.load(clusters_file)

    return clusters_data[cluster_id]


def linkset_to_csv(job_id, mapping_label):
    from common.ll.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
    filepath = join(CSV_ALIGNMENTS_DIR, f'{job_id}_{mapping_label}.csv')

    sql = psycopg2_sql.SQL(
        "COPY (SELECT source_uri, target_uri, 1 FROM {schema}.{view}) TO STDOUT WITH CSV DELIMITER ','").format(
        schema=psycopg2_sql.Identifier(f'job_{job_id}'),
        view=psycopg2_sql.Identifier(hash_string(mapping_label)),
    )

    with db_conn() as conn, conn.cursor() as cur:
        with open(filepath, 'w') as csv_file:
            cur.copy_expert(sql, csv_file)

    return filepath
