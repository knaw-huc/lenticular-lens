import src.Tests.TestData as TestData
from src.Clustering.SimpleLinkClustering import cluster_vis_input as visualise
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
visualise(specs=TestData.golden_agents_specifications, activated=True)
