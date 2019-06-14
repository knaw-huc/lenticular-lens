import os

CSV_ASSOCIATIONS_DIR = os.path.join(os.environ['DATA_DIR'], 'CSV_Associations') \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(CSV_ASSOCIATIONS_DIR):
    os.mkdir(CSV_ASSOCIATIONS_DIR)
