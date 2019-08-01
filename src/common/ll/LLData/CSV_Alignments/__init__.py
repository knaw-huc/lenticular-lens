import os

CSV_ALIGNMENTS_DIR = os.path.join(os.environ['DATA_DIR'], 'CSV_Alignments') \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

if not os.path.exists(CSV_ALIGNMENTS_DIR):
    os.mkdir(CSV_ALIGNMENTS_DIR)
