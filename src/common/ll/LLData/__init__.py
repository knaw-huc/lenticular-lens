import os

DATA_DIR = os.path.join(os.environ['DATA_DIR']) \
    if 'DATA_DIR' in os.environ else os.path.dirname(os.path.realpath(__file__))

RDF_DIR = os.path.join(DATA_DIR, 'rdf')
if not os.path.exists(RDF_DIR):
    os.mkdir(RDF_DIR)

GENERATED_JSON_DIR = os.path.join(DATA_DIR, 'generated_json')
if not os.path.exists(GENERATED_JSON_DIR):
    os.mkdir(GENERATED_JSON_DIR)
