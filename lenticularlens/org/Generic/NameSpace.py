from lenticularlens.org.Generic.Server_Settings import settings
import lenticularlens.org.Generic.Settings as St

db = settings[St.database]
DOMAIN_NAME = settings[St.domain_name]

rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfs = "http://www.w3.org/2000/01/rdf-schema#"
xsd = 'http://www.w3.org/2001/XMLSchema#'
owl = "http://www.w3.org/2002/07/owl#"
void = "http://rdfs.org/ns/void#"
bdb = "http://vocabularies.bridgedb.org/ops#"
sdg = 'tag:stardog:api:property:'
prov = "http://www.w3.org/ns/prov#"
skos = "http://www.w3.org/2004/02/skos/core#"
foaf = "http://xmlns.com/foaf/0.1/Organization"

orgref = "http://{}/orgref/resource/".format(DOMAIN_NAME)
grid = "http://www.grid.ac/institutes/"

risis = 'http://{}/'.format(DOMAIN_NAME)
lens = 'http://{}/lens/'.format(DOMAIN_NAME)
riclass = 'http://{}/class/'.format(DOMAIN_NAME)
schema = 'http://{}/ontology/'.format(DOMAIN_NAME)
dataset = "http://{}/dataset/".format(DOMAIN_NAME)
idea = "http://{}/activity/".format(DOMAIN_NAME)
linkset = "http://{}/linkset/".format(DOMAIN_NAME)
method = "http://{}/method/".format(DOMAIN_NAME)
alivocab = "http://{}/alignment/predicate/".format(DOMAIN_NAME)
tmpgraph = "http://{}/alignment/temp-match/".format(DOMAIN_NAME)
tmpvocab = "http://{}/temp-match/temp-match/predicate/".format(DOMAIN_NAME)
mechanism = "http://{}/mechanism/".format(DOMAIN_NAME)
singletons = "http://{}/singletons/".format(DOMAIN_NAME)
justification = "http://{}/justification/".format(DOMAIN_NAME)
alignmentTarget = "http://{}/alignmentTarget/".format(DOMAIN_NAME)
lensOp = "http://{}lens/operator/".format(DOMAIN_NAME)
lensOpu = "http://{}/lens/operator/union".format(DOMAIN_NAME)
lensOpi = "http://{}/lens/operator/intersection".format(DOMAIN_NAME)
lensOpt = "http://{}/lens/operator/transitive".format(DOMAIN_NAME)
lensOpd = "http://{}/lens/operator/difference".format(DOMAIN_NAME)
rsrId = "{}resourceIdentifier".format(alivocab)
plot = "{}plot/".format(alivocab)

reserchQ = "http://{}/dataset/researchQ".format(DOMAIN_NAME)
view = "http://{}/view/".format(DOMAIN_NAME)

cluster = "http://{}/cluster/".format(DOMAIN_NAME)
cluster_constraint = "http://{}/cluster_constrain/".format(DOMAIN_NAME)

lens_type = 'http://vocabularies.bridgedb.org/ops#Lens'
linkset_type = "http://rdfs.org/ns/void#Linkset"

kilometer = "http://qudt.org/vocab/unit#Kilometer"
meter = "http://qudt.org/vocab/unit#Meter"
centimeter = "http://qudt.org/vocab/unit#Centimeter"
mileUSStatute = "http://qudt.org/vocab/unit#MileUSStatute"
yard = "http://qudt.org/vocab/unit#Yard"
inch = "http://qudt.org/vocab/unit#Inch"
foot = "http://qudt.org/vocab/unit#Foot"