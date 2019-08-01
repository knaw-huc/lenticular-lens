from os.path import join
from common.ll.LLData.CSV_Alignments import CSV_ALIGNMENTS_DIR
from common.ll.LLData.CSV_Clusters import CSV_CLUSTER_DIR
from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
import common.ll.Clustering.SimpleLinkClustering as Cls
from common.ll.Generic.Utility import pickle_deserializer


# ****************************************************
"           1. GENERATE THE ILN CLUSTERS             "
"     TESTING THE ALIGNMENT CSV FILE OF THE GA      "
# ****************************************************

# CLUSTERING THE ALIGNMENT
ga_clusters = Cls.simple_csv_link_clustering(
    csv_path=join(CSV_ALIGNMENTS_DIR, "GA-linkset-paper.csv"),
    graph_name="GA-linkset-paper",
    save_in=CLUSTER_SERIALISATION_DIR, activated=False)

# CLUSTERING THE ASSOCIATION BASED RECONCILED DATA
RELATED = "GA-related-paper.csv"
SERIALISED = "Serialized_Cluster_PH1f99c8924c573d6_ga"
recon_names = Cls.extend_cluster(
    serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=SERIALISED,
    csv_association_file=join(CSV_ASSOCIATIONS_DIR, RELATED), save_in=CLUSTER_SERIALISATION_DIR,
    condition_30=False, activated=False)


# ****************************************************
"           1. GENERATE THE ILN CLUSTERS             "
"    TESTING THE ALIGNMENT OF RISIS ISWC CSV FILE    "
# ****************************************************
ser_cluster_name = Cls.simple_csv_link_clustering(
    csv_path=join(CSV_CLUSTER_DIR, "test.csv"),
    graph_name="union_Eter_2014_LeidenRanking_2015_Grid_20170712_H2020_Orgref_20170703_Orgreg_20170718_P1768695787",
    save_in=CLUSTER_SERIALISATION_DIR, activated=False)
# print(serialized_cluster_name)
# serialized_cluster_name = "Serialized_Cluster_PH0485d24f1a809a7"


# ****************************************************
"       2. GENERATE THE RECONCILED ILN CLUSTERS      "
"   TESTING THE SPLITTING OF INVESTIGATED CLUSTERS   "
# ****************************************************
RELATED = ""
SERIALISED = ""
extended_recon_names = Cls.extend_cluster(
    serialisation_dir=CLUSTER_SERIALISATION_DIR, serialized_cluster_name=SERIALISED,
    csv_association_file=join(CSV_CLUSTER_DIR, RELATED), save_in=CLUSTER_SERIALISATION_DIR,
    condition_30=True, activated=False)


# ****************************************************
"            READING THE SERIALISED FILE             "
# ****************************************************
# count = 0
# CLUSTERS = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name="{}-1.txt".format(ser_cluster_name))
# if CLUSTERS:
#     for key, var in CLUSTERS.items():
#         print(key)
#         print(var)
#         if count == 2:
#             break
#         count += 1


# ****************************************************
"         CLUSTERING AN ALIGNMENT CLUSTERING         "
"   THE RECONCILED AND PLOTTING DATA FOR OVERLEAF    "
# ****************************************************
DIR = "C:\Disambiguation\\4-GoldenAgents\\1. VALIDATION\Cedric\\validation"
LINKSET = "14dfe6fbe0fd677288ae055ede75f49b_output.csv"
RELATED = "associations.csv"
SAVED_IN = "C:\Disambiguation\\4-GoldenAgents\\1. VALIDATION\Cedric\\validation\Serialisations"

def test(directory, alignment, related, saved_in, activated):

    # 1. GENERATE THE ILN CLUSTERS
    serialized_cluster_name = Cls.simple_csv_link_clustering(
        csv_path=join(directory, alignment),
        graph_name="GOLDEN AGENT 50 YEARS RESTRICTION", save_in=saved_in, activated=activated)

    # 3. EXTEND THE CLUSTERS
    if serialized_cluster_name is not None:

        # 2. OUTPUTS THE DISTRIBUTION OF THE CLUSTERS FOR LATEX VISUALISATION
        Cls.ilns_distribution(
            saved_in, serialized_cluster_name=serialized_cluster_name,
            label="Golden Agent Data II CLUSTERS", print_latex=True, xmax=None, activated=activated)

        extended_reconciled_names = Cls.extend_cluster(
            saved_in, serialized_cluster_name=serialized_cluster_name,
            csv_association_file=join(directory, related),
            save_in=saved_in, condition_30=True, activated=activated)

        # 4. OUTPUTS THE DISTRIBUTION OF THE CLUSTERS FOR LATEX VISUALISATION
        Cls.ilns_distribution(
            saved_in, serialized_cluster_name=extended_reconciled_names[1],
            label="Golden Agent Data II RECONCILED", print_latex=True, xmax=None, activated=activated)

test(directory=DIR, alignment=LINKSET, related=RELATED, saved_in=SAVED_IN, activated=False)


# import sys
# import common.ll.Generic.Utility as Ut
# import soundex
# Ut.display_structure(soundex.Soundex())
# print(type(soundex.Soundex()))
# s = soundex.Soundex()
# print(s.soundex("Jackson"))
# print(s.soundex("honeyman"))
# Ut.display_structure(sys.modules)



# from common.ll.StringAlgorithm.Soundex import soundex
# print(soundex(["ali", "al", "albert", "alberto", "albertine"], size=3))
#
# from collections import Counter
# print(Counter(["ali", "al", "albert", "alberto", "albertine"]) )
# print(["ali", "al", "albert", "alberto", "albertine"].count("als"))