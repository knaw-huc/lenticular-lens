from config_db import execute_query
from node_values import get_node_values


def get_resource_value(resources, targets):

    """
    :param resources    : LIST OF RESOURCE URI FOR WHICH DATA NEEDS TO BE EXTRACTED
    :param targets      : A DICTIONARY WITH THE FOLLOWING KEYS
    :return             :

    DESCRIPTION OF THE PROPERTIES FOR NODE'S LABEL VISUALISATION OBJECT
    ------------------------------------------------------------------
    targets =
    [
        {
            graph           : THE DATASET URI
            data =
                [
                    entity_type : THE ENTITY TYPE OF INTEREST
                    properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                ]
        },
        ...
    ]
    """

    return get_node_values(resources, targets)
