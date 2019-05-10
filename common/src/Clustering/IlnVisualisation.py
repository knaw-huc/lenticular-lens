import re
import time
import gzip
import datetime
import intervals
import statistics
import json
import networkx as nx
import src.Generic.Utility as Ut
import src.Generic.Settings as St
import src.DataAccess.Middleware as Middleware


from math import floor
from copy import deepcopy
from os.path import join
from io import StringIO as Buffer
from collections import defaultdict
from src.Clustering.Iln_eQ import sigmoid
from src.Generic.Utility import pickle_deserializer, to_nt_format, \
    get_uri_local_name_plus, undo_nt_format,  print_object, get_key, hasher, hash_number, problem


# GET PATH OF THE SERIALISED DIRECTORY
from src.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR


_format = "It is %a %b %d %Y %H:%M:%S"
date = datetime.datetime.today()
_line = "--------------------------------------------------------------" \
        "--------------------------------------------------------------"


# ****************************************************
"                 HELPER FUNCTIONS                  "
# ****************************************************


def std(spec):
    spec_data = spec['cluster_data']['strengths']
    sample = []
    for key, strengths in spec_data.items():
        sample += [float(max(strengths))]
    return round(statistics.stdev(sample), 5)


def convert_properties(properties):
    # CONVERT THE PROPERTY LIST INTO A DICTIONARY SUCH THAT A QUERY
    # CAN BE AUTOMATED FOR FETCHING NODE LABELS FOR VISUALISATION
    nodes_vis_properties = []
    for property_data in properties:

        ds_exists = False
        dataset = property_data[St.dataset]
        e_type = property_data[St.entity_type]
        prop = property_data[St.property]

        for ds in nodes_vis_properties:

            # A DICTIONARY WITH THE SPECIFIED DATASET EXISTS
            if dataset == ds[St.graph]:
                ds_exists = True
                # CHECKING WHETHER THE ENTITY TYPE HAS ALREADY BEEN DOCUMENTED
                data = ds[St.data]
                for type_prop in data:

                    # THE DATA-TYPE EXISTS ALREADY FOR THIS DATASET
                    if e_type == type_prop[St.entity_type]:

                        # APPEND THE PROPERTY ONLY IF IT DOES NOT ALREADY EXIST
                        if prop not in type_prop[St.properties]:
                            type_prop[St.properties] += [prop]

                    # THE DATA TYPE DOES NOT EXIST SO WE ADD THE NEW DATA TYPE TO THE DATASET
                    else:
                        data += [
                            {
                                St.entity_type: e_type,
                                St.properties: [prop]
                            }
                        ]

        # THE DATASET IS NOT YET IN THE DICTIONARY
        if ds_exists is False:
            nodes_vis_properties += [{
                St.graph: dataset,
                St.data: [
                    {
                        St.entity_type: e_type,
                        St.properties: [prop]
                    }
                ]}]
    return nodes_vis_properties


def find_associations(nodes, text):

    # NODES REPRESENT THE RESOURCES OF THE INVESTIGATED CLUSTER
    associated = []

    if nodes and len(nodes) > 0:

        # RE-FORMATTING THE RESOURCES TO REMOVE THE NT FORMAT
        for i in range(0, len(nodes)):
            nodes[i] = undo_nt_format(nodes[i])

        # THE PATTERN FOR A RESOURCE
        example = "<*({0})>*[,]+(.*)|(.*)[,]+<*({0})>*"
        pattern = example.format(nodes[0])
        for i in range(1, len(nodes)):
            pattern += F"|{example.format(nodes[i])}"

        # EXTRACT THE LINKS
        found = re.findall(pattern, text)

        # REFINE THE LINK FOR ONLY TUPLES
        for group in found:
            temp = ()
            for item in group:
                if len(item) > 0:
                    temp += (item,)
            if len(temp) > 0:
                associated.append(temp)

        # print_object(associated)

    return associated


def add_vis_evidence(specs, vis_obj, serialised, resources_obj=None, dataset_obj=None, activated=False):

    tab = "" if vis_obj is None else "\t"

    # CONVERTING THE NODES TO A SET FOR GENERATING NODE DE-DUPLICATION
    overall_nodes = set(specs["cluster_data"]["nodes"])

    # IF AN ASSOCIATION FILE IS PROVIDED THEN READ THE FILE TO EXTRACT THE PAIRED NODES
    associations = None

    # THE PAIRED NODES WILL ALLOW TO FETCH THE CLUSTER THAT EXTEND THE CURRENT CLUSTER
    paired_nodes = set()

    # GET THE PAIRED NODE ON THE OTHER SIDE OF THE ASSOCIATION
    # ***************************************************************
    # --> 1 and 2. THIS FIRST PART DEALS WITH ASSOCIATIONS. FROM THE
    # PROVIDED ASSOCIATION CSV FILE, THE CODE EXTRACTS THE NODES OF
    # THE CURRENT CLUSTER THAT EXTEND THE CLUSTER WITH NEW CLUSTERS
    # ***************************************************************
    if 'associations' in specs:

        # ***************************************************************
        print(F"\n{tab}--> 1. FETCHING THE ASSOCIATED NODES ")
        # ***************************************************************

        with gzip.open(join(CSV_ASSOCIATIONS_DIR, specs['associations']), 'rt') as file:

            # LOOK FOR THE NODES IN ASSOCIATION
            associations = find_associations(specs['cluster_data']['nodes'], file.read())

            # ADD THE ASSOCIATION NODES TO THE OVERALL NODES TO PLOT
            for link in associations:

                src = to_nt_format(link[0])
                trg = to_nt_format(link[1])

                if src not in overall_nodes:
                    paired_nodes.add(src)

                if trg not in overall_nodes:
                    paired_nodes.add(trg)

                    # print_object(paired_nodes)

        # ***************************************************************
        print(F"\n{tab}--> 2. FETCHING THE ASSOCIATED CLUSTERS ")
        # ***************************************************************

        # COLLECTS THE CLUSTER ID OF THE CLUSTERS THAT EXTEND THE CURRENT CLUSTER
        extended = set()

        # THE MAPPING OBJECT THAT DOCUMENT THE MAPPING BETWEEN NODE AND CLUSTER THEY BELONG TO
        root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{serialised}-2.txt")

        # THE DICTIONARY OF THE CLUSTERS
        clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{serialised}-1.txt")

        for paired in paired_nodes:
            formatted = to_nt_format(paired)
            if formatted in root:
                extended.add(root[formatted])

        # RUN A RECURSIVE CODE BASED ON THE NEW CLUSTERS (EXTENDED CLUSTERS) FOUND
        for evidence_id in extended:
            ext_cluster = clusters[evidence_id]
            ext_specifications = {
                "data_store": specs['data_store'],
                "cluster_id": evidence_id,
                "cluster_data": {
                    "nodes": ext_cluster['nodes'] if ext_cluster else [],
                    'strengths': ext_cluster['strengths'] if ext_cluster else {},
                    "links": ext_cluster["links"] if ext_cluster else []},
                "properties": specs['properties']
            }

            # RECURSIVE CALL
            plot(ext_specifications, visualisation_obj=vis_obj,
                 resources_obj=resources_obj, dataset_obj=dataset_obj, activated=activated)

    # ADDING THE ASSOCIATION LINKS
    if associations is not None:
        for link in associations:
            formatted_src = to_nt_format(link[0])
            formatted_trg = to_nt_format(link[1])
            if formatted_src in resources_obj and formatted_trg in resources_obj:
                link_dict = {
                    "source": resources_obj[formatted_src],
                    "target": resources_obj[formatted_trg],
                    "distance": 250, "value": 4,
                    "color": "purple",
                    "dash": "20,10,5,5,5,10"
                }
                vis_obj["links"].append(link_dict)


def draw_graph(graph, file_path=None, show_image=False):

    import matplotlib.pyplot as plt
    # https://networkx.github.io/documentation/latest/auto_examples/drawing/
    # plot_node_colormap.html#sphx-glr-auto-examples-drawing-plot-node-colormap-py
    # extract nodes from graph
    # print "GRAPH:", graph
    analysis_builder = Buffer()
    analysis_builder_2 = Buffer()
    # nodes = set([n1 for n1, n2 in graph] + [n2 for n1, n2 in graph])
    nodes = set([data[0] for data in graph] + [data[1] for data in graph])
    # create networkx graph
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in graph:
        g.add_edge(edge[0], edge[1])

    # draw graph
    # pos = nx.shell_layout(g)
    # print edge_count
    colors = range(len(graph))
    pos = nx.spring_layout(g)
    try:
        nx.draw(g, pos, with_labels=True, font_weight='bold', node_size=800, edge_color=colors, width=2)
    except Exception as error:
        "{}".format(error)
        nx.draw(g, pos, with_labels=True, font_weight='bold', node_size=800, edge_color="b", width=2)

    # d_centrality = nx.degree_centrality(g)
    # b_centrality = nx.edge_betweenness_centrality(g)
    # G = nx.connectivity.build_auxiliary_node_connectivity(G)
    # cycles = nx.cycle_basis(G)
    # cycles = nx.simple_cycles(G)
    # cycles = list(nx.simple_cycles(g.to_directed()))
    # nbr_cycles = len(list(filter(lambda x: len(x) > 2, cycles)))/2
    # biggest_ring = reduce((lambda x, y: x if len(x) > len(y) else y), cycles)

    """""""""""""""""""""""""""""""""""""""
    MATRIX COMPUTATIONS
    """""""""""""""""""""""""""""""""""""""
    ratio = 0
    bridges = 0
    closure = 0
    diameter = 0
    nb_used = 0
    nd_used = 0
    edge_discovered = 0
    edge_derived = 0
    interpretation = 0
    estimated_quality = 0
    average_node_connectivity = 0
    normalised_diameter = 0
    normalised_bridge = 0
    normalised_closure = 0

    try:
        node_count = len(nodes)
        average_node_connectivity = nx.average_node_connectivity(g)
        ratio = average_node_connectivity / (len(nodes) - 1)

        edge_discovered = len(graph)
        edge_derived = node_count * (node_count - 1) / 2

        diameter = nx.diameter(g)  # / float(node_count - 1)
        if len(nodes) > 2:
            normalised_diameter = round((float(diameter - 1) / float(len(nodes) - 2)), 3)
        else:
            normalised_diameter = float(diameter - 1)

        bridges = len(list(nx.bridges(g)))
        normalised_bridge = round(float(bridges / float(len(nodes) - 1)), 3)

        closure = round(float(edge_discovered) / float(edge_derived), 3)
        normalised_closure = round(1 - closure, 2)

        # conclusion = round((normalised_closure * normalised_diameter + normalised_bridge) / 2, 3)
        interpretation = round((normalised_closure + normalised_diameter + normalised_bridge) / 3, 3)

        nb_used = round(sigmoid(bridges) if sigmoid(bridges) > normalised_bridge else normalised_bridge, 3)
        nd_used = round(sigmoid(diameter - 1)
                        if sigmoid(diameter - 1) > normalised_diameter else normalised_diameter, 3)
        estimated_quality = round((nb_used + nd_used + normalised_closure) / float(3), 3)

    except Exception as error:
        print("There was a problem:\n{}".format(error))

    """""""""""""""""""""""""""""""""""""""
    RETURN MATRIX COMPUTATIONS
    """""""""""""""""""""""""""""""""""""""
    analysis_builder.write("\n\nNETWORK ANALYSIS")
    analysis_builder.write("\n\tNETWORK {}".format(graph))
    analysis_builder.write("\n\t{:31} : {}".format("MAX DISTANCE:", closure))
    analysis_builder.write("\n\t{:31} : {}".format("MAXIMUM POSSIBLE CONNECTIVITY", len(nodes) - 1))
    analysis_builder.write("\n\t{:31} : {}".format("AVERAGE NODE CONNECTIVITY", average_node_connectivity))
    analysis_builder.write("\n\t{:31} : {}".format("AVERAGE NODE CONNECTIVITY RATIO", ratio))
    analysis_builder.write("\n\t{:31} : {}".format("BRIDGES", bridges))
    analysis_builder.write("\n\t{:31} : {}".format("CLOSURE", closure))
    analysis_builder.write("\n\t{:31} : {}".format("DIAMETER", diameter))
    analysis_builder.write("\n\t{:31} : {}".format("QUALITY", interpretation))
    analysis_builder.write("\n\t{:31} : {}".format("QUALITY USED", estimated_quality))
    analysis_builder.write("\n\tSUMMARY 1: BRIDGE {} CLOSURE {} DIAMETER {} QUALITY {} QUALITY USED {}".format(
        normalised_bridge, normalised_closure, normalised_diameter, interpretation, estimated_quality))
    analysis_builder.write("\n\tSUMMARY 2: BRIDGE {} CLOSURE {} DIAMETER {} QUALITY {} QUALITY USED {}".format(
        nb_used, normalised_closure, nd_used, interpretation, estimated_quality))

    """""""""""""""""""""""""""""""""""""""
    PRINTING MATRIX COMPUTATIONS IN PLOT
    """""""""""""""""""""""""""""""""""""""
    analysis_builder_2.write(
        "\nMETRICS READING: THE CLOSER TO ZERO, THE BETTER"
        "\n\nAverage Degree [{}] \nBridges [{}] normalised to [{}] [{}]\nDiameter [{}]  normalised to [{}] [{}]"
        "\nClosure [{}/{}][{}] normalised to [{}]\n\n>>> Decision Support [{}] [{}] <<<".format(
            average_node_connectivity, bridges, normalised_bridge, nb_used, diameter, normalised_diameter,
            nd_used, edge_discovered, edge_derived, closure, normalised_closure, interpretation, estimated_quality))

    if estimated_quality <= 0.1:
        analysis_builder_2.write("\n\nInterpretation: GOOD")

    elif bridges == 0 and diameter <= 2:
        analysis_builder_2.write("ACCEPTABLE")

    elif ((estimated_quality > 0.1) and (estimated_quality < 0.25)) or (bridges == 0):
        analysis_builder_2.write("\n\nInterpretation: UNCERTAIN")

    else:
        analysis_builder_2.write("\n\nInterpretation: THE NETWORK IS NOT A GOOD REPRESENTATION OF A SINGLE RESOURCE")

    if bridges > 0:
        analysis_builder_2.write("\n\nEvidence: NEED BRIDGE INVESTIGATION")

    if diameter > 2:
        analysis_builder_2.write("\n\nEvidence: TOO MANY INTERMEDIATES")

    if bridges == 0 and diameter <= 2:
        analysis_builder_2.write("\n\nEvidence: LESS INTERMEDIATES AND NO BRIDGE")

    """""""""""""""""""""""""""""""""""""""
    DRAWING THE NETWORK WITH MATPLOTLIB
    """""""""""""""""""""""""""""""""""""""
    if file_path:
        plt.title("LINKED RESOURCES NETWORK TOPOLOGY ANALYSIS\n{}".format(analysis_builder_2.getvalue()))
        # plt.legend("TEXT")
        # plt.text(-1.3, 1, "NETWORK ANALYSIS")
        # plt.show()
        plt.xlim(-1.9, 1.9)
        plt.ylim(-1.9, 1.9)
        plt.savefig(file_path, dpi=100, bbox_inches="tight", pad_inches=1, edgecolor='r')
        plt.close()

    if show_image:
        plt.show()

    return analysis_builder.getvalue()


# ****************************************************
"       VISUALISATION: INVESTIGATED vs EVIDENCE     "
# ****************************************************


def plot(specs, visualisation_obj=None, resources_obj=None,
         dataset_obj=None, sub_clusters=None, root=None, investigated=True, activated=False):

    """
    :param specs: CONTAINS ALL INFORMATION FOR GENERATING
                  THE CLUSTER FOR VISUALISATION PURPOSES.

    :param visualisation_obj: A DICTIONARY ABOUT LIST OF NODES AND LINKS AND MORE.
                              TIS IS THE NEEDED OBJECT FOR VISUALISATION

    :param resources_obj: THIS IS A DICTIONARY THAT MAPS THE URI OF A NODE TO ITS UNIQUE LABEL

    :param dataset_obj:

    :param dataset_obj:

    :param sub_clusters:

    :param root:

    :param investigated:

    :param activated: BOOLEAN ARGUMENT FOR NOT RUNNING THE FUNCTION UNLESS SPECIFICALLY REQUESTED
    param visualisation_obj: A DICTIONARY ABOUT LIST OF NODES AND LINKS AND MORE. T
                             HIS IS THE NEEDED OBJECT FOR VISUALISATION

    :return: A DICTIONARY DESCRIBED BELOW
    """

    """
    DESCRIPTION OF THE FUNCTION'S PARAMETERS
    ----------------------------------------
    specs = {

        "data_store"          : THE DATA STORE. FOR EXAMPLE STARDOG, POSTGRESQL, VIRTUOSO
        "cluster_id"          : THE ID OF THE CLUSTER TO BE VISUALISED
        "cluster_data"        : DICTIONARY OF NODES[], LINKS[] AND LINK STRENGTHS{KEY: VALUE}
        "properties": []
            # LIST OF DICTIONARIES WITH THE FOLLOWING KEYS
            #   dataset       : THE URI OF THE DATASET
            #   entity_type   : THE URI OF THE ENTITY TYPE
            #   property      : THE URI OF THE PROPERTY
    }

    DESCRIPTION OF THE PROPERTIES FOR NODE'S LABEL VISUALISATION OBJECT
    -------------------------------------------------------------------
    nodes_vis_properties =
    [
        {
            graph               : THE DATASET URI
            data = LIST OF DICTIONARIES
                [
                    entity_type : THE ENTITY TYPE OF INTEREST
                    properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                ]
        },
        ...
    ]

    DESCRIPTION OF THE CLUSTER DATA NEEDED FOR GRAPH VISUALISATION
    --------------------------------------------------------------
    cluster_data =
    {
        id: THE ID OF THE CLUSTER
        confidence  (FLOAT)     : THE SMALLEST STRENGTH
        decision    (FLOAT)     : e_Q VALUE
        metric      (STRING)    : e_Q message
        messageConf (STRING)    : A WHATEVER STRING

        "nodes": [] THE NODES IS A LIST OF DICTIONARIES WITH THE FOLLOWING KEYS
            #   id     (STRING)     : LABEL OF THE RESOURCE
            #   uri    (STRING)     : THE URI OF THE RESOURCE
            #   group  (INT)        : INDEX REPRESENTING THE DATASET FROM WHICH THE
            #                         RESOURCE ORIGINATED FROM. THIS HELPS COLORING THE NODE
            #   size   (STRING)     : THE SIZE OF THE NODE FOR DIFFERENTIATING
            #                         INVESTIGATED [10] ILN FROM EVIDENCE [5] ILN

        "links": [] THE LINKS IS A LIST OF DICTIONARIES WITH THE FOLLOWING KEYS:
            #   source   (STRING)   : LABEL OF THE RESOURCE. IT IS THE SAME AS THE KEY "id" IN THE NODE
            #   target   (STRING)   : LABEL OF THE RESOURCE. IT IS THE SAME AS THE KEY "id" IN THE NODE
            #   strength (STRING)   : THE SIMILARITY SCORE OR THE RECONCILIATION SCORE OR THE DERIVED SCORE
            #   distance (INT)      : THE LENGTH OF THE LINK.
            #                         A STANDARD LINK HAS A DEFAULT DISTANCE OF [150] AND THE ASSOCIATION IS [250]
            #   value    (INT)      : THICKNESS OF LINK. THE DEFAULT VALUE IS [4]
            #   color    (STRING)   : THE COLOR OF THE LINK
            #                 BLACK         -> EXACT MATCH  => (STRENGTH = 1)
            #                 RED           -> APPROX MATCH => (STRENGTH = [0, 1[)
            #                 PURPLE        -> ASSOCIATION
            #   dash     (STRING)   : THE PATTERN OF THE LINK LINE
            #                 APPROX        -> CONCATENATE "3," AND STRING OF "20 * (1 - LINK STRENGTH)"
            #                 ASSOCIATION   -> A STRING OF "20,10,5,5,5,10"
    }
    """

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [cluster_vis_input] IS NOT ACTIVATED.")
        return

    specs = deepcopy(specs)

    start = time.time()
    tab = "" if visualisation_obj is None else "\t"
    fill = 100 if visualisation_obj is None else 96

    print("\n{}{:.^{}}".format(tab, F"", fill))
    print("{}{:.^{}}".format(
        tab, F" VISUALISING CLUSTER {specs['cluster_id']} OF SIZE {len(specs['cluster_data']['nodes'])} ", fill))
    print("{}{:.^{}}".format(tab, F" OPTION-1: INVESTIGATED vs EVIDENCE ", fill))
    print("{}{:.^{}}".format(tab, F"", fill))

    dataset_index = {} if dataset_obj is None else dataset_obj

    # THE DICTIONARY TO RETURN FOR VISUALISATION
    vis_data = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    } if visualisation_obj is None else visualisation_obj

    # BOOK KEEPING OF THE NODES IN THE CLUSTER
    resources = {} if resources_obj is None else resources_obj

    # query = None
    data_store = specs[St.data_store]

    # CHANGING THE PROPERTIES INPUT DATA STRUCTURE WHICH IS A LIST
    # TO A DICTIONARY DATA STRUCTURE
    nodes_vis_properties = []

    # PRINTING THE SPECIFICATIONS (INPUT)
    print_object(specs, comment="USER SPECIFICATIONS", overview=False, activated=False)

    # CONVERT THE PROPERTY LIST INTO A DICTIONARY SUCH THAT A QUERY
    # CAN BE AUTOMATED FOR FETCHING NODE LABELS FOR VISUALISATION
    if specs[St.properties] is None:
        nodes_vis_properties = None

    else:
        for property_data in specs[St.properties]:

            ds_exists = False
            dataset = property_data[St.dataset]
            e_type = property_data[St.entity_type]
            prop = property_data[St.property]

            for ds in nodes_vis_properties:

                # A DICTIONARY WITH THE SPECIFIED DATASET EXISTS
                if dataset == ds[St.graph]:
                    ds_exists = True
                    # CHECKING WHETHER THE ENTITY TYPE HAS ALREADY BEEN DOCUMENTED
                    data = ds[St.data]
                    for type_prop in data:

                        # THE DATA-TYPE EXISTS ALREADY FOR THIS DATASET
                        if e_type == type_prop[St.entity_type]:

                            # APPEND THE PROPERTY ONLY IF IT DOES NOT ALREADY EXIST
                            if prop not in type_prop[St.properties]:
                                type_prop[St.properties] += [prop]

                        # THE DATA TYPE DOES NOT EXIST SO WE ADD THE NEW DATA TYPE TO THE DATASET
                        else:
                            data += [
                                {
                                    St.entity_type: e_type,
                                    St.properties: [prop]
                                }
                            ]

            # THE DATASET IS NOT YET IN THE DICTIONARY
            if ds_exists is False:
                nodes_vis_properties += [{
                    St.graph: dataset,
                    St.data: [
                        {
                            St.entity_type: e_type,
                            St.properties: [prop]
                        }
                    ]}]

        # PRINTING SELECTED PROPERTIES FOR EACH GRAPHS
        print_object(nodes_vis_properties,
                     comment="SELECTED PROPERTIES PER GRAPH AND ENTITY TYPE", overview=False, activated=False)

    # CONVERTING THE NODES TO A SET FOR GENERATING NODE DE-DUPLICATION
    overall_nodes = set(specs["cluster_data"]["nodes"])

    if sub_clusters is not None:
        group = set()
        count = 0
        for node in overall_nodes:
            count += 1
            # print(node)
            root[node] = node
            group.add(node)
        # sub_clusters[specs["cluster_id"] + "-investigated"] = group
        # print_object(root, overview=False)

    # IF AN ASSOCIATION FILE IS PROVIDED THEN READ THE FILE TO EXTRACT THE PAIRED NODES
    associations = None

    # THE PAIRED NODES WILL ALLOW TO FETCH THE CLUSTER THAT EXTEND THE CURRENT CLUSTER
    paired_nodes = set()

    # ***************************************************************
    # --> 1 and 2. THIS FIRST PART DEALS WITH ASSOCIATIONS. FROM THE
    # PROVIDED ASSOCIATION CSV FILE, THE CODE EXTRACTS THE NODES OF
    # THE CURRENT CLUSTER THAT EXTEND THE CLUSTER WITH NEW CLUSTERS
    # ***************************************************************
    if 'associations' in specs and specs['associations']:

        # ***************************************************************
        print(F"\n{tab}--> 1. FETCHING THE ASSOCIATED NODES ")
        # ***************************************************************

        with gzip.open(join(CSV_ASSOCIATIONS_DIR, specs['associations']), 'rt') as file:

            # LOOK FOR THE NODES IN ASSOCIATION
            associations = find_associations(specs['cluster_data']['nodes'], file.read())

            # ADD THE ASSOCIATION NODES TO THE OVERALL NODES TO PLOT
            for link in associations:

                src = to_nt_format(link[0])
                trg = to_nt_format(link[1])

                if src not in overall_nodes:
                    paired_nodes.add(src)

                if trg not in overall_nodes:
                    paired_nodes.add(trg)

            # print_object(paired_nodes)

        # ***************************************************************
        print(F"\n{tab}--> 2. FETCHING THE ASSOCIATED CLUSTERS ")
        # ***************************************************************

        # COLLECTS THE CLUSTER ID OF THE CLUSTERS THAT EXTEND THE CURRENT CLUSTER
        extended = set()

        # THE MAPPING OBJECT THAT DOCUMENT THE MAPPING BETWEEN NODE AND CLUSTER THEY BELONG TO
        root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-2.txt")

        # THE DICTIONARY OF THE CLUSTERS
        clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-1.txt")

        for paired in paired_nodes:
            extended.add(root[to_nt_format(paired)])

        print(F"\tTHE CLUSTERS EXTENDS TO {len(extended)} OTHER CLUSTERS")

        # RUN A RECURSIVE CODE BASED ON THE NEW CLUSTERS (EXTENDED CLUSTERS) FOUND
        for evidence_id in extended:

            evidence_cluster = clusters[evidence_id]
            evidence__specifications = {

                "data_store": "STARDOG",
                "cluster_id": evidence_id,
                "cluster_data": {
                    "nodes": evidence_cluster['nodes'] if evidence_cluster else [],
                    'strengths': evidence_cluster['strengths'] if evidence_cluster else {},
                    "links": evidence_cluster["links"] if evidence_cluster else []
                },
                "properties": specs['properties']
            }

            # RECURSIVE CALL
            plot(
                evidence__specifications, visualisation_obj=vis_data, investigated=False,
                resources_obj=resources, dataset_obj=dataset_index, activated=activated)

    # ***************************************************************
    print(F"\n{tab}--> 3. FETCHING THE QUERY RESULT DEPENDING ON THE QUERY TYPE")
    # ***************************************************************
    # NOW, CONVERTS THE SET OF NODE TO A LIST FOR FETCHING THE LABELS
    # specs["cluster_data"]["nodes"] = list(specs["cluster_data"]["nodes"])

    try:
        query = Middleware.node_labels_switcher[data_store](
            resources=specs["cluster_data"]["nodes"], targets=nodes_vis_properties) if nodes_vis_properties is not None \
            else None
        # print(query)

    except KeyError as err:
        query = None
        print(F"\tKEY ERROR: {err}")

    # ***************************************************************
    print(F"\n{tab}--> 4. RUNNING THE QUERY")
    # ***************************************************************
    # query = "select distinct ?subject " \
    #         "{ GRAPH <http://risis.eu/dataset/eter_2014> {?subject a ?o} } limit 3"
    # result = None
    table = None
    if query and (data_store in Middleware.run_query_matrix_switcher):
        result = Middleware.run_query_matrix_switcher[data_store](query)
        # Stardog.display_matrix(result, spacing=130, is_activated=True)
        table = result[St.result] if isinstance(result, dict) else result

    # ***************************************************************
    print(F"\n{tab}--> 5. BUILDING VISUALISATION OBJECT FOR UI")
    # ***************************************************************

    # NO NEED TO CONTINUE AS NO RESULT WAS FETCHED FROM THE DB SEVER
    if table is not None:

        # ITERATING THROUGH THE RETURN TABLE FROM THE DB SERVER
        # --> 1. CRATING THE NODE FOR THE VISUALISATION
        for i in range(1, len(table)):

            # CONVERT THE DATASET NAME INTO A DIGIT FOR SETTING A NODE'S COLOR
            i_dataset = table[i][1]
            label = table[i][3]
            uri = table[i][0]
            formatted_uri = to_nt_format(uri)

            if i_dataset not in dataset_index:
                dataset_index[i_dataset] = hash_number(i_dataset)

            # DOCUMENTING THE RESOURCE LABELS.
            # THIS MAKES SURE NODE WITH ALTERNATIVE NAME DO NOT CAME MORE THAN ONCE
            if formatted_uri not in resources:

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                db_label = get_uri_local_name_plus(i_dataset)
                underscore = db_label.split("__")
                db_label = underscore[1] if len(underscore) > 1 else db_label
                label = F"-- {label}"
                resources[formatted_uri] = F"{label} ({db_label} {get_uri_local_name_plus(uri)})"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formatted_uri],
                    "uri": uri,
                    "group": dataset_index[i_dataset],
                    "size": "8" if visualisation_obj is None else "5"
                }

                if investigated is True:
                    node_dict['investigated'] = str(investigated).lower()
                    node_dict["size"] = 8

                vis_data["nodes"].append(node_dict)

    else:

        index = hash_number(hasher(specs['cluster_id']))

        for rsc in specs["cluster_data"]["nodes"]:
            formatted_uri = to_nt_format(rsc)

            # DOCUMENTING THE RESOURCE LABELS.
            # THIS MAKES SURE NODE WITH ALTERNATIVE NAME DO NOT COME MORE THAN ONCE
            if formatted_uri not in resources:

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                # label = F"-- {hasher(formatted_uri)}"
                # label = get_uri_local_name_plus(formatted_uri)
                label = formatted_uri
                resources[formatted_uri] = F"{label}"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formatted_uri],
                    "uri": rsc,
                    "group": index,
                    "size": "8" if visualisation_obj is None else "5"
                }

                if investigated is True:
                    node_dict['investigated'] = str(investigated).lower()
                    node_dict["size"] = 8

                vis_data["nodes"].append(node_dict)

    # --> 2. CREATE THE LINKS: THE NODE NETWORK OBJECT
    cluster_strengths = specs["cluster_data"]["strengths"]
    for source, target in specs["cluster_data"]["links"]:
        # print(source, target )
        # EXTRACTING THE LINK'S STRENGTH
        current_link = (source, target) if source < target else (target, source)
        key_1 = "key_{}".format(str(Ut.hasher(current_link)).replace("-", "N"))

        # GETTING THE MAXIMUM STRENGTH IS MORE STRENGTH IS COMPUTED FOR THE LINK
        strength = float(max(cluster_strengths[key_1]))
        association = False
        link_dict = {
            "source": resources[to_nt_format(source)],
            "target": resources[to_nt_format(target)],
            "strength": F"{strength}",
            "distance": 250 if association is True else 150, "value": 4,
            "color": "purple" if association is True else("black" if strength == 1 else "red"),
            "dash": "20,10,5,5,5,10" if association is True else F"3,{20 * (1 - strength)}"
        }
        vis_data["links"].append(link_dict)
        # print(source, target)

    # ADDING THE ASSOCIATION LINKS
    if associations is not None:
        for link in associations:
            link_dict = {
                "source": resources[to_nt_format(link[0])],
                "target": resources[to_nt_format(link[1])],
                "distance": 250, "value": 4,
                "color": "purple",
                "dash": "20,10,5,5,5,10"
            }
            vis_data["links"].append(link_dict)

    # --> 3. RETURNING THE VISUALISATION OBJECT FOR RENDERING
    # print_object(vis_data)

    if visualisation_obj is None:
        Ut.completed(start)

    return vis_data

    # RETURN FEEDBACK
    # else:
    #
    #     print('\n\tTHE QUERY DID NOT YIELD ANY RESULT...'
    #           '\n\tIF YOU ARE EXPECTING RESULTS, PLEASE CHECK THE AUTOMATED QUERY FOR FURTHER DEBUGGING.')
    #
    #     if len(specs["cluster_data"]["nodes"]) == 0:
    #         print('\tA QUICK CHECK SHOWS THAT THE CLUSTER HAS NO RESOURCE (NO NODES).')
    #
    #         # IF THE INVESTIGATED CLUSTER EXTENDS, COLLECT ALL ILNS IT EXTENDS TO
    #         # FOR EACH EXTENDED CLUSTER, ADD THE NODES
    #         # FOR EACH EXTENDED CLUSTER, ADD THE LINKS
    #         # ADD THE ASSOCIATION
    #
    #         # LIST OF CLUSTERS THAT EXTEND
    #
    #         # print_object(root_reconciled)
    #         # print(type(root_reconciled))


# ****************************************************
"    VISUALISATION: INVESTIGATED vs SUB-CLUSTERS     "
# ****************************************************


def plot_reconciliation(specs, visualisation_obj=None, activated=False):

    """
    :param specs: CONTAINS ALL INFORMATION FOR GENERATING
                  THE CLUSTER FOR VISUALISATION PURPOSES.

    :param visualisation_obj: A DICTIONARY ABOUT LIST OF NODES AND LINKS AND MORE. T
                                 HIS IS THE NEEDED OBJECT FOR VISUALISATION

    :param activated: BOOLEAN ARGUMENT FOR NOT RUNNING THE FUNCTION UNLESS SPECIFICALLY REQUESTED
    :return: A DICTIONARY DESCRIBED BELOW
    """

    """
    DESCRIPTION OF THE FUNCTION'S PARAMETERS
    ----------------------------------------
    specs = {

        "data_store"          : THE DATA STORE. FOR EXAMPLE STARDOG, POSTGRESQL, VIRTUOSO
        "cluster_id"          : THE ID OF THE CLUSTER TO BE VISUALISED
        "cluster_data"        : DICTIONARY OF NODES[], LINKS[] AND LINK STRENGTHS{KEY: VALUE}
        "properties": []
            # LIST OF DICTIONARIES WITH THE FOLLOWING KEYS
            #   dataset       : THE URI OF THE DATASET
            #   entity_type   : THE URI OF THE ENTITY TYPE
            #   property      : THE URI OF THE PROPERTY
    }

    DESCRIPTION OF THE PROPERTIES FOR NODE'S LABEL VISUALISATION OBJECT
    -------------------------------------------------------------------
    nodes_vis_properties =
    [
        {
            graph               : THE DATASET URI
            data = LIST OF DICTIONARIES
                [
                    entity_type : THE ENTITY TYPE OF INTEREST
                    properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                ]
        },
        ...
    ]

    DESCRIPTION OF THE CLUSTER DATA NEEDED FOR GRAPH VISUALISATION
    --------------------------------------------------------------
    cluster_data =
    {
        id: THE ID OF THE CLUSTER
        confidence  (FLOAT)     : THE SMALLEST STRENGTH
        decision    (FLOAT)     : e_Q VALUE
        metric      (STRING)    : e_Q message
        messageConf (STRING)    : A WHATEVER STRING

        "nodes": [] THE NODES IS A LIST OF DICTIONARIES WITH THE FOLLOWING KEYS
            #   id     (STRING)     : LABEL OF THE RESOURCE
            #   uri    (STRING)     : THE URI OF THE RESOURCE
            #   group  (INT)        : INDEX REPRESENTING THE DATASET FROM WHICH THE
            #                         RESOURCE ORIGINATED FROM. THIS HELPS COLORING THE NODE
            #   size   (STRING)     : THE SIZE OF THE NODE FOR DIFFERENTIATING
            #                         INVESTIGATED [10] ILN FROM EVIDENCE [5] ILN

        "links": [] THE LINKS IS A LIST OF DICTIONARIES WITH THE FOLLOWING KEYS:
            #   source   (STRING)   : LABEL OF THE RESOURCE. IT IS THE SAME AS THE KEY "id" IN THE NODE
            #   target   (STRING)   : LABEL OF THE RESOURCE. IT IS THE SAME AS THE KEY "id" IN THE NODE
            #   strength (STRING)   : THE SIMILARITY SCORE OR THE RECONCILIATION SCORE OR THE DERIVED SCORE
            #   distance (INT)      : THE LENGTH OF THE LINK.
            #                         A STANDARD LINK HAS A DEFAULT DISTANCE OF [150] AND THE ASSOCIATION IS [250]
            #   value    (INT)      : THICKNESS OF LINK. THE DEFAULT VALUE IS [4]
            #   color    (STRING)   : THE COLOR OF THE LINK
            #                 BLACK         -> EXACT MATCH  => (STRENGTH = 1)
            #                 RED           -> APPROX MATCH => (STRENGTH = [0, 1[)
            #                 PURPLE        -> ASSOCIATION
            #   dash     (STRING)   : THE PATTERN OF THE LINK LINE
            #                 APPROX        -> CONCATENATE "3," AND STRING OF "20 * (1 - LINK STRENGTH)"
            #                 ASSOCIATION   -> A STRING OF "20,10,5,5,5,10"
    }
    """

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [cluster_vis_input_2] IS NOT ACTIVATED.")
        return

    specs = deepcopy(specs)

    start = time.time()
    tab = "" if visualisation_obj is None else "\t"
    fill = 100 if visualisation_obj is None else 96
    print("\n{}{:.^{}}".format(tab, F"", fill))
    print("{}{:.^{}}".format(
        tab, F" VISUALISING CLUSTER {specs['cluster_id']} OF SIZE {len(specs['cluster_data']['nodes'])} ", fill))
    print("{}{:.^{}}".format(tab, F" OPTION-2: INVESTIGATED vs SUB-CLUSTERS ", fill))
    print("{}{:.^{}}".format(tab, F"", fill))

    # query = None
    data_store = specs[St.data_store]

    # CHANGING THE PROPERTIES INPUT DATA STRUCTURE WHICH IS A LIST
    # TO A DICTIONARY DATA STRUCTURE
    nodes_vis_properties = []

    # PRINTING THE SPECIFICATIONS (INPUT)
    print_object(specs, comment="USER SPECIFICATIONS", overview=False, activated=False)

    # CONVERT THE PROPERTY LIST INTO A DICTIONARY SUCH THAT A QUERY
    # CAN BE AUTOMATED FOR FETCHING NODE LABELS FOR VISUALISATION
    for property_data in specs[St.properties]:

        ds_exists = False
        dataset = property_data[St.dataset]
        e_type = property_data[St.entity_type]
        prop = property_data[St.property]

        for ds in nodes_vis_properties:

            # A DICTIONARY WITH THE SPECIFIED DATASET EXISTS
            if dataset == ds[St.graph]:
                ds_exists = True
                # CHECKING WHETHER THE ENTITY TYPE HAS ALREADY BEEN DOCUMENTED
                data = ds[St.data]
                for type_prop in data:

                    # THE DATA-TYPE EXISTS ALREADY FOR THIS DATASET
                    if e_type == type_prop[St.entity_type]:

                        # APPEND THE PROPERTY ONLY IF IT DOES NOT ALREADY EXIST
                        if prop not in type_prop[St.properties]:
                            type_prop[St.properties] += [prop]

                    # THE DATA TYPE DOES NOT EXIST
                    else:
                        data += [
                            {
                                St.entity_type: e_type,
                                St.properties: [prop]
                            }
                        ]

        #   THE DATASET IS NOT YET IN THE DICTIONARY
        if ds_exists is False:
            nodes_vis_properties += [{
                St.graph: dataset,
                St.data: [
                    {
                        St.entity_type: e_type,
                        St.properties: [prop]
                    }
                ]}]

    # PRINTING SELECTED PROPERTIES FOR EACH GRAPHS
    print_object(nodes_vis_properties,
                 comment="SELECTED PROPERTIES PER GRAPH AND ENTITY TYPE", overview=False, activated=False)

    # ***************************************************************
    print(F"\n{tab}--> 1. FETCHING THE QUERY RESULT DEPENDING ON THE QUERY TYPE")
    # ***************************************************************

    try:
        query = Middleware.node_labels_switcher[data_store](
            resources=specs["cluster_data"]["nodes"], targets=nodes_vis_properties)
        # print(query)
    except KeyError as err:
        query = None
        print(F"\tKEY ERROR: {err}")

    # ***************************************************************
    print(F"\n{tab}--> 2. RUNNING THE QUERY")
    # ***************************************************************
    # query = "select distinct ?subject " \
    #         "{ GRAPH <http://risis.eu/dataset/eter_2014> {?subject a ?o} } limit 3"
    result = None
    if data_store in Middleware.run_query_matrix_switcher:
        result = Middleware.run_query_matrix_switcher[data_store](query)
    # Stardog.display_matrix(result, spacing=130, is_activated=True)
    table = result[St.result] if isinstance(result, dict) else result

    # ***************************************************************
    print(F"\n{tab}--> 3. BUILDING VISUALISATION OBJECT FOR UI")
    # ***************************************************************

    dataset = {}
    # BOOK KEEPING OF THE NODES IN THE CLUSTER
    resources = {}
    # THE RECONCILED CLUSTERS
    reconciled = None
    # FOE FETCHING THE IDs OF THE SUB-CLUSTERS
    sub_clusters_id = set()
    # THE DICTIONARY TO RETURN FOR VISUALISATION
    vis_data = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    } if visualisation_obj is None else visualisation_obj
    # FRO CHECKING WHETHER THE MAIN CLUSTER HAS BEEN RESTRUCTURED BASED ON ASSOCIATIONS
    is_restructured = True if 'sub_clusters' in specs else False

    # DE-SERIALISING THE RECONCILED CLUSTERS
    root_reconciled = None
    if is_restructured is True:
        reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt")
        root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt")

    # NO NEED TO CONTINUE AS NO RESULT WAS FETCHED FROM THE DB SEVER
    if table is not None:

        # ITERATING THROUGH THE RETURN TABLE FROM THE DB SERVER
        # --> 1. CRATING THE NODE FOR THE VISUALISATION
        for i in range(1, len(table)):

            # CONVERT THE DATASET NAME INTO A DIGIT FOR SETTING A NODE'S COLOR
            i_dataset = table[i][1]
            label = table[i][3]
            uri = table[i][0]
            formatted_uri = to_nt_format(uri)
            if i_dataset not in dataset:
                dataset[i_dataset] = hash_number(i_dataset)

            # DOCUMENTING THE RESOURCE LABELS.
            # THIS MAKES SURE NODE WITH ALTERNATIVE NAME DO NOT CAME MORE THAN ONCE
            if formatted_uri not in resources:

                # COLLECTING THE LIST OF CORROBORATED NODES
                if is_restructured is True and formatted_uri in root_reconciled:
                    sub_clusters_id.add(root_reconciled[formatted_uri])

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                db_label = get_uri_local_name_plus(i_dataset)
                underscore = db_label.split("__")
                db_label = underscore[1] if len(underscore) > 1 else db_label
                label = F"-- {label}"

                resources[formatted_uri] = F"{label} ({db_label} {get_uri_local_name_plus(uri)})" \
                    if visualisation_obj is None else F"{label} ({db_label} {get_uri_local_name_plus(uri)})"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formatted_uri],
                    "uri": uri,
                    "group": dataset[i_dataset],
                    "size": "8" if visualisation_obj is None else "5"}

                # ADD THE NODE TO THE VISUALISATION OBJECT
                vis_data["nodes"].append(node_dict)

    else:

        index = hash_number(hasher(specs['cluster_id']))

        for rsc in specs["cluster_data"]["nodes"]:
            formatted_uri = to_nt_format(rsc)

            # DOCUMENTING THE RESOURCE LABELS.
            # THIS MAKES SURE NODE WITH ALTERNATIVE NAME DO NOT CAME MORE THAN ONCE
            if formatted_uri not in resources:

                # COLLECTING THE LIST OF CORROBORATED NODES
                if is_restructured is True and formatted_uri in root_reconciled:
                    sub_clusters_id.add(root_reconciled[formatted_uri])

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                label = F"-- {hasher(formatted_uri)}"
                resources[formatted_uri] = F"{label}"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formatted_uri],
                    "uri": rsc,
                    "group": index,
                    "size": "8" if visualisation_obj is None else "5"
                }

                vis_data["nodes"].append(node_dict)

    # --> 2. CREATE THE LINKS: THE NODE NETWORK OBJECT
    cluster_strengths = specs["cluster_data"]["strengths"]
    for source, target in specs["cluster_data"]["links"]:
        # print(source, target )
        # EXTRACTING THE LINK'S STRENGTH
        current_link = (source, target) if source < target else (target, source)
        key_1 = "key_{}".format(str(Ut.hasher(current_link)).replace("-", "N"))

        # GETTING THE MAXIMUM STRENGTH IS MORE STRENGTH IS COMPUTED FOR THE LINK
        strength = float(max(cluster_strengths[key_1]))
        # association = False
        link_dict = {
            "source": resources[to_nt_format(source)],
            "target": resources[to_nt_format(target)],
            "strength": F"{strength}",
            "distance": 150, "value": 4,
            "color": "black" if strength == 1 else "red",
            "dash": F"3,{20 * (1 - strength)}"
        }
        vis_data["links"].append(link_dict)

        # print(source, target)

    # IF THERE IS A SUBSET, RUN A RECURSIVE CALL BY CREATING
    # A NEW SPECIFICATION AND PROVIDE THE VISUALISATION OBJECT AS WELL
    sub_vis = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    }

    if len(sub_clusters_id) > 0:
        # ***************************************************************
        print(F"\n{tab}--> 4. THE MAIN CLUSTER HAS BEEN RESTRUCTURED")
        print("\t{:*^41}".format(F""))
        print("\t{:*^41}".format(F" GENERATING {len(sub_clusters_id)} SUB-CLUSTERS "))
        # ***************************************************************

        for temp_id in sub_clusters_id:
            temp = reconciled[temp_id]
            specifications = {

                "data_store": specs['data_store'],

                "cluster_id": id,

                # "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
                "associations": specs["associations"],

                "serialised": specs["serialised"],

                "cluster_data": {

                    "nodes": temp['nodes'] if temp else [],

                    'strengths': temp['strengths'] if temp else {},

                    "links": temp["links"] if temp else []
                },

                "properties": specs['properties']
            }

            plot_reconciliation(specifications, visualisation_obj=sub_vis, activated=activated)
            # cluster_vis_input_2(specifications, visualisation_obj=vis_data, activated=activated)

            add_vis_evidence(specifications, sub_vis, specs["sub_clusters"],
                             resources_obj=resources, dataset_obj=dataset, activated=activated)

    # --> 3. RETURNING THE VISUALISATION OBJECT FOR RENDERING
    # print_object(vis_data)
    if visualisation_obj is None:
        Ut.completed(start)

    return vis_data, sub_vis
    # return vis_data

    # RETURN FEEDBACK
    # else:
    #
    #     print('\n\tTHE QUERY DID NOT YIELD ANY RESULT...'
    #           '\n\tIF YOU ARE EXPECTING RESULTS, PLEASE CHECK THE AUTOMATED QUERY FOR FURTHER DEBUGGING.')
    #
    #     if len(specs["cluster_data"]["nodes"]) == 0:
    #         print('\tA QUICK CHECK SHOWS THAT THE CLUSTER HAS NO RESOURCE (NO NODES).')
    #
    # # IF THE INVESTIGATED CLUSTER EXTENDS, COLLECT ALL ILNS IT EXTENDS TO
    # # FOR EACH EXTENDED CLUSTER, ADD THE NODES
    # # FOR EACH EXTENDED CLUSTER, ADD THE LINKS
    # # ADD THE ASSOCIATION
    #
    # # LIST OF CLUSTERS THAT EXTEND
    #
    # # print_object(root_reconciled)
    # # print(type(root_reconciled))


# ****************************************************
"           COMPRESSED VISUALISATION                 "
# ****************************************************


def plot_compact(specs, vis=None, root=None, map_of_labels=None, sub_clusters=None, link_thickness=1,
                 investigated=True, color=None, decimal_size=5, desc=True, delta=None, activated=False):

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [improved_cluster_vis] IS NOT ACTIVATED.")
        return

    cluster = deepcopy(specs["cluster_data"])
    data_store = specs["data_store"]
    # USER SELECTED PROPERTIES
    properties = specs['properties']
    # DICTIONARY WITH A LIST OF STRENGTHS
    strengths = cluster["strengths"]
    # DICTIONARY OF COMPACT CLUSTERS
    compact = defaultdict(list)
    total = len(cluster['nodes'])
    total_links = len(cluster['nodes'])

    link_view, nodes_view = [], []
    added, link_checker = set(), set()
    aggregated, new_links = dict(), dict()
    group_map, sub_cluster_link_count = dict(), dict()
    new_root = root if root is not None else dict()
    label_map = map_of_labels if map_of_labels is not None else dict()
    new_clusters = sub_clusters if sub_clusters is not None else dict()

    def strength_classification(stop=0.5, delta_diff=0.1, decimal=5, reverse=True):

        range_list = []
        up = 1
        while True:
            down = up - delta_diff
            down = 0 if down < 0 else down
            range_list += intervals.openclosed(round(down, decimal), round(up, 5))
            if down <= stop:
                break
            up = up - delta_diff

        range_list = sorted(range_list, reverse=reverse)

        return range_list

    problem(tab="\t", text=F"MISSING LINKS: {total*(total-1)/2 -  len(strengths)}\n", label=" INFO ")
    print("\t--> THE CLUSTER IS OF {} NODES AND {}: {}".format(
        total, total_links, "INVESTIGATED" if investigated is True else "EVIDENCE"))
    # print_object(strengths)

    # ***********************************
    print("\n\t--> 1. GET THE MAXIMUM")
    # ***********************************
    for key, value in strengths.items():
        if isinstance(value, list) is False:
            problem(text="THE STRENGTH MUST BE A LIST")
            exit()
        strengths[key] = round(float(max(value)), decimal_size)
    # print_object(strengths, overview=False)

    if delta is not None and delta > 0:

        strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=False))
        classification = []

        # ******************************************************
        print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
        # ******************************************************
        for key, value in strengths.items():
            classification = strength_classification(stop=value, delta_diff=delta, decimal=decimal_size, reverse=desc)
            break

        # *******************************************
        print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
        # *******************************************
        for interval in classification:
            s = intervals.to_string(interval)
            if s not in aggregated:
                aggregated[s] = []

    else:

        # *****************************************************
        print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
        # *****************************************************
        strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=desc))

        # ****************************************
        print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
        # ****************************************
        for key, value in strengths.items():
            s = intervals.to_string(intervals.singleton(value))
            if s not in aggregated:
                aggregated[s] = []

    # USE THE AGGREGATED TO REORGANIZE THE LINKS
    def find_bin(search_strength, bin_input, delta_used, stop, reverse=True):
        # print(bin_input)
        # print(search_strength, delta_used, stop)
        index = (floor((1 - search_strength) / delta_used)) if reverse is True \
            else (floor((search_strength - stop) / delta_used)) + 1
        # print(bin_input[index])
        return bin_input[index]

    # LIST OF ALL BINS
    bins_list = list(aggregated.keys())
    bin_end = intervals.from_string(bins_list[0], conv=float).lower if desc is False \
        else intervals.from_string(bins_list[0], conv=float).upper
    # print_object(bins_list)

    # DICTIONARY OF LINKS ORGANISED PER BINS
    grouped_links = dict()

    # INITIALISE THE BINS IN WHICH THE LINKS CAN B E ORGANISED
    for bin_key in aggregated:
        grouped_links[bin_key] = set()

    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # (BOTTLENECK SOLUTION-1)
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # ORGANISE THE LINKS IN THE BINS
    for source, target in cluster["links"]:

        # GET THE KEY OF THE CURRENT LINK
        link_key = get_key(source, target)

        # GET THE STRENGTH OF THE CURRENT LINK
        link_strength = strengths[link_key]

        # FIND THE BIN FOR THE CURRENT LINK BASED ON ITS STRENGTH
        bin_key = find_bin(
                search_strength=link_strength, bin_input=bins_list, delta_used=delta, stop=bin_end, reverse=desc) \
            if delta is not None and delta > 0 else intervals.to_string(intervals.singleton(link_strength))

        # APPEND THE LINK TO THE BIN STACK
        grouped_links[bin_key].add((source, target))

    # print_object(list(grouped_links.keys()), overview=False)
    # print_object(grouped_links, overview=False)
    # print_object(aggregated, overview=False)

    print(F"\t\t   >>> {len(aggregated)} POSSIBLE SUB-GROUPS FOUND BASED ON STRENGTH.")
    print("\t\t   >>> THE CLASSIFICATION IS {} .".format(" | ".join(str(x) for x in aggregated.keys())))

    # ************************************************************
    # ************************************************************
    print("\n\t--> 4. FIND NEW SUB-CLUSTERS AT EACH ITERATION. "
          "THIS ASSUMES THAT THE DICTIONARY IS SORTED IN REVERSE")
    # AT THE END OF THIS, WE HAVE ALL
    # SUB-CLUSTERS BASED ON AGGREGATED STRENGTHS
    # ************************************************************
    # ************************************************************
    step_4 = time.time()
    for constraint_key in aggregated.keys():

        # ITERATING THROUGH THE LINKS
        print(F"\t\tBIN {constraint_key:17}")

        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # (BOTTLENECK PROBLEM-1)
        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        # for source, target in cluster["links"]:
        for source, target in grouped_links[constraint_key]:

            # GET THE KEY OF THE CURRENT LINK
            link_key = get_key(source, target)

            # GET THE STRENGTH OF THE CURRENT LINK
            link_strength = strengths[link_key]

            # WE ARE INTERESTED IN FINDING NODES OF THE CURRENT GROUP
            # print(link_strength, constraint_key)
            if link_strength not in intervals.from_string(constraint_key, conv=float):
                continue

            # LOOKING FOR NODES THAT CAN BE GROUPED-IN WITH THE CURRENT STRENGTH
            src_pos, trg_pos = None, None

            # GROUP OF THE CURRENT STRENGTH.
            groups = aggregated[constraint_key]

            # LOOK FOR A GROUP THAT HAS THE SOURCE OR TARGET
            for i in range(0, len(groups)):
                if source in groups[i]:
                    src_pos = i
                if target in groups[i]:
                    trg_pos = i
                if src_pos is not None and trg_pos is not None:
                    break

            # print(constraint_key, source, target)
            # print(src_pos, trg_pos)

            # FILL AGGREGATED WITH THE NEW SUB-CLUSTERS
            # SAVING THE NODE IN THE CORRECT GROUP
            if src_pos == trg_pos is None:

                if source not in added and target not in added:
                    aggregated[constraint_key] += [{source, target}]
                    added.add(source)
                    added.add(target)

                elif source not in added and target in added:
                    aggregated[constraint_key] += [{source}]
                    added.add(source)

                elif source in added and target not in added:
                    aggregated[constraint_key] += [{target}]
                    added.add(target)

            elif src_pos is not None and trg_pos is None:

                # if source not in added:
                #     aggregated[link_strength][src_pos].add(source)
                #     added.add(source)

                if target not in added:
                    aggregated[constraint_key][src_pos].add(target)
                    added.add(target)

            elif src_pos is None and trg_pos is not None:

                if source not in added:
                    aggregated[constraint_key][trg_pos].add(source)
                    added.add(source)
                # if target not in added:
                #     aggregated[link_strength][trg_pos].add(target)
                #     added.add(target)

            elif src_pos is not None and trg_pos is not None and src_pos != trg_pos:

                if len(aggregated[constraint_key][src_pos]) > len(aggregated[constraint_key][trg_pos]):
                    big = aggregated[constraint_key][src_pos]
                    small = aggregated[constraint_key][trg_pos]
                    for item in small:
                        big.add(item)
                    aggregated[constraint_key].__delitem__(trg_pos)

                else:
                    small = aggregated[constraint_key][src_pos]
                    big = aggregated[constraint_key][trg_pos]
                    for item in small:
                        big.add(item)
                    aggregated[constraint_key].__delitem__(src_pos)
    print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_4)}")
    # print_object(aggregated, overview=False)

    # ************************************************************
    print("\n\t--> 5. CREATING "
          "\n\t\t5.1 SUB-CLUSTERS "
          "\n\t\t5.2 NUMBER OF LINKS WITHIN SUB-CLUSTERS "
          "\n\t\t5.3 LINKS ACROSS SUB-GROUPS")
    # ************************************************************
    count_bins = 0
    bins_total = len(aggregated)
    step_5 = time.time()
    for key, groups in aggregated.items():

        count_bins += 1
        made = F'IS MADE OF {len(groups)} GROUPS'
        print(F"\t\t\t{count_bins} / {bins_total} BIN {key:7} {made:17} AND {len(grouped_links[key])} LINKS")
        # FOR EACH GROUP OF THE SAME STRENGTH
        for group in groups:

            # GENERATE THE ID OF THIS GROUP BASED ON THE SMALLEST NODE STRING
            smallest = None
            for resource in group:
                if smallest is None:
                    smallest = resource
                elif smallest > resource:
                    smallest = resource
            # print("smallest", smallest)
            group_id = hasher(smallest)

            # *****************************
            # 5.1 RECONSTRUCT THE CLUSTER
            # *****************************
            new_clusters[group_id] = group

            # 5.2 DOCUMENT THE ALL MAP
            group_map[group_id] = key

            # **************************
            # 5.3 GENERATE THE ROOT MAP
            # **************************
            for resource in group:
                new_root[resource] = group_id

            # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            # ITERATING THROUGH THE LINKS (BOTTLENECK-2)
            # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            # for source, target in cluster["links"]:
            # for source, target in grouped_links[key]:
            copy = deepcopy(grouped_links[key])
            for source, target in copy:

                # ****************************************
                #  5.4 FIND LINKS ACROSS SUB CLUSTERS
                # ****************************************
                # link_key = get_key(source, target)
                # if (source not in group and target in group) or (source in group and target not in group):
                #     if link_key not in new_links:
                #         new_links[link_key] = source, target, strengths[link_key]

                # ******************************************************
                # 5.5 COUNT THE NUMBER OFF LINKS WITHIN EACH SUB-CLUSTER
                # ******************************************************
                if (source != target) and (source in group and target in group):

                    if group_id not in sub_cluster_link_count:
                        sub_cluster_link_count[group_id] = 1
                    else:
                        sub_cluster_link_count[group_id] += 1

                    # REMOVE LINKS FOUND
                    grouped_links[key].remove((source, target))

                    # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                    if len(group) > 2:
                            compact[group_id].append((source, target, strengths[get_key(source, target)]))

    for key, groups in aggregated.items():
        for group in groups:
            copy = deepcopy(grouped_links)
            for bin_key, value in copy.items():

                if intervals.from_string(bin_key, float) < intervals.from_string(key, float):
                    for source, target in value:

                        # ****************************************
                        #  5.4 FIND LINKS ACROSS SUB CLUSTERS
                        # ****************************************
                        link_key = get_key(source, target)
                        if (source not in group and target in group) or (source in group and target not in group):
                            if link_key not in new_links:
                                new_links[link_key] = source, target, strengths[link_key]

                            # REMNOVE LINKS FOUND
                            grouped_links[bin_key].remove((source, target))

    print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_5)}")
    # print_object(new_clusters, overview=False)
    # print_object(new_links, overview=False)
    # print_object(group_map, overview=False)
    # print_object(new_root, overview=False)

    # *****************************************************************
    print("\n\t--> 6. FETCH LABELS AND GENERATE VISUALISATION NODES")
    # *****************************************************************

    properties_converted = convert_properties(properties) if properties is not None else None
    step_6 = time.time()

    for key, sub_cluster in new_clusters.items():

        # ************************************
        # 6.1 GET A LABEL FOR THE SUB-CLUSTER
        # ************************************
        # result = None
        resource = list(sub_cluster)[0]
        # print_object(resource, overview=False)
        # QUERY FOR FETCHING THE LABEL
        query = Middleware.node_labels_switcher[data_store](
            resources=[resource], targets=properties_converted)

        # FETCHING THE LABELS
        table = None
        if data_store in Middleware.run_query_matrix_switcher and query:
            result = Middleware.run_query_matrix_switcher[data_store](query)
            # Stardog.display_matrix(result, spacing=130, is_activated=True)
            table = result[St.result] if isinstance(result, dict) else result

        if properties_converted is not None and table is not None:
            db_label = get_uri_local_name_plus(table[1][1])
            underscore = db_label.split("__")
            db_label = underscore[1] if len(underscore) > 1 else db_label
            label = F"-- {table[1][3]} ({db_label})"
        else:
            # label = F"-- ({resource})"
            # label = F"-- {get_uri_local_name_plus(resource)}"
            label = F"-- {resource}"

        # MAP THE LABEL TO THE SUB-CLUSTER
        label_map[key] = label

        # ****************************************
        # 6.2 GENERATE THE NODES FOR VISUALISATION
        # ****************************************
        group_size = len(sub_cluster)
        possible = group_size * (group_size - 1) / 2
        missing_links = (possible - sub_cluster_link_count[key]) / float(possible) \
            if key in sub_cluster_link_count else 0

        if key in group_map:
            node = {
                'nodes': group_size,
                'strength': group_map[key],
                'size': 10,
                'missing_links': missing_links,
                'group': color,
                'id': label_map[key],
                'investigated': str(investigated).lower()
            }
            node['group'] = 1 if group_size == 1 else int((hash_number(key)) if color is None else int(color))

            # if node['group'] > 1:
            #     print("\t\t --> COMMUNITY COLOR",  node['group'])
            nodes_view += [node]

            if node['missing_links'] < 0:
                print(sub_cluster_link_count[key])
                print("possible:", possible)
                print("group_size:", group_size)
                print("sub_cluster_link_count", sub_cluster_link_count[key])
    print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_6)}")
    # print_object(nodes_view, overview=False)

    # ***************************************************
    print('\t--> 7. GENERATE VISUALISATION LINKS')
    # ***************************************************
    link_count = dict()
    step_7 = time.time()
    for key, link in new_links.items():

        # [link[0]]     -> RETURNS THE RESOURCE
        # [new_root]    -> RETURNS THE SUB-CLUSTER THO WITCH THE RESOURCE BELONGS TO
        # [label_map]   -> RETURNS THE LABEL OF SUB-CLUSTER
        # print_object(new_root)
        label_1 = label_map[new_root[link[0]]]
        label_2 = label_map[new_root[link[1]]]
        strength = link[2]
        distance = 150

        # ORDERING THE LABELS
        if label_1 < label_2:
            source, target = label_1, label_2
            dist_factor = [len(new_clusters[new_root[link[0]]]), len(new_clusters[new_root[link[1]]])]
        else:
            source, target = label_2, label_1
            dist_factor = [len(new_clusters[new_root[link[1]]]), len(new_clusters[new_root[link[0]]])]

        # GENERATE THE KEY
        labels = F"{source}-{target}"

        if labels not in link_count:
            link_count[labels] = 1
        else:
            link_count[labels] += 1

        current = {
            'source': source,
            'target': target,
            "dash": F"3,{20 * (1 - float(strength))}",
            'distance': distance,
            'color': 'red' if float(strength) < 1 else "black",
            'value': 4,
            'strength': strength,
            'dist_factor': dist_factor,
        }

        if labels not in link_checker:
            link_view += [current]
            link_checker.add(labels)
        else:
            # print(labels)
            for dictionary in link_view:
                curr_label = F"{dictionary['source']}-{dictionary['target']}"
                if labels == curr_label:
                    dictionary['strength'] = max(dictionary['strength'], current['strength'])
                    break

    # UPDATING THE THICKNESS OF GHE LINKS
    for link in link_view:
        link['value'] = link_count[F"{link['source']}-{link['target']}"] * link_thickness

    # VISUALISATION OBJECT
    if vis is None:
        vis = {
            "id": specs["cluster_id"],
            "confidence": 1,
            "decision": 1,
            "metric": "e_Q MESSAGE",
            "messageConf": "",
            'links': link_view,
            'nodes': nodes_view
        }
    else:

        vis['links'] += link_view
        vis['nodes'] += nodes_view

    print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_7)}")
    # print_object(vis, overview=False)
    # print_object(nodes_view, overview=False)
    # print_object(link_view, overview=False)
    # print_object(aggregated, overview=False)
    # print_object(link_count, overview=False)
    # print_object(label_map, overview=False)

    # with open('C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code\data_new_vis.json', mode='w') as file:
    #     json.dump(vis, file)

    return vis, compact


def plot_compact_child(children):

    # THIS FUNCTION COMPLEMENTS PLOT COMPACT AS IT PLOTS
    # THE COMPACT GROUPS FOUND BY THE PLOT COMPACT FUNCTION

    host = "http://localhost:63342/LenticularLens/src/LLData/Validation/{}"
    from src.LLData.Validation import CLUSTER_VISUALISATION_DIR
    import webbrowser as web
    visualisation_obj = None
    investigated = True

    for key, child in children.items():

        vis_data = {
            "id": key,
            "confidence": 1,
            "decision": 1,
            "metric": "e_Q MESSAGE",
            "messageConf": "",
            "nodes": [],
            "links": []
        }

        nodes = set()

        for link in child:
            # GETTING THE MAXIMUM STRENGTH IS MORE STRENGTH IS COMPUTED FOR THE LINK
            association = False
            nodes.add(link[0])
            nodes.add(link[1])
            link_dict = {
                "source": link[0],
                "target": link[1],
                "strength": link[2],
                "distance": 250 if association is True else 150, "value": 4,
                "color": "purple" if association is True else("black" if link[2] == 1 else "red"),
                "dash": "20,10,5,5,5,10" if association is True else F"3,{20 * (1 - link[2])}"
            }
            vis_data["links"].append(link_dict)

        # CREATE THE NODE OBJECT FOR VISUALISATION
        for node in list(nodes):
            node_dict = {
                'id': node,
                "uri": node,
                "group": hash_number(key),
                "size": "8" if visualisation_obj is None else "5"
            }

            if investigated is True:
                node_dict['investigated'] = str(investigated).lower()
                node_dict["size"] = 8

            vis_data["nodes"].append(node_dict)

        with open(join(CLUSTER_VISUALISATION_DIR, "data_compact.json"), mode='w') as compact_file:
            json.dump(vis_data, compact_file)
        web.open_new_tab(host.format('Compact_vis.html'))
        time.sleep(3)


# ****************************************************
"      COMPRESSED VISUALISATION WITH EVIDENCE        "
# ****************************************************


def plot_compact_association(specs, reduce_investigated=False, activated=False):

    # ***************************************************************
    # --> 1 and 2. THIS FIRST PART DEALS WITH ASSOCIATIONS. FROM THE
    # PROVIDED ASSOCIATION CSV FILE, THE CODE EXTRACTS THE NODES OF
    # THE CURRENT CLUSTER THAT EXTEND THE CLUSTER WITH NEW CLUSTERS
    # ***************************************************************

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [compact_association_vis] IS NOT ACTIVATED.")
        return

    total = 0
    color = 0
    label_map = dict()
    overall_root = dict()
    sub_clusters = dict()

    specs = deepcopy(specs)

    # THE PAIRED NODES WILL ALLOW TO FETCH THE CLUSTER THAT EXTEND THE CURRENT CLUSTER
    paired_nodes = set()

    # BOOK KEEPING OF THE NODES IN THE CLUSTER
    # resources = {}

    # CONVERTING THE NODES TO A SET FOR GENERATING NODE DE-DUPLICATION
    overall_nodes = set(specs["cluster_data"]["nodes"])

    # THE DICTIONARY TO RETURN FOR VISUALISATION
    vis = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    }

    # ****************************************************************************************
    print(F"\n\t--> 1.  COMPACTING THE INVESTIGATED CLUSTER FETCHING THE ASSOCIATED NODES ")
    # ****************************************************************************************
    if reduce_investigated is True:
        ""
        plot_compact(
            specs, vis=vis, root=overall_root, map_of_labels=label_map, sub_clusters=sub_clusters,
            link_thickness=1, investigated=True, color=color, activated=True)

    else:
        # REMOVE THE ASSOCIATION CSV FILE
        association_csv = specs.pop("associations")

        vis = plot(specs, resources_obj=label_map, sub_clusters=sub_clusters, root=overall_root, activated=True)

        # ADD THE ASSOCIATION CSV FILE BACK
        specs['associations'] = association_csv

    total += 1

    # ***************************************************************
    print(F"\n\t--> 2. FETCHING THE ASSOCIATED NODES ")
    # ***************************************************************

    with open(join(CSV_ASSOCIATIONS_DIR, specs['associations']), 'r') as file:

        # LOOK FOR THE NODES IN ASSOCIATION
        associations = find_associations(specs['cluster_data']['nodes'], file.read())

        # ADD THE ASSOCIATION NODES TO THE OVERALL NODES TO PLOT
        for link in associations:

            src = to_nt_format(link[0])
            trg = to_nt_format(link[1])

            if src not in overall_nodes:
                paired_nodes.add(src)

            if trg not in overall_nodes:
                paired_nodes.add(trg)
    # print_object(paired_nodes)

    # ***************************************************************
    print(F"\n\t--> 3. FETCHING THE ASSOCIATED CLUSTERS ")
    # ***************************************************************

    # COLLECTS THE CLUSTER ID OF THE CLUSTERS THAT EXTEND THE CURRENT CLUSTER
    extended = set()

    # THE MAPPING OBJECT THAT DOCUMENT THE MAPPING BETWEEN NODE AND CLUSTER THEY BELONG TO
    root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-2.txt")

    # THE DICTIONARY OF THE CLUSTERS
    clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-1.txt")

    for paired in paired_nodes:
        extended.add(root[to_nt_format(paired)])

    print(F"\tTHE CLUSTERS EXTENDS TO {len(extended)} OTHER CLUSTER(S)")
    # print_object(label_map, overview=False)
    # RUN A RECURSIVE CODE BASED ON THE NEW CLUSTERS (EXTENDED CLUSTERS) FOUND
    for evidence_id in extended:
        ext_cluster = clusters[evidence_id]
        ext_specifications = {

            "data_store": "STARDOG",
            "cluster_id": evidence_id,
            "cluster_data": {
                "nodes": ext_cluster['nodes'] if ext_cluster else [],
                'strengths': ext_cluster['strengths'] if ext_cluster else {},
                "links": ext_cluster["links"] if ext_cluster else []
            },
            "properties": specs['properties']
        }

        # RECURSIVE CALL
        color += 1
        plot_compact(
            ext_specifications, vis=vis, root=overall_root, map_of_labels=label_map,
            sub_clusters=sub_clusters, link_thickness=1, investigated=False, color=color, activated=True)

        print(F"\n\t\t>>> OVERALL NODE COUNT {len(overall_root)}")

    problem(tab="\t", label=" STATISTICS ",
            text=F"\n\t\t>>> INVESTIGATED CLUSTER OF SIZE {len(overall_nodes)} WITH AND OVERALL EVIDENCE {color}")

    # ****************************************************
    print(F"\n\t--> 4. ADDING THE ASSOCIATION LINKS")
    # ****************************************************
    # ***************************************************
    # print_object(overall_root, overview=False)
    # print_object(label_map, overview=False)
    # print_object(sub_clusters, overview=False)

    if associations is not None and len(label_map) > 0:

        print(F"\n\t--> ASSOCIATED: {len(associations)}")
        ass_thickness = dict()
        for link in associations:

            try:
                input_1 = overall_root[to_nt_format(link[0])]
            except KeyError:
                input_1 = to_nt_format(link[0]).split("-")[0]

            try:
                input_2 = overall_root[to_nt_format(link[1])]
            except KeyError:
                input_2 = to_nt_format(link[1]).split("-")[0]

            size_1 = len(sub_clusters[input_1]) if input_1 in sub_clusters else len(overall_nodes)
            size_2 = len(sub_clusters[input_2]) if input_2 in sub_clusters else len(overall_nodes)

            label_1 = label_map[input_1]
            label_2 = label_map[input_2]

            if label_1 < label_2:
                source, target = label_1, label_2

                if reduce_investigated is True:
                    dist_factor = [
                        len(sub_clusters[input_1]),
                        len(sub_clusters[input_2])]
                else:
                    dist_factor = [size_1, size_2]
            else:
                source, target = label_2, label_1
                if reduce_investigated is True:
                    dist_factor = [
                        len(sub_clusters[input_2]),
                        len(sub_clusters[input_1])]

                else:
                    dist_factor = [size_2, size_1]

            label_key = F"{source}-{target}"
            if label_key not in ass_thickness:
                ass_thickness[label_key] = 1
                print("\t\t" + label_key)
                link_dict = {
                    "source": source,
                    "target": target,
                    "distance": 250,
                    "value": 1,
                    "color": "purple",
                    "dash": "20,10,5,5,5,10",
                    'dist_factor': dist_factor
                }
                vis["links"] += [link_dict]
                # print_object(link_dict)

            # INCREMENTING THE THICKNESS
            else:
                ass_thickness[label_key] += 10
                for curr_link in vis["links"]:
                    curr_key = F"{curr_link['source']}-{curr_link['target']}"
                    if curr_key == label_key:
                        curr_link["value"] = ass_thickness[label_key]
                        print(F"\t\t{curr_key}\tINCREMENTED!!!")
                        break

            # print_object(link_dict, overview=False)

    # print("\n\t--> label_map", len(label_map))
    # print_object(overall_root, overview=False)
    # with open('C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code\data_new_vis.json', mode='w') as file:
    #     json.dump(vis, file)

    return vis


# ******************************************************
" COMPRESSED VISUALISATION OF RECONCILED WITH EVIDENCE "
# ******************************************************


def plot_compact_association_rec(specs, reduce_investigated=False, activated=False):

    # ***************************************************************
    # --> 1 and 2. THIS FIRST PART DEALS WITH ASSOCIATIONS. FROM THE
    # PROVIDED ASSOCIATION CSV FILE, THE CODE EXTRACTS THE NODES OF
    # THE CURRENT CLUSTER THAT EXTEND THE CLUSTER WITH NEW CLUSTERS
    # ***************************************************************

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [compact_association_vis] IS NOT ACTIVATED.")
        return

    specs = deepcopy(specs)

    total = 0
    color = 0
    label_map = dict()
    overall_root = dict()
    sub_clusters = dict()

    # THE PAIRED NODES WILL ALLOW TO FETCH THE CLUSTER THAT EXTEND THE CURRENT CLUSTER
    paired_nodes = set()

    # BOOK KEEPING OF THE NODES IN THE CLUSTER
    # resources = {}

    # THE DICTIONARY TO RETURN FOR VISUALISATION
    vis = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    }

    # THE SET OF ALL INDEPENDENT RECONCILED SUB CLUSTERS
    sub_clusters_id = set()

    # LOADING THE CLUSTERS AND THE MAPPING OF NODES TO CLUSTER ID
    reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt")
    root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt")

    # CONVERTING THE NODES TO A SET FOR GENERATING NODE DE-DUPLICATION
    overall_nodes = set()
    for node in specs["cluster_data"]["nodes"]:
        if node in root_reconciled:
            overall_nodes.add(node)

    for node in specs["cluster_data"]["nodes"]:
        formatted_uri = to_nt_format(node)
        # COLLECTING THE LIST OF CORROBORATED NODES
        if formatted_uri in root_reconciled:
            sub_clusters_id.add(root_reconciled[formatted_uri])

    # COMPACTING ASSOCIATED CLUSTERS
    if reduce_investigated is True:

        for temp_id in sub_clusters_id:
            color += 1
            temp = reconciled[temp_id]
            specifications = {
                "data_store": specs['data_store'],
                "cluster_id": temp_id,
                "associations": specs["associations"],
                "serialised": specs["sub_clusters"],
                "cluster_data": {
                    "nodes": temp['nodes'] if temp else [],
                    'strengths': temp['strengths'] if temp else {},
                    "links": temp["links"] if temp else []},
                "properties": specs['properties']
            }

            vis = plot_compact(
                specifications, vis=vis, root=overall_root, map_of_labels=label_map, sub_clusters=sub_clusters,
                link_thickness=1, investigated=True, color=color, activated=True)

    else:

        for temp_id in sub_clusters_id:

            print(f">>> SIZE OF THE RECONCILED [{len(sub_clusters_id)}]")
            color += 1
            temp = reconciled[temp_id]
            specifications = {
                "data_store": specs['data_store'],
                "cluster_id": temp_id,
                "associations": specs["associations"],
                "serialised": specs["sub_clusters"],
                "cluster_data": {
                    "nodes": temp['nodes'] if temp else [],
                    'strengths': temp['strengths'] if temp else {},
                    "links": temp["links"] if temp else []},
                "properties": specs['properties']
            }

            # REMOVE THE ASSOCIATION CSV FILE
            association_csv = specifications.pop("associations")

            vis = plot(specifications, visualisation_obj=vis, resources_obj=label_map,
                       sub_clusters=sub_clusters, root=overall_root, investigated=True, activated=True)

            # ADD THE ASSOCIATION CSV FILE BACK
            specs['associations'] = association_csv

    total += 1

    # ***************************************************************
    print(F"\n\t--> FETCHING THE ASSOCIATED NODES ")
    # ***************************************************************
    with open(join(CSV_ASSOCIATIONS_DIR, specs['associations']), 'r') as file:

        # LOOK FOR THE NODES IN ASSOCIATION
        associations = find_associations(list(overall_nodes), file.read())

        # ADD THE ASSOCIATION NODES TO THE OVERALL NODES TO PLOT
        for link in associations:

            src = to_nt_format(link[0])
            trg = to_nt_format(link[1])

            if src not in overall_nodes:
                paired_nodes.add(src)

            if trg not in overall_nodes:
                paired_nodes.add(trg)
    # print_object(paired_nodes)

    # ***************************************************************
    print(F"\n\t--> FETCHING THE ASSOCIATED CLUSTERS ")
    # ***************************************************************

    # COLLECTS THE CLUSTER ID OF THE CLUSTERS THAT EXTEND THE CURRENT CLUSTER
    extended = set()

    # THE MAPPING OBJECT THAT DOCUMENT THE MAPPING BETWEEN NODE AND CLUSTER THEY BELONG TO
    root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['sub_clusters']}-2.txt")

    # THE DICTIONARY OF THE CLUSTERS
    clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['sub_clusters']}-1.txt")

    for paired in paired_nodes:
        formatted = to_nt_format(paired)
        if formatted in root:
            extended.add(root[to_nt_format(paired)])

    print(F"\tTHE CLUSTERS EXTENDS TO {len(extended)} OTHER CLUSTER(S)")
    # print_object(label_map, overview=False)
    # RUN A RECURSIVE CODE BASED ON THE NEW CLUSTERS (EXTENDED CLUSTERS) FOUND
    for evidence_id in extended:
        ext_cluster = clusters[evidence_id]
        ext_specifications = {

            "data_store": "STARDOG",
            "cluster_id": evidence_id,
            "cluster_data": {
                "nodes": ext_cluster['nodes'] if ext_cluster else [],
                'strengths': ext_cluster['strengths'] if ext_cluster else {},
                "links": ext_cluster["links"] if ext_cluster else []
            },
            "properties": specs['properties']
        }

        # RECURSIVE CALL
        color += 1
        plot_compact(
            ext_specifications, vis=vis, root=overall_root, map_of_labels=label_map,
            sub_clusters=sub_clusters, link_thickness=1, investigated=False, color=color, activated=True)

        print(F"\n\t\t>>> OVERALL NODE COUNT {len(overall_root)}")

    problem(tab="\t", label=" STATISTICS ",
            text=F"\n\t\t>>> INVESTIGATED CLUSTER OF SIZE {len(overall_nodes)} WITH AND OVERALL EVIDENCE {color}")

    # ****************************************************
    # # ADDING THE ASSOCIATION LINKS
    # ****************************************************
    # ***************************************************
    # print_object(overall_root, overview=False)
    # print_object(label_map, overview=False)
    # print_object(sub_clusters, overview=False)
    if associations is not None and len(label_map) > 0:

        print(F"\n\t--> ASSOCIATED: {len(associations)}")
        ass_thickness = dict()
        for link in associations:

            try:
                input_1 = overall_root[to_nt_format(link[0])]
            except KeyError:
                input_1 = to_nt_format(link[0]).split("-")[0]

            try:
                input_2 = overall_root[to_nt_format(link[1])]
            except KeyError:
                input_2 = to_nt_format(link[1]).split("-")[0]

            size_1 = len(sub_clusters[input_1]) if input_1 in sub_clusters else len(overall_nodes)
            size_2 = len(sub_clusters[input_2]) if input_2 in sub_clusters else len(overall_nodes)

            if input_1 in label_map and input_2 in label_map:

                label_1 = label_map[input_1]
                label_2 = label_map[input_2]

                if label_1 < label_2:
                    source, target = label_1, label_2

                    if reduce_investigated is True:
                        dist_factor = [
                            len(sub_clusters[input_1]),
                            len(sub_clusters[input_2])]
                    else:
                        dist_factor = [size_1, size_2]
                else:
                    source, target = label_2, label_1
                    if reduce_investigated is True:
                        dist_factor = [
                            len(sub_clusters[input_2]),
                            len(sub_clusters[input_1])]

                    else:
                        dist_factor = [size_2, size_1]

                label_key = F"{source}-{target}"
                if label_key not in ass_thickness:
                    ass_thickness[label_key] = 1
                    print("\t\t" + label_key)
                    link_dict = {
                        "source": source,
                        "target": target,
                        "distance": 250,
                        "value": 1,
                        "color": "purple",
                        "dash": "20,10,5,5,5,10",
                        'dist_factor': dist_factor
                    }
                    vis["links"] += [link_dict]
                    # print_object(link_dict)

                # INCREMENTING THE THICKNESS
                else:
                    ass_thickness[label_key] += 10
                    for curr_link in vis["links"]:
                        curr_key = F"{curr_link['source']}-{curr_link['target']}".format()
                        if curr_key == label_key:
                            curr_link["value"] = ass_thickness[label_key]
                            print(F"\t\t{curr_key}\tINCREMENTED!!!")
                            break

            # print_object(link_dict, overview=False)

    # print("\n\t--> label_map", len(label_map))

    # print_object(overall_root, overview=False)

    # with open(join(CLUSTER_VISUALISATION_DIR, "data_new_vis.json.json"), mode='w') as file:
    #     json.dump(vis, file)

    return vis


def get_reconciled(specs, desc=True, activated=True):

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [get_reconciled] IS NOT ACTIVATED.")
        return

    specs = deepcopy(specs)

    # THE SET OF ALL INDEPENDENT RECONCILED SUB CLUSTERS
    sub_clusters_id = set()

    # LOADING THE CLUSTERS AND THE MAPPING OF NODES TO CLUSTER ID
    reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt")
    root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt")

    for node in specs["cluster_data"]["nodes"]:
        formatted_uri = to_nt_format(node)
        # COLLECTING THE LIST OF CORROBORATED NODES
        if formatted_uri in root_reconciled:
            sub_clusters_id.add(root_reconciled[formatted_uri])

    # ***************************************************************
    print("\n--> 1. THE MAIN CLUSTER HAS BEEN RESTRUCTURED")
    print("\t{:*^41}".format(F""))
    print("\t{:*^41}".format(F" GENERATING {len(sub_clusters_id)} SUB-CLUSTERS "))
    # ***************************************************************

    # print_object(sub_clusters_id, overview=False)

    vis = {
        "id": specs["cluster_id"],
        "confidence": 1,
        "decision": 1,
        "metric": "e_Q MESSAGE",
        "messageConf": "",
        "nodes": [],
        "links": []
    }
    root, map_of_labels, sub_clusters, color = {}, {}, {}, 0

    for sub_id in sub_clusters_id:
        color += 1
        temp = reconciled[sub_id]
        specifications = {
            "data_store": specs['data_store'],
            "cluster_id": sub_id,
            "associations": specs["associations"],
            "serialised": specs["sub_clusters"],
            "cluster_data": {
                "nodes": temp['nodes'] if temp else [],
                'strengths': temp['strengths'] if temp else {},
                "links": temp["links"] if temp else []},
            "properties": specs['properties']
        }
        # print_object(specifications, overview=False)
        vis = plot_compact(
            specifications, vis=vis, root=root, map_of_labels=map_of_labels,
            sub_clusters=sub_clusters, link_thickness=1, investigated=True,
            color=color, decimal_size=5, desc=desc, delta=None, activated=activated)

        # print_object(vis, overview=False)
        # with open('C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code\data_new_vis.json', mode='w') as file:
        #     json.dump(vis, file)
        # break

    return vis


# ****************************************************
# ****************************************************
"   PLOT STATISTICS: HISTOGRAM OF THE DISTRIBUTION   "
# ****************************************************
# ****************************************************


def ilns_distribution(serialisation_dir, name, frequency=False,
                      label="ILNs DISTRIBUTION", print_latex=False, xmax=None, activated=False):

    # print(serialisation_dir)
    # print(name)
    # print(label)
    # print(print_latex)
    # print(xmax)
    # print(activated)

    if activated is False:
        problem(text="--> THE FUNCTION [ilns_distribution] IS NOT ACTIVATED.")
        return

    """
    :param serialisation_dir: THE DIRECTORY OF THE SERIALISED FILE
    :param serialized_cluster_name: THE NAME OF THE SERIALISED FILE WITHOUT EXTENSION AND WITHOUT NUMBER
    :param label: THE LABEL OF THE GRAPH FOR LATEX REFERENCE
    :param print_latex: BOOLEAN VALUE FOR PRINTING THE LATEX HISTOGRAM ONTO THE CONSOLE
    :param xmax: THE MAXIMUM X AXIS VALUE FOR THE HISTOGRAM
    :return:
    """

    print("{:.^100}".format(' LINK DISTRIBUTION '))
    print("{:.^100}".format(' ********** '))

    label = label.replace(" ", "_")
    count = 0
    hist = ""
    total = 0
    first, second, stat_up, stat_down = 0, 0, 0, 0

    accumulated = 0
    count_20 = 0
    x_max = 0
    x_95 = 0
    y_95 = 0

    distribution = {}

    if frequency is False:

        # LOAD SERIALISED CLUSTER OBJECT
        ilns = pickle_deserializer(serialisation_dir, name)

        # COMPUTE THE FREQUENCY
        for c_id, cluster in ilns['clusters'].items():
            size = len(cluster['nodes'])
            if size not in distribution:
                distribution[size] = 1
            else:
                distribution[size] += 1

        for key in sorted(distribution.keys()):

            # COUNT CLUSTER BELOW 31
            if key < 31:
                first += distribution[key]
            else:
                second += distribution[key]

            total += distribution[key]

            # BUILDING THE HISTOGRAM FOR LATEX
            if count == 0:
                hist += F'\n\t\t({key}, {distribution[key]})'
            elif count % 5 == 0:
                hist += F'\n\t\t({key}, {distribution[key]})'
            else:
                hist += F'\t\t({key}, {distribution[key]})'

            count += 1

        for key in sorted(distribution.keys()):
            if round(((accumulated / float(total)) * 100), 2) < 95:
                accumulated += distribution[key]
                x_95 = key
                y_95 = 3 * distribution[key]
            else:
                count_20 += 1
                if count_20 > 16:
                    break
            x_max = key

        if xmax is None:
            xmax = x_max

    else:
        threshold = 31
        # LOAD THE FREQUENCY
        distribution = pickle_deserializer(serialisation_dir, name)

        for key in sorted(distribution.keys()):

            total += len(distribution[key])

            # COUNT CLUSTER BELOW 31
            if key < threshold:
                first += len(distribution[key])
            else:
                second += len(distribution[key])

            # BUILDING THE HISTOGRAM FOR LATEX
            if count == 0:
                hist += F'\n\t\t({key}, {len(distribution[key])})'
            elif count % 5 == 0:
                hist += F'\n\t\t({key}, {len(distribution[key])})'
            else:
                hist += F'\t\t({key}, {len(distribution[key])})'

            count += 1
            if count == xmax:
                break

        for key in sorted(distribution.keys()):

            if round(((accumulated / float(total)) * 100), 2) < 95:
                accumulated += len(distribution[key])
                x_95 = key
                y_95 = len(distribution[key])

            else:
                count_20 += 1
                if count_20 > 16:
                    break
            x_max = key

        if xmax is None:
            xmax = x_max

    hist = F"""
    \\begin{{figure}}[ht]
    \pgfplotsset{{width=12cm, height=3.5cm}}
    \\begin{{tikzpicture}}
    \\begin{{axis}}[
      title=Identity-Link-Networks using approximate name similarity,
      axis lines = left,                xmax={xmax},
      ybar interval,                    ybar interval=0.8,
      ylabel=Number of ILNs,            xlabel=ILN Size,
      ymajorgrids=true,                 xmajorgrids=false,      grid style=dashed,
      ticklabel style={{font=\\tiny}},  minor y tick num = 3,
      colormap/greenyellow,
      % ymax=3000,                      ymin=0, xmin=1,
      % xtick={{3, 5, 7, 9, 11, 13, 15, 17, 19}},
      % xmajorgrids=true,
      % hide axis,
    ]
    \\addplot coordinates {{
        {hist}
    }}  ;
    \\addplot [ybar, bar width=12pt, color=red, line width=1] coordinates {{ ({x_95}.5, {y_95}) }};
    \end{{axis}}
    \end{{tikzpicture}}
    \\vspace{{-7pt}}
    \caption{{Identity Link Networks Distribution}}
    \label{{fig_{label}}}
    \\vspace{{-0.5CM}}
    \end{{figure}}
    """

    if print_latex is True:
        print(hist, end="\n\n")

    stat_up = round((first / float(first + second)) * 100, 5)
    stat_down = round((second / float(first + second)) * 100, 5)
    print("\n{:.^100}".format(F' DISTRIBUTION RESULTS WITH XMAX: {xmax} '))
    print(F"\tTHE TOTAL NUMBER OF CLUSTERS < {threshold:<5}   {first:12} REPRESENTING {stat_up}% OF THE TOTAL")
    print(F"\tTHE TOTAL NUMBER OF CLUSTERS > {threshold:<5}   {second:12} REPRESENTING {stat_down}% OF THE TOTAL")
    print("\tTHE TOTAL NUMBER OF CLUSTERS           {:12} ".format(first + second))
    print("\t95% CLUSTERS IS REACHED AT SIZE        {:12} ".format(x_95))
    # print("\tNUMBER OF CLUSTERS OF SIZE BELOW 31         {} REPRESENTING {}% OF THE TOTAL".format(first, stat_up))
    # print("\tNUMBER OF CLUSTERS OF SIZE ABOVE 30         {} REPRESENTING {}% OF THE TOTAL".format(second, stat_down))
    print("{:.^100}".format(''))

    with open(join(serialisation_dir, "distribution.latex"), mode="w") as distribution:
        distribution.write(hist)

    return hist


# def plot_compact1_0(specs, vis=None, root=None, map_of_labels=None, sub_clusters=None, link_thickness=1,
#                   investigated=True, color=None, decimal_size=5, desc=True, delta=None, activated=False):
#
#     if activated is False or specs is None:
#         problem(text="--> THE FUNCTION [improved_cluster_vis] IS NOT ACTIVATED.")
#         return
#
#     cluster = deepcopy(specs["cluster_data"])
#     data_store = specs["data_store"]
#     # USER SELECTED PROPERTIES
#     properties = specs['properties']
#     # DICTIONARY WITH A LIST OF STRENGTHS
#     strengths = cluster["strengths"]
#     total = len(cluster['nodes'])
#     total_links = len(cluster['nodes'])
#
#     link_view, nodes_view = [], []
#     added, link_checker = set(), set()
#     aggregated, new_links = dict(), dict()
#     group_map, sub_cluster_link_count = dict(), dict()
#     new_root = root if root is not None else dict()
#     label_map = map_of_labels if map_of_labels is not None else dict()
#     new_clusters = sub_clusters if sub_clusters is not None else dict()
#
#     def strength_classification(stop=0.5, delta_diff=0.1, decimal=5, reverse=True):
#
#         range_list = []
#         up = 1
#         while True:
#             down = up - delta_diff
#             down = 0 if down < 0 else down
#             range_list += intervals.openclosed(round(down, decimal), round(up, 5))
#             if down <= stop:
#                 break
#             up = up - delta_diff
#
#         range_list = sorted(range_list, reverse=reverse)
#
#         return range_list
#
#     problem(tab="\t", text=F"MISSING LINKS: {total*(total-1)/2 -  len(strengths)}\n", label=" INFO ")
#     print("\t--> THE CLUSTER IS OF {} NODES AND {}: {}".format(
#         total, total_links, "INVESTIGATED" if investigated is True else "EVIDENCE"))
#     # print_object(strengths)
#
#     # ***********************************
#     print("\n\t--> 1. GET THE MAXIMUM")
#     # ***********************************
#     for key, value in strengths.items():
#         if isinstance(value, list) is False:
#             problem(text="THE STRENGTH MUST BE A LIST")
#             exit()
#         strengths[key] = round(float(max(value)), decimal_size)
#     # print_object(strengths, overview=False)
#
#     if delta is not None and delta > 0:
#
#         strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=False))
#         classification = []
#
#         # ******************************************************
#         print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
#         # ******************************************************
#         for key, value in strengths.items():
#             classification = strength_classification(stop=value, delta_diff=delta, decimal=decimal_size, reverse=desc)
#             break
#
#         # *******************************************
#         print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
#         # *******************************************
#         for interval in classification:
#             s = intervals.to_string(interval)
#             if s not in aggregated:
#                 aggregated[s] = []
#
#     else:
#
#         # *****************************************************
#         print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
#         # *****************************************************
#         strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=desc))
#
#         # ****************************************
#         print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
#         # ****************************************
#         for key, value in strengths.items():
#             s = intervals.to_string(intervals.singleton(value))
#             if s not in aggregated:
#                 aggregated[s] = []
#
#     # USE THE AGGREGATED TO REORGANIZE THE LINKS
#     def find_bin(search_strength, bin_input, delta_used, stop, reverse=True):
#         # print(bin_input)
#         # print(search_strength, delta_used, stop)
#         index = (floor((1 - search_strength) / delta_used)) if reverse is True \
#             else (floor((search_strength - stop) / delta_used)) + 1
#         # print(bin_input[index])
#         return bin_input[index]
#
#     # LIST OF ALL BINS
#     bins_list = list(aggregated.keys())
#     bin_end = intervals.from_string(bins_list[0], conv=float).lower if desc is False \
#         else intervals.from_string(bins_list[0], conv=float).upper
#     # print_object(bins_list)
#
#     # DICTIONARY OF LINKS ORGANISED PER BINS
#     grouped_links = dict()
#
#     # INITIALISE THE BINS IN WHICH THE LINKS CAN B E ORGANISED
#     for bin_key in aggregated:
#         grouped_links[bin_key] = []
#
#     # ORGANISE THE LINKS IN THE BINS
#     for source, target in cluster["links"]:
#
#         # GET THE KEY OF THE CURRENT LINK
#         link_key = get_key(source, target)
#
#         # GET THE STRENGTH OF THE CURRENT LINK
#         link_strength = strengths[link_key]
#
#         # FIND THE BIN FOR THE CURRENT LINK BASED ON ITS STRENGTH
#         bin_key = find_bin(
#                 search_strength=link_strength, bin_input=bins_list, delta_used=delta, stop=bin_end, reverse=desc) \
#             if delta is not None and delta > 0 else intervals.to_string(intervals.singleton(link_strength))
#
#         # APPEND THE LINK TO THE BIN STACK
#         grouped_links[bin_key] += [(source, target)]
#
#     # print_object(list(grouped_links.keys()), overview=False)
#     # print_object(grouped_links, overview=False)
#     # print_object(aggregated, overview=False)
#
#     print(F"\t\t   >>> {len(aggregated)} POSSIBLE SUB-GROUPS FOUND BASED ON STRENGTH.")
#     print("\t\t   >>> THE CLASSIFICATION IS {} .".format(" | ".join(str(x) for x in aggregated.keys())))
#
#     # ************************************************************
#     print("\n\t--> 4. FIND NEW SUB-CLUSTERS AT EACH ITERATION. "
#           "THIS ASSUMES THAT THE DICTIONARY IS SORTED IN REVERSE")
#     # AT THE END OF THIS, WE HAVE ALL
#     # SUB-CLUSTERS BASED ON AGGREGATED STRENGTHS
#     # ************************************************************
#     step_4 = time.time()
#     for constraint_key in aggregated.keys():
#
#         # ITERATING THROUGH THE LINKS
#         print(F"\t\tBIN {constraint_key:17}")
#
#         # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#         # (BOTTLENECK)
#         # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#         for source, target in cluster["links"]:
#             # for source, target in grouped_links[constraint_key]:
#
#             # GET THE KEY OF THE CURRENT LINK
#             link_key = get_key(source, target)
#
#             # GET THE STRENGTH OF THE CURRENT LINK
#             link_strength = strengths[link_key]
#
#             # WE ARE INTERESTED IN FINDING NODES OF THE CURRENT GROUP
#             # print(link_strength, constraint_key)
#             if link_strength not in intervals.from_string(constraint_key, conv=float):
#                 continue
#
#             # LOOKING FOR NODES THAT CAN BE GROUPED-IN WITH THE CURRENT STRENGTH
#             src_pos, trg_pos = None, None
#
#             # GROUP OF THE CURRENT STRENGTH.
#             groups = aggregated[constraint_key]
#
#             # LOOK FOR A GROUP THAT HAS THE SOURCE OR TARGET
#             for i in range(0, len(groups)):
#                 if source in groups[i]:
#                     src_pos = i
#                 if target in groups[i]:
#                     trg_pos = i
#                 if src_pos is not None and trg_pos is not None:
#                     break
#
#             # print(constraint_key, source, target)
#             # print(src_pos, trg_pos)
#
#             # FILL AGGREGATED WITH THE NEW SUB-CLUSTERS
#             # SAVING THE NODE IN THE CORRECT GROUP
#             if src_pos == trg_pos is None:
#
#                 if source not in added and target not in added:
#                     aggregated[constraint_key] += [{source, target}]
#                     added.add(source)
#                     added.add(target)
#
#                 elif source not in added and target in added:
#                     aggregated[constraint_key] += [{source}]
#                     added.add(source)
#
#                 elif source in added and target not in added:
#                     aggregated[constraint_key] += [{target}]
#                     added.add(target)
#
#             elif src_pos is not None and trg_pos is None:
#
#                 # if source not in added:
#                 #     aggregated[link_strength][src_pos].add(source)
#                 #     added.add(source)
#
#                 if target not in added:
#                     aggregated[constraint_key][src_pos].add(target)
#                     added.add(target)
#
#             elif src_pos is None and trg_pos is not None:
#
#                 if source not in added:
#                     aggregated[constraint_key][trg_pos].add(source)
#                     added.add(source)
#                 # if target not in added:
#                 #     aggregated[link_strength][trg_pos].add(target)
#                 #     added.add(target)
#
#             elif src_pos is not None and trg_pos is not None and src_pos != trg_pos:
#
#                 if len(aggregated[constraint_key][src_pos]) > len(aggregated[constraint_key][trg_pos]):
#                     big = aggregated[constraint_key][src_pos]
#                     small = aggregated[constraint_key][trg_pos]
#                     for item in small:
#                         big.add(item)
#                     aggregated[constraint_key].__delitem__(trg_pos)
#
#                 else:
#                     small = aggregated[constraint_key][src_pos]
#                     big = aggregated[constraint_key][trg_pos]
#                     for item in small:
#                         big.add(item)
#                     aggregated[constraint_key].__delitem__(src_pos)
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_4)}")
#     # print_object(aggregated, overview=False)
#
#     # ************************************************************
#     print("\n\t--> 5. CREATING "
#           "\n\t\t5.1 SUB-CLUSTERS "
#           "\n\t\t5.2 NUMBER OF LINKS WITHIN SUB-CLUSTERS "
#           "\n\t\t5.3 LINKS ACROSS SUB-GROUPS")
#     # ************************************************************
#     count_bins = 0
#     bins_total = len(aggregated)
#     step_5 = time.time()
#     for key, groups in aggregated.items():
#
#         count_bins += 1
#         made = F'IS MADE OF {len(groups)} GROUPS'
#         print(F"\t\t\t{count_bins} / {bins_total} BIN {key:7} {made:17} AND {len(grouped_links[key])} LINKS")
#         # FOR EACH GROUP OF THE SAME STRENGTH
#         for group in groups:
#
#             # GENERATE THE ID OF THIS GROUP BASED ON THE SMALLEST NODE STRING
#             smallest = None
#             for resource in group:
#                 if smallest is None:
#                     smallest = resource
#                 elif smallest > resource:
#                     smallest = resource
#             # print("smallest", smallest)
#             group_id = hasher(smallest)
#
#             # *****************************
#             # 5.1 RECONSTRUCT THE CLUSTER
#             # *****************************
#             new_clusters[group_id] = group
#
#             # 5.2 DOCUMENT THE ALL MAP
#             group_map[group_id] = key
#
#             # **************************
#             # 5.3 GENERATE THE ROOT MAP
#             # **************************
#             for resource in group:
#                 new_root[resource] = group_id
#
#             # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#             # ITERATING THROUGH THE LINKS (BOTTLENECK)
#             # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#             for source, target in cluster["links"]:
#                 # for source, target in grouped_links[key]:
#
#                 # ****************************************
#                 #  5.4 FIND LINKS ACROSS SUB CLUSTERS
#                 # ****************************************
#                 link_key = get_key(source, target)
#                 if (source not in group and target in group) or (source in group and target not in group):
#                     if link_key not in new_links:
#                         new_links[link_key] = source, target, strengths[link_key]
#
#                 # ******************************************************
#                 # 5.5 COUNT THE NUMBER OFF LINKS WITHIN EACH SUB-CLUSTER
#                 # ******************************************************
#                 if (source != target) and (source in group and target in group):
#
#                     if group_id not in sub_cluster_link_count:
#                         sub_cluster_link_count[group_id] = 1
#                     else:
#                         sub_cluster_link_count[group_id] += 1
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_5)}")
#     # print_object(new_clusters, overview=False)
#     # print_object(new_links, overview=False)
#     # print_object(group_map, overview=False)
#     # print_object(new_root, overview=False)
#
#     # *****************************************************************
#     print("\n\t--> 6. FETCH LABELS AND GENERATE VISUALISATION NODES")
#     # *****************************************************************
#
#     properties_converted = convert_properties(properties) if properties is not None else None
#     step_6 = time.time()
#     for key, sub_cluster in new_clusters.items():
#
#         # ************************************
#         # 6.1 GET A LABEL FOR THE SUB-CLUSTER
#         # ************************************
#         # result = None
#         resource = list(sub_cluster)[0]
#         # print_object(resource, overview=False)
#         # QUERY FOR FETCHING THE LABEL
#         query = Middleware.node_labels_switcher[data_store](
#             resources=resource, targets=properties_converted)
#
#         # FETCHING THE LABELS
#         table = None
#         if data_store in Middleware.run_query_matrix_switcher and query:
#             result = Middleware.run_query_matrix_switcher[data_store](query)
#             # Stardog.display_matrix(result, spacing=130, is_activated=True)
#             table = result[St.result] if isinstance(result, dict) else result
#
#         if properties_converted is not None and table is not None:
#             db_label = get_uri_local_name_plus(table[1][1])
#             underscore = db_label.split("__")
#             db_label = underscore[1] if len(underscore) > 1 else db_label
#             label = F"-- {table[1][3]} ({db_label})"
#         else:
#             # label = F"-- ({resource})"
#             # label = F"-- {get_uri_local_name_plus(resource)}"
#             label = F"-- {resource}"
#
#         # MAP THE LABEL TO THE SUB-CLUSTER
#         label_map[key] = label
#
#         # ****************************************
#         # 6.2 GENERATE THE NODES FOR VISUALISATION
#         # ****************************************
#         group_size = len(sub_cluster)
#         possible = group_size * (group_size - 1) / 2
#
#         if key in group_map:
#             node = {
#                 'nodes': group_size,
#                 'strength': group_map[key],
#                 'size': 10,
#                 'missing_links':
#                     (possible - sub_cluster_link_count[key]) / float(possible) if key in sub_cluster_link_count else 0,
#                 'group': color,
#                 'id': label_map[key],
#                 'investigated': str(investigated).lower()
#             }
#             node['color'] = hash_number(key) if color is None else color
#             nodes_view += [node]
#
#             if node['missing_links'] < 0:
#                 print(sub_cluster_link_count[key])
#                 print("possible:", possible)
#                 print("group_size:", group_size)
#                 print("sub_cluster_link_count", sub_cluster_link_count[key])
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_6)}")
#     # print_object(nodes_view, overview=False)
#
#     # ***************************************************
#     print('\t--> 7. GENERATE VISUALISATION LINKS')
#     # ***************************************************
#     link_count = dict()
#     step_7 = time.time()
#     for key, link in new_links.items():
#
#         # [link[0]]     -> RETURNS THE RESOURCE
#         # [new_root]    -> RETURNS THE SUB-CLUSTER THO WITCH THE RESOURCE BELONGS TO
#         # [label_map]   -> RETURNS THE LABEL OF SUB-CLUSTER
#         # print_object(new_root)
#         label_1 = label_map[new_root[link[0]]]
#         label_2 = label_map[new_root[link[1]]]
#         strength = link[2]
#         distance = 150
#
#         # ORDERING THE LABELS
#         if label_1 < label_2:
#             source, target = label_1, label_2
#             dist_factor = [len(new_clusters[new_root[link[0]]]), len(new_clusters[new_root[link[1]]])]
#         else:
#             source, target = label_2, label_1
#             dist_factor = [len(new_clusters[new_root[link[1]]]), len(new_clusters[new_root[link[0]]])]
#
#         # GENERATE THE KEY
#         labels = F"{source}-{target}"
#
#         if labels not in link_count:
#             link_count[labels] = 1
#         else:
#             link_count[labels] += 1
#
#         current = {
#             'source': source,
#             'target': target,
#             "dash": F"3,{20 * (1 - float(strength))}",
#             'distance': distance,
#             'color': 'red' if float(strength) < 1 else "black",
#             'value': 4,
#             'strength': strength,
#             'dist_factor': dist_factor,
#         }
#
#         if labels not in link_checker:
#             link_view += [current]
#             link_checker.add(labels)
#         else:
#             # print(labels)
#             for dictionary in link_view:
#                 curr_label = F"{dictionary['source']}-{dictionary['target']}"
#                 if labels == curr_label:
#                     dictionary['strength'] = max(dictionary['strength'], current['strength'])
#                     break
#
#     # UPDATING THE THICKNESS OF GHE LINKS
#     for link in link_view:
#         link['value'] = link_count[F"{link['source']}-{link['target']}"] * link_thickness
#
#     # VISUALISATION OBJECT
#     if vis is None:
#         vis = {
#             "id": specs["cluster_id"],
#             "confidence": 1,
#             "decision": 1,
#             "metric": "e_Q MESSAGE",
#             "messageConf": "",
#             'links': link_view,
#             'nodes': nodes_view
#         }
#     else:
#
#         vis['links'] += link_view
#         vis['nodes'] += nodes_view
#
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_7)}")
#     # print_object(vis, overview=False)
#     # print_object(nodes_view, overview=False)
#     # print_object(link_view, overview=False)
#     # print_object(aggregated, overview=False)
#     # print_object(link_count, overview=False)
#     # print_object(label_map, overview=False)
#
#     # with open('C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code\data_new_vis.json', mode='w') as file:
#     #     json.dump(vis, file)
#
#     return vis
#
#
# def plot_compact1_1(specs, vis=None, root=None, map_of_labels=None, sub_clusters=None, link_thickness=1,
#                  investigated=True, color=None, decimal_size=5, desc=True, delta=None, activated=False):
#
#     if activated is False or specs is None:
#         problem(text="--> THE FUNCTION [improved_cluster_vis] IS NOT ACTIVATED.")
#         return
#
#     cluster = deepcopy(specs["cluster_data"])
#     data_store = specs["data_store"]
#     # USER SELECTED PROPERTIES
#     properties = specs['properties']
#     # DICTIONARY WITH A LIST OF STRENGTHS
#     strengths = cluster["strengths"]
#     # DICTIONARY OF COMPACT CLUSTERS
#     compact = defaultdict(list)
#     total = len(cluster['nodes'])
#     total_links = len(cluster['nodes'])
#
#     link_view, nodes_view = [], []
#     added, link_checker = set(), set()
#     aggregated, new_links = dict(), dict()
#     group_map, sub_cluster_link_count = dict(), dict()
#     new_root = root if root is not None else dict()
#     label_map = map_of_labels if map_of_labels is not None else dict()
#     new_clusters = sub_clusters if sub_clusters is not None else dict()
#
#     def strength_classification(stop=0.5, delta_diff=0.1, decimal=5, reverse=True):
#
#         range_list = []
#         up = 1
#         while True:
#             down = up - delta_diff
#             down = 0 if down < 0 else down
#             range_list += intervals.openclosed(round(down, decimal), round(up, 5))
#             if down <= stop:
#                 break
#             up = up - delta_diff
#
#         range_list = sorted(range_list, reverse=reverse)
#
#         return range_list
#
#     problem(tab="\t", text=F"MISSING LINKS: {total*(total-1)/2 -  len(strengths)}\n", label=" INFO ")
#     print("\t--> THE CLUSTER IS OF {} NODES AND {}: {}".format(
#         total, total_links, "INVESTIGATED" if investigated is True else "EVIDENCE"))
#     # print_object(strengths)
#
#     # ***********************************
#     print("\n\t--> 1. GET THE MAXIMUM")
#     # ***********************************
#     for key, value in strengths.items():
#         if isinstance(value, list) is False:
#             problem(text="THE STRENGTH MUST BE A LIST")
#             exit()
#         strengths[key] = round(float(max(value)), decimal_size)
#     # print_object(strengths, overview=False)
#
#     if delta is not None and delta > 0:
#
#         strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=False))
#         classification = []
#
#         # ******************************************************
#         print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
#         # ******************************************************
#         for key, value in strengths.items():
#             classification = strength_classification(stop=value, delta_diff=delta, decimal=decimal_size, reverse=desc)
#             break
#
#         # *******************************************
#         print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
#         # *******************************************
#         for interval in classification:
#             s = intervals.to_string(interval)
#             if s not in aggregated:
#                 aggregated[s] = []
#
#     else:
#
#         # *****************************************************
#         print("\t--> 2. ORDER THE MAXIMUM IN DESCENDING ORDER")
#         # *****************************************************
#         strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=desc))
#
#         # ****************************************
#         print("\n\t--> 3. FIND ALL POSSIBLE GROUPS")
#         # ****************************************
#         for key, value in strengths.items():
#             s = intervals.to_string(intervals.singleton(value))
#             if s not in aggregated:
#                 aggregated[s] = []
#
#     # USE THE AGGREGATED TO REORGANIZE THE LINKS
#     def find_bin(search_strength, bin_input, delta_used, stop, reverse=True):
#         # print(bin_input)
#         # print(search_strength, delta_used, stop)
#         index = (floor((1 - search_strength) / delta_used)) if reverse is True \
#             else (floor((search_strength - stop) / delta_used)) + 1
#         # print(bin_input[index])
#         return bin_input[index]
#
#     # LIST OF ALL BINS
#     bins_list = list(aggregated.keys())
#     bin_end = intervals.from_string(bins_list[0], conv=float).lower if desc is False \
#         else intervals.from_string(bins_list[0], conv=float).upper
#     # print_object(bins_list)
#
#     # DICTIONARY OF LINKS ORGANISED PER BINS
#     grouped_links = dict()
#
#     # INITIALISE THE BINS IN WHICH THE LINKS CAN B E ORGANISED
#     for bin_key in aggregated:
#         grouped_links[bin_key] = []
#
#     # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#     # (BOTTLENECK SOLUTION-1)
#     # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#     # ORGANISE THE LINKS IN THE BINS
#     for source, target in cluster["links"]:
#
#         # GET THE KEY OF THE CURRENT LINK
#         link_key = get_key(source, target)
#
#         # GET THE STRENGTH OF THE CURRENT LINK
#         link_strength = strengths[link_key]
#
#         # FIND THE BIN FOR THE CURRENT LINK BASED ON ITS STRENGTH
#         bin_key = find_bin(
#                 search_strength=link_strength, bin_input=bins_list, delta_used=delta, stop=bin_end, reverse=desc) \
#             if delta is not None and delta > 0 else intervals.to_string(intervals.singleton(link_strength))
#
#         # APPEND THE LINK TO THE BIN STACK
#         grouped_links[bin_key] += [(source, target)]
#
#     # print_object(list(grouped_links.keys()), overview=False)
#     # print_object(grouped_links, overview=False)
#     # print_object(aggregated, overview=False)
#
#     print(F"\t\t   >>> {len(aggregated)} POSSIBLE SUB-GROUPS FOUND BASED ON STRENGTH.")
#     print("\t\t   >>> THE CLASSIFICATION IS {} .".format(" | ".join(str(x) for x in aggregated.keys())))
#
#     # ************************************************************
#     # ************************************************************
#     print("\n\t--> 4. FIND NEW SUB-CLUSTERS AT EACH ITERATION. "
#           "THIS ASSUMES THAT THE DICTIONARY IS SORTED IN REVERSE")
#     # AT THE END OF THIS, WE HAVE ALL
#     # SUB-CLUSTERS BASED ON AGGREGATED STRENGTHS
#     # ************************************************************
#     # ************************************************************
#     step_4 = time.time()
#     for constraint_key in aggregated.keys():
#
#         # ITERATING THROUGH THE LINKS
#         print(F"\t\tBIN {constraint_key:17}")
#
#         # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#         # (BOTTLENECK PROBLEM-1)
#         # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#         # for source, target in cluster["links"]:
#         for source, target in grouped_links[constraint_key]:
#
#             # GET THE KEY OF THE CURRENT LINK
#             link_key = get_key(source, target)
#
#             # GET THE STRENGTH OF THE CURRENT LINK
#             link_strength = strengths[link_key]
#
#             # WE ARE INTERESTED IN FINDING NODES OF THE CURRENT GROUP
#             # print(link_strength, constraint_key)
#             if link_strength not in intervals.from_string(constraint_key, conv=float):
#                 continue
#
#             # LOOKING FOR NODES THAT CAN BE GROUPED-IN WITH THE CURRENT STRENGTH
#             src_pos, trg_pos = None, None
#
#             # GROUP OF THE CURRENT STRENGTH.
#             groups = aggregated[constraint_key]
#
#             # LOOK FOR A GROUP THAT HAS THE SOURCE OR TARGET
#             for i in range(0, len(groups)):
#                 if source in groups[i]:
#                     src_pos = i
#                 if target in groups[i]:
#                     trg_pos = i
#                 if src_pos is not None and trg_pos is not None:
#                     break
#
#             # print(constraint_key, source, target)
#             # print(src_pos, trg_pos)
#
#             # FILL AGGREGATED WITH THE NEW SUB-CLUSTERS
#             # SAVING THE NODE IN THE CORRECT GROUP
#             if src_pos == trg_pos is None:
#
#                 if source not in added and target not in added:
#                     aggregated[constraint_key] += [{source, target}]
#                     added.add(source)
#                     added.add(target)
#
#                 elif source not in added and target in added:
#                     aggregated[constraint_key] += [{source}]
#                     added.add(source)
#
#                 elif source in added and target not in added:
#                     aggregated[constraint_key] += [{target}]
#                     added.add(target)
#
#             elif src_pos is not None and trg_pos is None:
#
#                 # if source not in added:
#                 #     aggregated[link_strength][src_pos].add(source)
#                 #     added.add(source)
#
#                 if target not in added:
#                     aggregated[constraint_key][src_pos].add(target)
#                     added.add(target)
#
#             elif src_pos is None and trg_pos is not None:
#
#                 if source not in added:
#                     aggregated[constraint_key][trg_pos].add(source)
#                     added.add(source)
#                 # if target not in added:
#                 #     aggregated[link_strength][trg_pos].add(target)
#                 #     added.add(target)
#
#             elif src_pos is not None and trg_pos is not None and src_pos != trg_pos:
#
#                 if len(aggregated[constraint_key][src_pos]) > len(aggregated[constraint_key][trg_pos]):
#                     big = aggregated[constraint_key][src_pos]
#                     small = aggregated[constraint_key][trg_pos]
#                     for item in small:
#                         big.add(item)
#                     aggregated[constraint_key].__delitem__(trg_pos)
#
#                 else:
#                     small = aggregated[constraint_key][src_pos]
#                     big = aggregated[constraint_key][trg_pos]
#                     for item in small:
#                         big.add(item)
#                     aggregated[constraint_key].__delitem__(src_pos)
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_4)}")
#     # print_object(aggregated, overview=False)
#
#     # ************************************************************
#     print("\n\t--> 5. CREATING "
#           "\n\t\t5.1 SUB-CLUSTERS "
#           "\n\t\t5.2 NUMBER OF LINKS WITHIN SUB-CLUSTERS "
#           "\n\t\t5.3 LINKS ACROSS SUB-GROUPS")
#     # ************************************************************
#     count_bins = 0
#     bins_total = len(aggregated)
#     step_5 = time.time()
#     for key, groups in aggregated.items():
#
#         count_bins += 1
#         made = F'IS MADE OF {len(groups)} GROUPS'
#         print(F"\t\t\t{count_bins} / {bins_total} BIN {key:7} {made:17} AND {len(grouped_links[key])} LINKS")
#         # FOR EACH GROUP OF THE SAME STRENGTH
#         for group in groups:
#
#             # GENERATE THE ID OF THIS GROUP BASED ON THE SMALLEST NODE STRING
#             smallest = None
#             for resource in group:
#                 if smallest is None:
#                     smallest = resource
#                 elif smallest > resource:
#                     smallest = resource
#             # print("smallest", smallest)
#             group_id = hasher(smallest)
#
#             # *****************************
#             # 5.1 RECONSTRUCT THE CLUSTER
#             # *****************************
#             new_clusters[group_id] = group
#
#             # 5.2 DOCUMENT THE ALL MAP
#             group_map[group_id] = key
#
#             # **************************
#             # 5.3 GENERATE THE ROOT MAP
#             # **************************
#             for resource in group:
#                 new_root[resource] = group_id
#
#             # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#             # ITERATING THROUGH THE LINKS (BOTTLENECK-2)
#             # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#             # for source, target in cluster["links"]:
#             for source, target in grouped_links[key]:
#
#                 # ****************************************
#                 #  5.4 FIND LINKS ACROSS SUB CLUSTERS
#                 # ****************************************
#                 link_key = get_key(source, target)
#                 if (source not in group and target in group) or (source in group and target not in group):
#                     if link_key not in new_links:
#                         new_links[link_key] = source, target, strengths[link_key]
#
#                 # ******************************************************
#                 # 5.5 COUNT THE NUMBER OFF LINKS WITHIN EACH SUB-CLUSTER
#                 # ******************************************************
#                 if (source != target) and (source in group and target in group):
#
#                     if group_id not in sub_cluster_link_count:
#                         sub_cluster_link_count[group_id] = 1
#                     else:
#                         sub_cluster_link_count[group_id] += 1
#
#                     if len(group) > 2:
#                             compact[group_id].append((source, target, strengths[link_key]))
#
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_5)}")
#     # print_object(new_clusters, overview=False)
#     # print_object(new_links, overview=False)
#     # print_object(group_map, overview=False)
#     # print_object(new_root, overview=False)
#
#     # *****************************************************************
#     print("\n\t--> 6. FETCH LABELS AND GENERATE VISUALISATION NODES")
#     # *****************************************************************
#
#     properties_converted = convert_properties(properties) if properties is not None else None
#     step_6 = time.time()
#
#     for key, sub_cluster in new_clusters.items():
#
#         # ************************************
#         # 6.1 GET A LABEL FOR THE SUB-CLUSTER
#         # ************************************
#         # result = None
#         resource = list(sub_cluster)[0]
#         # print_object(resource, overview=False)
#         # QUERY FOR FETCHING THE LABEL
#         query = Middleware.node_labels_switcher[data_store](
#             resources=resource, targets=properties_converted)
#
#         # FETCHING THE LABELS
#         table = None
#         if data_store in Middleware.run_query_matrix_switcher and query:
#             result = Middleware.run_query_matrix_switcher[data_store](query)
#             # Stardog.display_matrix(result, spacing=130, is_activated=True)
#             table = result[St.result] if isinstance(result, dict) else result
#
#         if properties_converted is not None and table is not None:
#             db_label = get_uri_local_name_plus(table[1][1])
#             underscore = db_label.split("__")
#             db_label = underscore[1] if len(underscore) > 1 else db_label
#             label = F"-- {table[1][3]} ({db_label})"
#         else:
#             # label = F"-- ({resource})"
#             # label = F"-- {get_uri_local_name_plus(resource)}"
#             label = F"-- {resource}"
#
#         # MAP THE LABEL TO THE SUB-CLUSTER
#         label_map[key] = label
#
#         # ****************************************
#         # 6.2 GENERATE THE NODES FOR VISUALISATION
#         # ****************************************
#         group_size = len(sub_cluster)
#         possible = group_size * (group_size - 1) / 2
#
#         if key in group_map:
#             node = {
#                 'nodes': group_size,
#                 'strength': group_map[key],
#                 'size': 10,
#                 'missing_links':
#                     (possible - sub_cluster_link_count[key]) / float(possible) if key in sub_cluster_link_count else 0,
#                 'group': color,
#                 'id': label_map[key],
#                 'investigated': str(investigated).lower()
#             }
#             node['group'] = 1 if group_size == 1 else int((hash_number(key)) if color is None else int(color))
#
#             if node['group'] > 1:
#                 print("\t\t --> COMMUNITY COLOR",  node['group'])
#             nodes_view += [node]
#
#             if node['missing_links'] < 0:
#                 print(sub_cluster_link_count[key])
#                 print("possible:", possible)
#                 print("group_size:", group_size)
#                 print("sub_cluster_link_count", sub_cluster_link_count[key])
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_6)}")
#     # print_object(nodes_view, overview=False)
#
#     # ***************************************************
#     print('\t--> 7. GENERATE VISUALISATION LINKS')
#     # ***************************************************
#     link_count = dict()
#     step_7 = time.time()
#     for key, link in new_links.items():
#
#         # [link[0]]     -> RETURNS THE RESOURCE
#         # [new_root]    -> RETURNS THE SUB-CLUSTER THO WITCH THE RESOURCE BELONGS TO
#         # [label_map]   -> RETURNS THE LABEL OF SUB-CLUSTER
#         # print_object(new_root)
#         label_1 = label_map[new_root[link[0]]]
#         label_2 = label_map[new_root[link[1]]]
#         strength = link[2]
#         distance = 150
#
#         # ORDERING THE LABELS
#         if label_1 < label_2:
#             source, target = label_1, label_2
#             dist_factor = [len(new_clusters[new_root[link[0]]]), len(new_clusters[new_root[link[1]]])]
#         else:
#             source, target = label_2, label_1
#             dist_factor = [len(new_clusters[new_root[link[1]]]), len(new_clusters[new_root[link[0]]])]
#
#         # GENERATE THE KEY
#         labels = F"{source}-{target}"
#
#         if labels not in link_count:
#             link_count[labels] = 1
#         else:
#             link_count[labels] += 1
#
#         current = {
#             'source': source,
#             'target': target,
#             "dash": F"3,{20 * (1 - float(strength))}",
#             'distance': distance,
#             'color': 'red' if float(strength) < 1 else "black",
#             'value': 4,
#             'strength': strength,
#             'dist_factor': dist_factor,
#         }
#
#         if labels not in link_checker:
#             link_view += [current]
#             link_checker.add(labels)
#         else:
#             # print(labels)
#             for dictionary in link_view:
#                 curr_label = F"{dictionary['source']}-{dictionary['target']}"
#                 if labels == curr_label:
#                     dictionary['strength'] = max(dictionary['strength'], current['strength'])
#                     break
#
#     # UPDATING THE THICKNESS OF GHE LINKS
#     for link in link_view:
#         link['value'] = link_count[F"{link['source']}-{link['target']}"] * link_thickness
#
#     # VISUALISATION OBJECT
#     if vis is None:
#         vis = {
#             "id": specs["cluster_id"],
#             "confidence": 1,
#             "decision": 1,
#             "metric": "e_Q MESSAGE",
#             "messageConf": "",
#             'links': link_view,
#             'nodes': nodes_view
#         }
#     else:
#
#         vis['links'] += link_view
#         vis['nodes'] += nodes_view
#
#     print(F"\t\tDONE IN {datetime.timedelta(seconds=time.time() - step_7)}")
#     # print_object(vis, overview=False)
#     # print_object(nodes_view, overview=False)
#     # print_object(link_view, overview=False)
#     # print_object(aggregated, overview=False)
#     # print_object(link_count, overview=False)
#     # print_object(label_map, overview=False)
#
#     # with open('C:\\Users\Al\Dropbox\@VU\Ve\Golden Agents\Cluster Vis Code\data_new_vis.json', mode='w') as file:
#     #     json.dump(vis, file)
#
#     return vis, compact
