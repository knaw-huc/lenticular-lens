from config_db import db_conn
from helpers import file_date, hash_string
from os.path import join
import pickle
from psycopg2 import sql as psycopg2_sql
from src.Clustering.SimpleLinkClustering import simple_csv_link_clustering
import src.Clustering.SimpleLinkClustering as Cls
from src.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from src.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
from src.Generic.Utility import hasher


def get_cluster_data(clustering_id, cluster_id):
    print('Reading file')
    from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
    with open(join(CLUSTER_SERIALISATION_DIR, f'{clustering_id}-1.txt'), 'rb') as clusters_file:
        clusters_data = pickle.load(clusters_file)

    return clusters_data[cluster_id]


def cluster_csv(csv_filepath, job_id, mapping_label):
    # csv_filepath = join(CSV_ALIGNMENTS_DIR, "GA-linkset-paper.csv")

    filename = f'Cluster_{hasher(job_id)}_{mapping_label}'
    # filename = '__PHDemoClusters__'

    return simple_csv_link_clustering(csv_filepath, CLUSTER_SERIALISATION_DIR, file_name=filename, activated=True)


def cluster_reconciliation_csv(related_filename, job_id, mapping_label):

    filename = f'Reconciled_{hasher(job_id)}_{mapping_label}_{hasher(related_filename)}'
    # filename = '__PHDemoClustersReconciled__'
    serialised = f'Cluster_{hasher(job_id)}_{mapping_label}'
    # serialised = '__PHDemoClusters__'
    return Cls.extend_cluster(
        serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
        csv_association_file=join(CSV_ASSOCIATIONS_DIR, related_filename), save_in=CLUSTER_SERIALISATION_DIR,
        reconciled_name=filename, condition_30=True, activated=True)


def cluster_and_reconcile(csv_filepath, job_id, mapping_label, related_filename):
    cluster_csv(csv_filepath, job_id, mapping_label)
    cluster_reconciliation_csv(related_filename, job_id, mapping_label)


def linkset_to_csv(job_id, mapping_label):
    from src.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
    filepath = join(CSV_ALIGNMENTS_DIR, f'{job_id}_{mapping_label}.csv')

    sql = psycopg2_sql.SQL("COPY (SELECT source_uri, target_uri, 1 FROM {schema}.{view}) TO STDOUT WITH CSV DELIMITER ','").format(
        schema=psycopg2_sql.Identifier(f'job_{job_id}'),
        view=psycopg2_sql.Identifier(hash_string(mapping_label)),
    )

    with db_conn() as conn, conn.cursor() as cur:
        with open(filepath, 'w') as csv_file:
            cur.copy_expert(sql, csv_file)

    return filepath
