# import Alignments.ConstraintClustering.DatasetsResourceClustering as Dcs
import src.Generic.Settings as St
from src.Generic.Utility import pickle_deserializer
# import Alignments.Linksets.SPA_Linkset as Linkset
import src.Generic .Utility as Ut


###################################################
# CREATING MULTIPLE CLUSTERS IN ONE STEP
###################################################

# THE INITIAL DATASET IS grid_20170712
grid_GRAPH = "http://risis.eu/dataset/grid_20170712"
grid_org_type = "http://xmlns.com/foaf/0.1/Organization"
grid_cluster_PROPS = ["<http://www.grid.ac/ontology/hasAddress>/<http://www.grid.ac/ontology/countryCode>",
                      "<http://www.grid.ac/ontology/hasAddress>/<http://www.grid.ac/ontology/countryName>"]
grid_link_org_props = ["http://www.w3.org/2000/01/rdf-schema#label", "http://www.w3.org/2004/02/skos/core#prefLabel",
                       "http://www.w3.org/2004/02/skos/core#altLabel",
                       "http://xmlns.com/foaf/0.1/homepage"]
grid_main_dict = {St.graph: grid_GRAPH,
                  St.data: [{St.entity_type: grid_org_type, St.properties: grid_link_org_props}]}

# [ORGREF] DATASET TO ADD
orgref_GRAPH = "http://risis.eu/dataset/orgref_20170703"
orgref_cluster_PROPS = ["http://risis.eu/orgref_20170703/ontology/predicate/Country"]
orgref_org_type = "http://risis.eu/orgref_20170703/ontology/class/Organisation"
orgref_link_org_props = ["http://risis.eu/orgref_20170703/ontology/predicate/Name",
                         "http://risis.eu/orgref_20170703/ontology/predicate/Website"]
orgref_main_dict = {St.graph: orgref_GRAPH,
                    St.data: [{St.entity_type: orgref_org_type, St.properties: orgref_link_org_props}]}

# [ETER] DATASET TO ADD
eter_GRAPH = "http://risis.eu/dataset/eter_2014"
eter_cluster_PROPS = ["http://risis.eu/eter_2014/ontology/predicate/Country_Code"]
eter_org_type = "http://risis.eu/eter_2014/ontology/class/University"
eter_link_org_props = ["http://risis.eu/eter_2014/ontology/predicate/Institution_Name",
                       "<http://risis.eu/eter_2014/ontology/predicate/English_Institution_Name>",
                       "http://risis.eu/eter_2014/ontology/predicate/Name_of_foreign_institution",
                       "http://risis.eu/eter_2014/ontology/predicate/Institutional_website"]
eter_main_dict = {St.graph: eter_GRAPH,
                  St.data: [{St.entity_type: eter_org_type, St.properties: eter_link_org_props}]}

# [ORGREG] DATASET TO ADD
orgreg_GRAPH = "http://risis.eu/dataset/orgreg_20170718"
orgreg_cluster_PROPS = ["<http://risis.eu/orgreg_20170718/ontology/predicate/locationOf>"
                        "/<http://risis.eu/orgreg_20170718/ontology/predicate/Country_of_location>",
                        "http://risis.eu/orgreg_20170718/ontology/predicate/Country_of_establishment"]
orgreg_org_type = "http://risis.eu/orgreg_20170718/resource/organization"
orgreg_link_org_props = ["http://risis.eu/orgreg_20170718/ontology/predicate/Name_of_entity",
                         "http://risis.eu/orgreg_20170718/ontology/predicate/English_name_of_entity",
                         "http://risis.eu/orgreg_20170718/ontology/predicate/Entity_current_name_English",
                         "http://risis.eu/orgreg_20170718/ontology/predicate/Website_of_entity"]
orgreg_main_dict = {St.graph: orgreg_GRAPH,
                    St.data: [{St.entity_type: orgreg_org_type, St.properties: orgreg_link_org_props}]}

# [LEIDEN] DATASET TO ADD
leiden_GRAPH = "http://risis.eu/dataset/leidenRanking_2015"
leiden_cluster_PROPS = ["<http://risis.eu/leidenRanking_2015/ontology/predicate/country>"]
leiden_org_type = "http://risis.eu/leidenRanking_2015/ontology/class/University"
leiden_link_org_props = ["http://risis.eu/leidenRanking_2015/ontology/predicate/actor"]
leiden_main_dict = {St.graph: leiden_GRAPH,
                    St.data: [{St.entity_type: leiden_org_type, St.properties: leiden_link_org_props}]}

# [H2020] DATASET TO ADD
h2020_GRAPH = "http://risis.eu/dataset/h2020"
h2020_cluster_PROPS = ["http://risis.eu/cordisH2020/vocab/country"]
h2020_org_type = "http://xmlns.com/foaf/0.1/Organization"
h2020_link_org_props = ["http://xmlns.com/foaf/0.1/name", "http://xmlns.com/foaf/0.1/page"]
h2020_main_dict = {St.graph: h2020_GRAPH,
                   St.data: [{St.entity_type: h2020_org_type, St.properties: h2020_link_org_props}]}

# [OPENAIRE] DATASET TO ADD
openaire_GRAPH = "http://risis.eu/dataset/openAire_20170816"
openaire_cluster_PROPS = ["http://dbpedia.org/ontology/country"]
openaire_org_type = "http://xmlns.com/foaf/0.1/Organization"
openaire_link_org_props = ["http://www.w3.org/2004/02/skos/core#prefLabel",
                           "http://www.w3.org/2004/02/skos/core#altLabel",
                           "http://lod.openaire.eu/vocab/webSiteUrl"]
openaire_main_dict = {St.graph: openaire_GRAPH,
                      St.data: [{St.entity_type: openaire_org_type, St.properties: openaire_link_org_props}]}


targets = [
    grid_main_dict,
    orgref_main_dict,
    orgreg_main_dict,
    eter_main_dict,
    leiden_main_dict,
    h2020_main_dict,
    openaire_main_dict
]

specs = {St.reference: "http://risis.eu/cluster/reference/N1528759258",
         St.mechanism: "exactStrSim",
         St.researchQ_URI: "http://risis.eu/activity/idea_749ab8",
         St.targets: targets}

# ###########################################################################
"              VISUALISATION SPECIFICATIONS FOR RISIS ISWC                 "
# ###########################################################################

def get_cluster_node(ser_name, cluster_position=1, cluster_id=None):

    count = 0
    cluster = None
    from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
    CLUSTERS = pickle_deserializer(
        serialised_folder=CLUSTER_SERIALISATION_DIR, name="{}-1.txt".format(ser_name))
    if CLUSTERS:

        if cluster_id is not None:
            return CLUSTERS[cluster_id]

        for key, data in CLUSTERS.items():
            if count == cluster_position:
                if len(data['nodes']) > 2:
                    data['id'] = key
                    cluster = data
                    break
                else:
                    cluster_position += 5
            count += 1
    return cluster


CLUSTER = get_cluster_node("Serialized_Cluster_PH1f99c8924c573d6_ga", cluster_position=900)

# 10 50 900 1500
specifications = {
    "data_store": "STARDOG",
    "cluster_id": "PH4b23221d4da4c66",
    "cluster_data": {
        # 'nodes': ['<http://www.grid.ac/institutes/grid.1001.0>',
        #           '<http://risis.eu/cordisH2020/resource/participant_999849132>',
        #           '<http://risis.eu/leidenRanking_2015/resource/1056>',
        #           '<http://risis.eu/orgref_20170703/resource/285106>'],
        "nodes": CLUSTER['nodes'] if CLUSTER else [],
        # 'strengths': {
        #     'key_Hf8ea6acc94be5aa': ['1'],
        #     'key_H4c869bc8ee45d2a': ['1'],
        #     'key_Hcffbfb968e684ec': ['1'],
        #     'key_Hf163ba132455ff3': ['1'],
        #     'key_Hea75934b924584b': ['1']},
        'strengths': CLUSTER['strengths'] if CLUSTER else {},
        # 'links': [
        #     ('<http://risis.eu/cordisH2020/resource/participant_999849132>',
        #      '<http://www.grid.ac/institutes/grid.1001.0>'),
        #     ('<http://risis.eu/cordisH2020/resource/participant_999849132>',
        #      '<http://risis.eu/leidenRanking_2015/resource/1056>'),
        #     ('<http://risis.eu/leidenRanking_2015/resource/1056>',
        #      '<http://www.grid.ac/institutes/grid.1001.0>'),
        #     ('<http://risis.eu/cordisH2020/resource/participant_999849132>',
        #      '<http://risis.eu/orgref_20170703/resource/285106>'),
        #     ('<http://risis.eu/leidenRanking_2015/resource/1056>',
        #      '<http://risis.eu/orgref_20170703/resource/285106>')]
        "links": CLUSTER["links"] if CLUSTER else []
    },
    "properties": [
        # GRID
        {"dataset": "http://risis.eu/dataset/grid_20170712",
         "entity_type": "http://xmlns.com/foaf/0.1/Organization",
         "property": "http://www.w3.org/2004/02/skos/core#prefLabel"},
        # ORGREF
        {"dataset": "http://risis.eu/dataset/orgref_20170703",
         "entity_type": "http://risis.eu/orgref_20170703/ontology/class/Organisation",
         "property": "http://risis.eu/orgref_20170703/ontology/predicate/Name"},
        # ORGREG
        {"dataset": "http://risis.eu/dataset/orgreg_20170718",
         "entity_type": "http://risis.eu/orgreg_20170718/ontology/class/University",
         "property": "http://risis.eu/orgreg_20170718/ontology/predicate/Entity_current_name_English"},
        # LEIDEN
        {"dataset": "http://risis.eu/dataset/leidenRanking_2015",
         "entity_type": "http://risis.eu/leidenRanking_2015/ontology/class/University",
         "property": "http://risis.eu/leidenRanking_2015/ontology/predicate/actor"},
        # ETER
        {"dataset": "http://risis.eu/dataset/eter_2014",
         "entity_type": "http://risis.eu/eter_2014/ontology/class/University",
         "property": "<http://risis.eu/eter_2014/ontology/predicate/English_Institution_Name>"},
        # H2020
        {"dataset": 'http://risis.eu/dataset/h2020',
            "entity_type": "http://xmlns.com/foaf/0.1/Organization",
            "property": "http://xmlns.com/foaf/0.1/name"}
    ]
}

golden_agents_specifications = {
    "data_store": "POSTGRESQL",
    "cluster_id": CLUSTER['id'],
    "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
    "associations": 'GA-related-paper.csv',
    "serialised": 'Serialized_Cluster_PH1f99c8924c573d6_ga',
    "cluster_data": {
        "nodes": CLUSTER['nodes'],
        'strengths': CLUSTER['strengths'],
        "links": CLUSTER["links"]
    },
    "properties": [
        # MARRIAGE_PERSON
        {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister",
         "entity_type": "saaOnt_Person",
         "property": "saaOnt_full_nameList"
         },
        # BAPTISM_PERSON
        {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_doopregister",
         "entity_type": "saaOnt_Person",
         "property": "saaOnt_full_name"
         },
        {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico",
         "entity_type": "foaf_Person",
         "property": "foaf_name"
         },
        # {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico",
        #  "entity_type": "schema_Person",
        #  "property": "foaf_name"
        #  },
        # {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__onstage_20190220",
        #  "entity_type": "schema_Person",
        #  "property": "schema_name"
        #  },
        {"dataset": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_begraafregisters",
         "entity_type": "saaOnt_Person",
         "property": "saaOnt_full_name"
         },
    ]
}

RESOURCES = [
    "http://www.grid.ac/institutes/grid.1001.0/address-0",
    "http://www.grid.ac/institutes/grid.1001.0",
    "http://www.grid.ac/institutes/grid.413314.0",
    "http://risis.eu/orgref_20170703/resource/10039929",
    "http://risis.eu/orgref_20170703/resource/12186216",
    "http://risis.eu/orgref_20170703/resource/11979083",
    "http://risis.eu/eter_2014/resource/AT0001",
    "http://risis.eu/eter_2014/resource/AT0002",
    "http://risis.eu/eter_2014/resource/AT0003"
]


# ###########################################################################
"            VISUALISATION SPECIFICATIONS FOR GOLDEN AGENTS                 "
# ###########################################################################


# 10 30 60 70 100
# ---> [10] of size [10] remained [10]
# ---> [400] of size [3] remained [3]
# ---> [700] of size [3] remained [3]


# --> [500] size {5} splits in {2} and [2]


# --> [070] size [3] became size [2]
# --> [130] size [6] became size [3]
# --> [200] size [12] became size [2]
from src.Generic.Utility import print_object

# 376 jan janz evidence
# 458 is also crazy

def get_ga_specs(position):

    GA_CLUSTER = get_cluster_node("Serialized_Cluster_PH1f99c8924c573d6_ga", cluster_position=position)

    ga_specifications = {

        "data_store": "POSTGRESQL",
        "cluster_id": GA_CLUSTER['id'],
        "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
        "associations": 'GA-related-paper.csv',
        "serialised": 'Serialized_Cluster_PH1f99c8924c573d6_ga',
        "cluster_data": {

            "nodes": GA_CLUSTER['nodes'] if GA_CLUSTER else [],

            'strengths': GA_CLUSTER['strengths'] if GA_CLUSTER else {},

            "links": GA_CLUSTER["links"] if GA_CLUSTER else []
        },
        "properties": [

            # MARRIAGE
            {"dataset": "http://goldenagents.org/datasets/Marriage003",
             "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
             "property": "http://goldenagents.org/uva/SAA/ontology/full_name"},

            # ECARTICO
            {"dataset": "http://goldenagents.org/datasets/Ecartico",
             "entity_type": "http://www.vondel.humanities.uva.nl/ecartico/ontology/Person",
             "property": "http://www.vondel.humanities.uva.nl/ecartico/ontology/full_name"},

            # BAPTISM
            {"dataset": "http://goldenagents.org/datasets/Baptism002",
             "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
             "property": "http://goldenagents.org/uva/SAA/ontology/first_name"},

            # BURIAL
            {"dataset": "http://goldenagents.org/datasets/Burial008",
             "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
             "property": "http://goldenagents.org/uva/SAA/ontology/full_name"},

        ]
    }

    return ga_specifications


regex_text = """

http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24444353p1, http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24444353p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24524508p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24524508p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24584356p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24584356p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24674131p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24674131p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24454450p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24454450p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24514526p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24514526p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24524635p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24524635p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24314608p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24314608p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24384694p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24384694p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24404578p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24404578p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24514619p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24514619p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24285260p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24285260p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24286887p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24286887p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24536824p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24536824p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24286916p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24286916p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24414729p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24414729p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24694102p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24694102p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24254615p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24254615p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24444661p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24444661p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24464747p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24464747p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24211797p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24211797p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24271865p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24271865p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24212125p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24212125p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24361872p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24361872p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24331962p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24331962p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24242154p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24242154p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24568800p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24568800p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24379824p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24379824p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24559396p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24559396p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24239767p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24239767p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24261977p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24261977p2
http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24361977p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24361977p2


"""
"http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24392020p1,http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24392020p2"

pattern_1 = "(.*)[,]*<*(http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24444353p1)>*[,]*(.*)"
pattern_2 = "(.*)[,]*<*(http://goldenagents.org/uva/SAA/person/IndexOpDoopregister/saaId24361977p2)>*[,]*(.*)"

import re






