import os

CSV_CLUSTER_DIR = os.path.join(os.environ['DATA_DIR'], 'CSV_Clusters') \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(CSV_CLUSTER_DIR):
    os.mkdir(CSV_CLUSTER_DIR)
