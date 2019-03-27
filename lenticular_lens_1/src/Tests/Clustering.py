from os.path import join
from src.LLData.CSVClusters import CSV_CLUSTER_DIR
from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
import src.Clustering.SimpleLinkClustering as Cls
from src.Generic.Utility import pickle_deserializer

# ****************************************************
"           1. GENERATE THE ILN CLUSTERS             "
"       TESTING THE CLUSTERING OF A CSV FILE         "
# ****************************************************
ser_cluster_name = Cls.simple_csv_link_clustering(
    csv_path=join(CSV_CLUSTER_DIR, "14dfe6fbe0fd677288ae055ede75f49b_output.csv"),
    graph_name="14dfe6fbe0fd677288ae055ede75f49b_output",
    save_in=CLUSTER_SERIALISATION_DIR, activated=True)
# with open(join(CSV_CLUSTER_DIR, "golden_marriage_marriage.csv"), 'r') as read_file:
#     with open(join(CSV_CLUSTER_DIR, "golden_marriage_marriage_2.csv"), 'w') as write_file:
#         for line in read_file:
#             write_file.write(f'{line.rstrip()},1\n')

# print(serialized_cluster_name)
# serialized_cluster_name = "Serialized_Cluster_PH0485d24f1a809a7"

# ****************************************************
"            READING THE SERIALISED FILE             "
# ****************************************************



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
# import src.Generic.Utility as Ut
# import soundex
# Ut.display_structure(soundex.Soundex())
# print(type(soundex.Soundex()))
# s = soundex.Soundex()
# print(s.soundex("Jackson"))
# print(s.soundex("honeyman"))
# Ut.display_structure(sys.modules)



# from src.StringAlgorithm.Soundex import soundex
# print(soundex(["ali", "al", "albert", "alberto", "albertine"], size=3))
#
# from collections import Counter
# print(Counter(["ali", "al", "albert", "alberto", "albertine"]) )
# print(["ali", "al", "albert", "alberto", "albertine"].count("als"))