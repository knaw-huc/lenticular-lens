
#####################################################################################
""" DICTIONANY VARIABLES                                                         """
#####################################################################################


Stardog = "STARDOG"
Postgre = "POSTGRESQL"
Virtuoso = "VIRTUOSO"

data_store = "data_store"
database = "database"
stardog_uri = "stardog_uri"

split_sys = "split_sys"
data = "data"
rdf_predicate = "rdf_predicate"

# URI of the RESOURCE
entity = "entity"
entity_prefix = "entity_prefix"
entity_ns = 'entity_ns'
entity_name = "entity_name"
entity_type = 'entity_type'
entity_types = "entity_type"

# URI of any graph
graph = 'graph'
graph_prefix = "graph_prefix"
graph_ns = 'graph_ns'
graph_name = 'graph_name'

# AN ENRICHED GRAPH OF THE ORIGINAL GRAPH.
# THIS GRAPH CONTAINS THE NEW ENRICHED PROPERTIES
extended_graph = 'graph'
extended_graph_prefix = "graph_prefix"
extended_graph_ns = 'graph_ns'
extended_graph_name = 'graph_name'

# URI of the lens graph
lens = "lens"
lens_prefix = 'lens_prefix'
lens_ns = 'lens_ns'
lens_name = "lens_name"
lens_comment = "lens_comment"
lens_operation = "lens_operation"

# URU of the linkset graph
linkset = 'linkset'
linkset_prefix = 'linkset_prefix'
linkset_ns = 'linkset_ns'
linkset_name = 'linkset_name'
linkset_comment = 'linkset_comment'

longitude = "longitude"
longitude_prefix = 'longitude_prefix'
longitude_ns = 'longitude_ns'
longitude_name = 'longitude_name'

latitude = "latitude"
latitude_prefix = 'latitude_prefix'
latitude_ns = 'latitude_ns'
latitude_name = 'latitude_name'

# URI of the singleton graph
singleton = 'singleton'
assertion_method = 'assertion_method'
justification = 'justification'
justification_comment = 'justification_comment'

link = 'link'
link_prefix = "link_prefix"
link_ns = 'link_ns'
link_name = 'link_name'
link_comment = 'link_comment'
link_subpropertyof = 'link_subpropertyof'
link_old = 'link_old'
link_old_name = "link_old_name"
link_old_ns = "link_old_ns"

# URI of the aligned predicate
aligns = 'aligns'
aligns_prefix = 'aligns_prefix'
aligns_ns = 'aligns_ns'
aligns_name = 'aligns_name'

insert_query = 'insert_query'
mechanism = "mechanism"
context_code = 'context_code'
sameAsCount = "sameAsCount"

source = "source"
target = "target"
targets = "targets"
dataset = "dataset"
src_dataset = "src_dataset"
trg_dataset = "trg_dataset"
src_graph_type = "src_graph_type"
trg_graph_type = "trg_graph_type"
datasets = "datasets"
predicates = "predicates"

alignments = "alignments"

# the alignment used to reduce another graph (dataset)
reducer = "reducer"
elements = "elements"

research_Q = "research_Q"
entity_ofInterest = "entity_ofInterest"
linkset_alignments = "linkset_alignments"
lens_actions = ":lens_actions"
property = "property"
properties = "properties"

linkset_insert_queries = "linkset_insert_queries"
triples = "triples"
subject = "subject"
predicate = "predicate"
# Number of triples expected
expectedTriples = "expectedTriples"
# Number of duplicates removed
removedDuplicates = "removedDuplicates"
# triples describing or listing all graphs involved for this lens
lens_target_triples = "lens_target_triples"
# The metadata triple of a graph
linkset_metadata = "linkset_metadata"

# the URI of the linked subject resource
src_resource = "source resource"
# the URI of the linked object resource
trg_resource = "target resource"
# table or matrix row
row = "row"
# inverted index that reduces cartesian computation
inv_index = 'inverted index'
# Approximate string similarity value
sim ="similarity measure"
# predicate value of the subject resource
src_value = "source value"
# predicate value of the object resource
trg_value = "target value"

meta_writer = "metadata_writer"
crpdce_writer = "correspondence writer"
singletons_writer = "singletons writer"
batch_writer = 'batch_writer'

meta_writer_path = "metadata writer path "
crpdce_writer_path  = "correspondence writer path "
singletons_writer_path  = "singletons writer path "
batch_output_path = "batch_output_path"
threshold = "threshold"

singletonGraph = "singletonGraph"
alignsSubjects = "alignsSubjects"
alignsObjects = "alignsObjects"
subjectsTarget = "subjectsTarget"
objectsTarget = "objectsTarget"

refined = "refined"
refined_name = "refined_name"
refined_ns = "refined_ns"

expands = "expands"
expands_name = "expands_name"
expands_ns = "expands_ns"

derivedfrom = "derived from"


error_code = "error_code"
result = "result"
message = "message"

researchQ_URI = "researchQ_URI"

intermediate_graph = "intermediate_graph"


stardog_host_name = "stardog_host_name"
stardog_path = 'stardog_path'
stardog_version = "stardog_version"
stardog_user = "stardog_user"
stardog_pass = "stardog_pass"
ll_port = "ll_port"


data_dir = "data_dir"
linkset_dir = "linkset_dir"
lens_dir = "lens_dir"
uploaded_dataset_dir = "uploaded_dataset_dir"
uploaded_alignments= "UPLOADED_ALIGNMENTS"

linkset_Exact_dir = "linkset_Exact_dir"
linkset_Approx_dir = "linkset_Approx_dir"
linkset_Emb_dir = "linkset_Emb_dir"
linkset_ID_dir = "linkset_ID_dir"
linkset_Refined_dir = "linkset_Refined_dir"
linkset_Subset_dir = "linkset_Subset_dir"
lens_Refined_dir = "lens_Refined_dir"

lens_Diff_dir = "lens_Diff_dir"
lens_transitive__dir = "lens_transitive__dir"
lens_Union__dir = "lens_Union__dir"

long_predicate = "long_predicate"
lat_predicate = "lat_predicate"
enriched = "enriched"
delta = "delta"
numeric_approx_type = "numeric_approx_type"
corr_reducer = "corr_reducer"
stardog_data_path = "stardog_data_path"

reference = "reference"
crossCheck = "crossCheck"

unit = "unit"
unit_value = "unit_value"


# CLUSTERING
child = "children"
children = "children"
matrix = "matrix"
column = "column"
annotate = "annotate"
matrix_d = "matrix_d"
expanded_name = "expanded_name"


