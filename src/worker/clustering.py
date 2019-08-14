from os.path import join

from common.helpers import hasher
from common.config_db import db_conn

import common.ll.Clustering.SimpleLinkClustering as Cls
from common.ll.Clustering.SimpleLinkClustering import simple_csv_link_clustering

from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from common.ll.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR


def start_clustering(job_id, alignment, association_file, clustering_id):
    filename = f'alignment_{hasher(job_id)}_alignment_{alignment}.csv.gz'
    csv_filepath = join(CSV_ALIGNMENTS_DIR, filename)

    if clustering_id and association_file:
        reconciliation_result = cluster_reconciliation_csv(association_file, job_id, alignment)

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('''
            UPDATE clusterings
            SET extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
            WHERE job_id = %s AND alignment = %s
            ''', (reconciliation_result['extended_clusters_count'], reconciliation_result['cycles_count'], 'Finished',
                  job_id, alignment))
    elif not clustering_id and association_file:
        clustering_result = cluster_csv(csv_filepath, job_id, alignment)
        reconciliation_result = cluster_reconciliation_csv(association_file, job_id, alignment)

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('''
            UPDATE clusterings
            SET clustering_id = %s, clusters_count = %s, 
                extended_count = %s, cycles_count = %s, status = %s, finished_at = now()
            WHERE job_id = %s AND alignment = %s
            ''', (clustering_result['file_name'], clustering_result['clusters_count'],
                  reconciliation_result['extended_clusters_count'], reconciliation_result['cycles_count'], 'Finished',
                  job_id, alignment))
    else:
        clustering_result = cluster_csv(csv_filepath, job_id, alignment)

        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('''
            UPDATE clusterings
            SET clustering_id = %s, clusters_count = %s, status = %s, finished_at = now()
            WHERE job_id = %s AND alignment = %s
            ''', (clustering_result['file_name'], clustering_result['clusters_count'], 'Finished',
                  job_id, alignment))


def cluster_csv(csv_filepath, job_id, mapping_label):
    filename = f'Cluster_{hasher(job_id)}_{mapping_label}'
    return simple_csv_link_clustering(csv_filepath, CLUSTER_SERIALISATION_DIR, file_name=filename, activated=True)


def cluster_reconciliation_csv(related_filename, job_id, mapping_label):
    filename = f'Reconciled_{hasher(job_id)}_{mapping_label}_{hasher(related_filename)}'
    serialised = f'Cluster_{hasher(job_id)}_{mapping_label}'
    return Cls.extend_cluster(
        serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=serialised,
        csv_association_file=join(CSV_ASSOCIATIONS_DIR, related_filename), save_in=CLUSTER_SERIALISATION_DIR,
        reconciled_name=filename, condition_30=True, activated=True)
