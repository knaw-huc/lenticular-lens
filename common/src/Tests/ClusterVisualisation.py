import json
from os.path import join
import src.Tests.TestData as TestData
from src.LLData.Validation import CLUSTER_VISUALISATION_DIR
from src.Clustering.SimpleLinkClustering import cluster_vis_input as visualise, cluster_vis_input_2 as visualise_2
# ****************************************************
"       FOR VISUALISING THE CLUSTERS IN D3.JS        "
# ****************************************************
target = [
    {
        "graph": "https://golden.agent/dataset/marriage",
        "data": [
            {"entity_ype": "https://golden.agent/type/Person", "properties":
                ["https://golden.agent/property/name", "https://golden.agent/property/date"]}
        ]
    },
    {
        "graph": "https://golden.agent/dataset/baptism",
        "data": [
            {"entity_type": "https://golden.agent/type/Person", "properties":
                ["https://golden.agent/property/full_name", "https://golden.agent/property/date"]}
        ]
    }
]

from src.Generic.Utility import pickle_deserializer
from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
# from src.LLData.CSVClusters import CSV_CLUSTER_DIR
# from src.Generic.Utility import print_object
# print_object(TestData.targets)
# option = 0
# data = visualise(specs=TestData.ga_specifications, activated=True) if option == 1 \
#     else visualise_2(specs=TestData.ga_specifications, activated=True) if option == 2 else None
#
# with open(join("C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code", "data.json"), 'w') as f:
#     json.dump(data, f, sort_keys=True)

# 753 VALIDATING A LINE
# 357 GOOD EXAMPLE OF NO CYCLE WITH CLUSTER OF 6. IT EXTENDS WITH 4 CLUSTERS
# 123 VERY GOOD EXAMPLE OF A CLUSTER OF SIZE 31 THAT EXTEND TO 20 CLUSTERS AND GENERATES 6 SUB-CLUSTERS
# 456 LOOKS LIKE 123 [EXTENDS WITH 17] AND [GENERATES 3 SUB-CLUSTERS]
cluster_position = 1
data_1 = visualise(specs=TestData.golden_agents_specifications, activated=True)
# data_2 = visualise_2(specs=TestData.golden_agents_specifications, activated=True)

# SEND IT TO BE VISUALISED
# EXTRA CODE FOR TESTING THAT THE FUNCTION WORKS SO FAR
# with open(join("C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code", "data.json"), 'w') as f:
#     json.dump(data_1, f, sort_keys=True)
#
# with open(join("C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code", "data-sub-1.json"), 'w') as f:
#     json.dump(data_1, f, sort_keys=True)
#
# with open(join("C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code", "data-sub-2.json"), 'w') as f:
#     json.dump(data_2[1], f, sort_keys=True)


with open(join(CLUSTER_VISUALISATION_DIR, "data.json"), 'w') as f:
    json.dump(data_1, f, sort_keys=True)

# with open(join(CLUSTER_VISUALISATION_DIR, "data.json"), 'w') as f:
#     json.dump(data_2[1], f, sort_keys=True)




# print_object(res)




