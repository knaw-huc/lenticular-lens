import os

CLUSTER_VISUALISATION_DIR = os.path.join(os.environ['DATA_DIR'], 'Validation') \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(CLUSTER_VISUALISATION_DIR):
    os.mkdir(CLUSTER_VISUALISATION_DIR)
