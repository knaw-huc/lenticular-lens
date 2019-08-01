import os

CLUSTER_SERIALISATION_DIR = os.path.join(os.environ['DATA_DIR'], 'Serialisation') \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(CLUSTER_SERIALISATION_DIR):
    os.mkdir(CLUSTER_SERIALISATION_DIR)
