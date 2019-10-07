import re
import time
import gzip
import datetime
import intervals
import statistics
import networkx as nx
import common.ll.Generic.Utility as Ut
import common.ll.Generic.Settings as St
import common.ll.DataAccess.Middleware as Middleware

from math import floor
from copy import deepcopy
from os.path import join
from io import StringIO as Buffer
from collections import defaultdict
from common.ll.Clustering.Iln_eQ import sigmoid
from common.ll.Generic.Utility import pickle_deserializer, to_nt_format, print_heading, completed, \
    get_uri_local_name_plus, undo_nt_format,  print_object, get_key, hasher, hash_number, problem


# GET PATH OF THE SERIALISED DIRECTORY
from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
import common.ll.DataAccess.Stardog.Query as Stardog

label_prefix = '-- '
related_distance = 550
short_distance = 350
_format = "It is %a %b %d %Y %H:%M:%S"
date = datetime.datetime.today()
_line = "--------------------------------------------------------------" \
        "--------------------------------------------------------------"
sat_reducer = 1

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


def find_associations_regex(nodes, text):

    start = time.time()
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

        print_object(associated)

    completed(start)

    return associated


def find_associations(nodes, association_file):

    # NODES REPRESENT THE RESOURCES OF THE INVESTIGATED CLUSTER

    associated = []
    start = time.time()

    # MAKE SURE THE LIST IS NOT EMPTY
    if nodes and len(nodes) > 0:

        # OPEN THE ASSOCIATION FILE
        with gzip.open(association_file, 'rt') as associations:

            for statement in associations:

                # SPLIT THE ASSOCIATION
                split = statement.strip().split(',')

                # PUT IT IN NT FORMAT PRIOR TO THE CHECK
                if to_nt_format(split[0]) in nodes or to_nt_format(split[1]) in nodes:

                    # APPEND THE RESULT TO THE LIST
                    associated.append((split[0], split[1]))

        # print_object(associated)

    print(F"\t>>> WE FOUND {len(associated)} ASSOCIATIONS FOR PROVIDED {len(nodes)} NODES in {datetime.timedelta(seconds=time.time() - start)}.")
    # completed(start)

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

        association_file = join(CSV_ASSOCIATIONS_DIR, specs['associations'])

        # LOOK FOR THE NODES IN ASSOCIATION
        associations = find_associations(specs['cluster_data']['nodes'], association_file)

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
        root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{serialised}-2.txt.gz")

        # THE DICTIONARY OF THE CLUSTERS
        clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{serialised}-1.txt.gz")

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
                    "distance": short_distance, "value": 4,
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
    elif St.graph in specs[St.properties][0] and St.data in specs[St.properties][0]:
        nodes_vis_properties = specs[St.properties]
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

        association_file = join(CSV_ASSOCIATIONS_DIR, specs['associations'])

        # LOOK FOR THE NODES IN ASSOCIATION
        associations = find_associations(specs['cluster_data']['nodes'], association_file)

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
        root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-2.txt.gz")

        # THE DICTIONARY OF THE CLUSTERS
        clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['serialised']}-1.txt.gz")

        for paired in paired_nodes:
            formatted = to_nt_format(paired)
            if formatted in root:
                extended.add(root[formatted])

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
            resources=specs["cluster_data"]["nodes"], targets=nodes_vis_properties) \
            if nodes_vis_properties is not None else None
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
            "distance": related_distance if association is True else short_distance, "value": 4,
            "color": "purple" if association is True else("black" if strength == 1 else "red"),
            "dash": "20,10,5,5,5,10" if association is True else F"3,{20 * (1 - strength)}"
        }
        vis_data["links"].append(link_dict)
        # print(source, target)

    # ADDING THE ASSOCIATION LINKS
    if associations is not None:
        for link in associations:
            if to_nt_format(link[0]) in resources and to_nt_format(link[1]) in resources:

                link_dict = {
                    "source": resources[to_nt_format(link[0])],
                    "target": resources[to_nt_format(link[1])],
                    "distance": related_distance, "value": 4,
                    "color": "purple",
                    "dash": "20,10,5,5,5,10"
                }
                vis_data["links"].append(link_dict)

    # --> 3. RETURNING THE VISUALISATION OBJECT FOR RENDERING
    # print_object(vis_data)

    if visualisation_obj is None:
        Ut.completed(start, tab="")

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
        reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt.gz")
        root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt.gz")

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
            "distance": short_distance, "value": 4,
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


def plot_compact(specs, vis=None, root=None, map_of_labels=None, sub_clusters=None,
                 link_thickness=2, investigated=True, color=None, decimal_size=5, desc=True,
                 delta=None, community_only=False, html_color="#FFFFE0", activated=False):

    if activated is False or specs is None:
        problem(text="--> THE FUNCTION [improved_cluster_vis] IS NOT ACTIVATED.")
        return

    step = time.time()

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

    # USE THE AGGREGATED TO REORGANIZE THE LINKS
    def find_bin(search_strength, bin_input, delta_used, stop, reverse=True):
        # print(bin_input)
        # print(search_strength, delta_used, stop)
        index = (floor((1 - search_strength) / delta_used)) if reverse is True \
            else (floor((search_strength - stop) / delta_used)) + 1
        # print(bin_input[index])
        return bin_input[index]

    # UPDATING THE NUMBER OF INTERLINK BETWEEN COMMUNITIES
    def update_inter_link(delete=None, is_source=True):

        if delete is None:
            inter_key = get_key(new_root[source], new_root[target])
            if inter_key not in inter_links:
                inter_links[inter_key] = [new_root[source], new_root[target], link_strength, 1]
            else:
                inter_links[inter_key][3] += 1
                if inter_links[inter_key][2] < link_strength:
                    inter_links[inter_key][2] = link_strength
        else:
            # merged_id = new_root[delete]
            to_del = set()

            for del_k, del_item in inter_links.items():

                if delete in del_item:
                    to_del.add(del_k)

            for deletion_key in to_del:

                del_item = inter_links[deletion_key]

                new_group = new_root[list(new_clusters[delete])[0]]

                is_source = (delete == del_item[0])

                new_key = get_key(new_group, del_item[1]) if is_source else get_key(del_item[0], new_group)
                if is_source:
                    del_item[0] = new_group
                else:
                    del_item[1] = new_group

                # new_key = get_key(new_root[del_item[0]], new_root[del_item[1]])

                if new_key not in inter_links:
                    inter_links[new_key] = del_item

                else:
                    inter_links[new_key][3] += del_item[3]
                    if inter_links[new_key][2] < del_item[2]:
                        inter_links[new_key][2] = del_item[2]

                del inter_links[deletion_key]

    # LABELLING A NODE
    def node_label():

        # global properties_converted
        # SELECT ?resource ?dataset ?property ?value
        print('\t\tLABELLING THE NODE USING THE DATA STORE') if properties is not None \
            else print('\t\tKEEPING THE RESOURCE URIS AS PROPERTY ATTRIBUTE IS NONE')

        # ************************************
        # 6.1 GET A LABEL FOR THE SUB-CLUSTER
        # ************************************
        resource = []
        inverse_map = dict()
        for g_id, g_label in label_map.items():
            g_label = g_label.replace("-- ", "")
            resource.append(g_label)
            inverse_map[g_label] = g_id

        # QUERY FOR FETCHING THE LABEL
        query = Middleware.node_labels_switcher[data_store](
            resources=resource, targets=properties_converted)

        # FETCHING THE LABELS
        table = None
        if data_store in Middleware.run_query_matrix_switcher and query:
            result = Middleware.run_query_matrix_switcher[data_store](query)
            Stardog.display_matrix(result, spacing=130, is_activated=False)
            table = result[St.result] if isinstance(result, dict) else result

        if properties_converted is not None and table is not None:

            for i, rsc_label in enumerate(table):
                if i > 0:
                    uri = to_nt_format(table[i][0])
                    db_label = get_uri_local_name_plus(table[i][1])
                    underscore = db_label.split("__")
                    db_label = underscore[1] if len(underscore) > 1 else db_label
                    label = F"{label_prefix}{table[i][3]} ({db_label} {hasher(uri)})"
                    # label = F"{label_prefix}{table[i][3]} ({db_label})"

                    label_map[inverse_map[uri]] = label

    the_delta = F"\nWITH A DELTA OF {delta}" if delta is not None else ""
    indent = "\t" # if vis is None else "t"
    print_heading(F"PLOTTING THE ILN IN A COMPACT REPRESENTATION{the_delta}", tab=indent)
    data_store = specs["data_store"]
    cluster = deepcopy(specs["cluster_data"])

    # 5% of the total of the node should be swolloed
    node_total = specs["cluster_data"]["nodes"]
    node_total_ratio = round(15 * len(node_total) / 100)

    loners = dict()
    properties_converted = None

    # USER SELECTED PROPERTIES
    properties = specs['properties']

    # DICTIONARY WITH A LIST OF STRENGTHS
    strengths = cluster["strengths"]

    # LINKS RESTRUCTURED AS SOURCE - TARGET - MAX STRENGTH
    links = []

    # THE SET OF ALL MAX STRENGTH
    unique_strengths = set()

    # AGGREGATED IS A DICTIONARY WHERE THE KEY IS THE INTERVAL CONSTRAINT
    aggregated, inter_links = dict(), dict()

    # DICTIONARY OF LINKS ORGANISED PER BINS
    grouped_links = dict()

    # ADDED IS TO CHECK THE NODES THAT HAVE BEEN GROUPED
    added, link_checker = set(), set()

    group_map, sub_cluster_link_count = dict(), dict()
    new_root = root if root is not None else dict()
    label_map = map_of_labels if map_of_labels is not None else dict()
    new_clusters = sub_clusters if sub_clusters is not None else dict()

    # VIEW OBJECTS
    link_view, nodes_view = [], []

    # COMPACT NODE (N>1)
    parent_nodes = dict()

    # DICTIONARY OF COMPACT CLUSTERS
    compact = defaultdict(list)

    # ####################################################################################
    print("\t1. RESTRUCTURE THE LINKS IN TERMS OF SOURCE - TARGET - MAX STRENGTH")
    # ####################################################################################

    for source, target in cluster["links"]:

        # GET THE MAXIMUM STRENGTH
        max_strength = round(float(max(strengths[get_key(source, target)])), decimal_size)

        # ADD MAX-STRENGTH TO THE UNIQUE SET OF STRENGTHS
        unique_strengths.add(max_strength)

        # RESTRUCTURE THE LINK
        links.append((source, target, max_strength))

    # ####################################################################################
    print("\n\t2. CREATING THE CLASSIFICATION BINS BASED ON DELTA OR POINT.")
    # ####################################################################################

    if delta is not None and delta > 0:

        # 2. SORT THE SET ALL MAX STRENGTHS NOW AS A LIST
        unique_strengths = sorted(unique_strengths, reverse=False)

        # ***********************************************************
        print("\t\t2.1 ORDER THE MAXIMUM IN DESCENDING ORDER")
        # ***********************************************************

        classification = strength_classification(
            stop=unique_strengths[0], delta_diff=delta, decimal=decimal_size, reverse=desc)

        # ***********************************************************
        print("\t\t2.2. FIND ALL POSSIBLE GROUPS")
        # ***********************************************************
        for interval in classification:
            s = intervals.to_string(interval)
            if s not in aggregated:
                aggregated[s] = []

    else:

        # ***********************************************************
        print("\t\t2.1. ORDER THE MAXIMUM IN DESCENDING ORDER")
        # ***********************************************************
        # strengths = dict(sorted(strengths.items(), key=lambda item_to_sort: item_to_sort[1], reverse=desc))
        unique_strengths = sorted(unique_strengths, reverse=desc)

        # ***********************************************************
        print("\t\t2.2. FIND ALL POSSIBLE GROUPS")
        # ***********************************************************
        for value in unique_strengths:
            s = intervals.to_string(intervals.singleton(value))
            if s not in aggregated:
                aggregated[s] = []

    # ####################################################################################
    print("\n\t3. POPULATING THE BINS")
    # ####################################################################################

    # LIST OF ALL BINS FOR QUICK ACCESS
    bins_list = list(aggregated.keys())

    # DEPENDING OF THE ORDER, GET THE LAST BIN (STRENGTH INTERVAL)
    bin_end = intervals.from_string(bins_list[0], conv=float).lower if desc is False \
        else intervals.from_string(bins_list[0], conv=float).upper

    # INITIALISE THE BINS IN WHICH THE LINKS CAN BE ORGANISED
    for bin_key in aggregated:
        grouped_links[bin_key] = set()

    # ORGANISE THE LINKS IN THE BINS
    for source, target, link_strength in links:

        # FIND THE BIN FOR THE CURRENT LINK BASED ON ITS STRENGTH
        bin_key = find_bin(
            search_strength=link_strength, bin_input=bins_list, delta_used=delta, stop=bin_end, reverse=desc) \
            if delta is not None and delta > 0 else intervals.to_string(intervals.singleton(link_strength))

        # APPEND THE LINK TO THE BIN STACK
        grouped_links[bin_key].add((source, target, link_strength))

    print(F"\t\t   >>> {len(aggregated)} POSSIBLE SUB-GROUPS FOUND BASED ON STRENGTH.")
    print("\t\t   >>> THE CLASSIFICATION IS {} .".format(" | ".join(str(x) for x in aggregated.keys())))

    # ####################################################################################
    print("\n\t4. FIND NEW SUB-CLUSTERS AT EACH ITERATION (REVERSED SORTED DICTIONARY)")
    """ AT THE END OF THIS, WE HAVE ALL SUB-CLUSTERS BASED ON AGGREGATED STRENGTHS """
    # ####################################################################################

    step_4 = time.time()

    for constraint_key in aggregated.keys():

        # GROUP OF THE CURRENT STRENGTH.
        groups = aggregated[constraint_key]

        # print("group_position", group_position)

        # FETCH THE LINKS IN THE CURRENT INTERVAL
        for source, target, link_strength in grouped_links[constraint_key]:

            src_pos = groups.index(new_root[source]) if (source in new_root) and (new_root[source] in groups) else None
            trg_pos = groups.index(new_root[target]) if (target in new_root) and (new_root[target] in groups) else None

            # IF THE SOURCE IS A LONER, MAKE IT AVAILABLE TO CONNECT WITH NODES OF LOWER STRENGTH
            if source in loners:

                loner_constraint = loners[source][0]
                loner_group_id = loners[source][1]

                aggregated[loner_constraint].remove(loner_group_id)
                aggregated[constraint_key].append(loner_group_id)

                group_map[loner_group_id] = constraint_key
                src_pos = aggregated[constraint_key].index(loner_group_id)
                del loners[source]

                # added.remove(source)
                # group_id = loners[source][1]
                # aggregated[loners[source][0]].remove(group_id)
                # del new_root[source], new_clusters[group_id], loners[source]
                # # del new_clusters[group_id]
                # # del loners[source]
                # src_pos = None

            if target in loners:

                loner_constraint = loners[target][0]
                loner_group_id = loners[target][1]
                aggregated[loner_constraint].remove(loner_group_id)
                aggregated[constraint_key].append(loner_group_id)
                group_map[loner_group_id] = constraint_key
                trg_pos = aggregated[constraint_key].index(loner_group_id)
                del loners[target]

                # added.remove(target)
                # group_id = loners[target][1]
                # aggregated[loners[target][0]].remove(group_id)
                # del new_root[target], new_clusters[group_id], loners[target]
                # # del new_clusters[group_id]
                # # del loners[target]
                # trg_pos = None

            # print(constraint_key, source, target)
            # print(src_pos, trg_pos)

            # FILL AGGREGATED WITH THE NEW SUB-CLUSTERS
            # SAVING THE NODE IN THE CORRECT GROUP
            group_id = get_key(source, target)

            if True:

                # 1. SOURCE AND TARGET ARE NOT AGGREGATED (NOT IN A GROUP)
                if src_pos == trg_pos is None:

                    # SOURCE AND TARGET ARE IN THE SAME GROUP BUT IN THE SAME BIN
                    if source not in added and target not in added:
                        group = {source, target}
                        groups += [group_id]
                        added.add(source)
                        added.add(target)

                        # CREATE A NEW GROUP
                        new_clusters[group_id] = group

                        # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                        compact[group_id].append((source, target, link_strength))

                        # GROUP LABEL
                        label_map[group_id] = F"{label_prefix}{source}"

                        # DOCUMENT THE GROUP A NODE BELONGS TO
                        new_root[source] = group_id
                        new_root[target] = group_id

                        # DOCUMENT THE ALL MAP
                        group_map[group_id] = constraint_key

                        # ADD A WITHIN GROUP LINK CONT FOR THE GROUP
                        sub_cluster_link_count[group_id] = 1

                    # SOURCE AND TARGET ARE NOT FOUND IN THE CURRENT GROUP BUT ARE ADDED ALREADY
                    elif source in added and target in added:

                        if new_root[source] == new_root[target]:
                            sub_cluster_link_count[new_root[source]] += 1
                            # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                            compact[new_root[source]].append((source, target, link_strength))

                        else:
                            # print("\t\t--------------- INTER COMMUNITY ---------------")
                            # print(source, "|", target)
                            update_inter_link()

                    # SOURCE AND TARGET ARE IN DIFFERENT GROUPS BUT IN THE SAME BIN
                    elif source not in added and target in added:

                        group = {source}
                        groups += [group_id]
                        added.add(source)

                        # CREATE A NEW GROUP
                        new_clusters[group_id] = group

                        # GROUP LABEL
                        label_map[group_id] = F"{label_prefix}{source}"

                        # DOCUMENT THE GROUP A NODE BELONGS TO
                        new_root[source] = group_id

                        # DOCUMENT THE ALL MAP
                        group_map[group_id] = constraint_key

                        #  NO LINK TO ADD BECAUSE SOURCE AND TARGET ARE IN DIFFERENT GROUPS
                        if new_root[source] != new_root[target]:
                            # print("\t\t--------------- INTER COMMUNITY ")
                            # print(source, "|", target)

                            update_inter_link()

                    # SOURCE AND TARGET ARE IN DIFFERENT GROUPS BUT IN THE SAME BIN
                    elif source in added and target not in added:

                        group = {target}
                        groups += [group_id]
                        added.add(target)

                        # CREATE A NEW GROUP
                        new_clusters[group_id] = group

                        # GROUP LABEL
                        label_map[group_id] = F"{label_prefix}{target}"

                        # DOCUMENT THE GROUP A NODE BELONGS TO
                        new_root[target] = group_id

                        # DOCUMENT THE ALL MAP
                        group_map[group_id] = constraint_key

                        #  NO LINK TO ADD BECAUSE SOURCE AND TARGET ARE IN DIFFERENT GROUPS
                        if new_root[source] != new_root[target]:
                            # print("\t\t--------------- INTER COMMUNITY ")
                            # print(source, "|", target)

                            update_inter_link()

                # 2. THE TARGET NODE HAS NO GROUP
                elif src_pos is not None and trg_pos is None:

                    if target not in added:

                        # AT SOURCE POSITION, ADD TARGET
                        # groups[src_pos].add(target)
                        added.add(target)

                        #  ADD TO AN EXISTING GROUP
                        new_clusters[new_root[source]].add(target)

                        # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                        compact[new_root[source]].append((source, target, link_strength))

                        # DOCUMENT THE GROUP A NODE BELONGS TO
                        new_root[target] = new_root[source]

                        # ADD A WITHIN GROUP LINK CONT FOR THE GROUP
                        if new_root[source] in sub_cluster_link_count:
                            sub_cluster_link_count[new_root[source]] += 1
                        else:
                            sub_cluster_link_count[new_root[source]] = 1

                    else:

                        if new_root[source] == new_root[target]:

                            if new_root[source] in sub_cluster_link_count:
                                sub_cluster_link_count[new_root[source]] += 1
                            else:
                                sub_cluster_link_count[new_root[source]] = 1

                            # sub_cluster_link_count[new_root[source]] += 1
                            # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                            compact[new_root[source]].append((source, target, link_strength))

                        else:
                            # print("\t\t--------------- INTER COMMUNITY ---------------")
                            # print(source, "|", target)

                            update_inter_link()

                # 3. THE SOURCE NODE HAS NO GROUP
                elif src_pos is None and trg_pos is not None:

                    if source not in added:

                        # ADD THE SOURCE AT THE TARGET'S POSITION
                        # groups[trg_pos].add(source)
                        added.add(source)

                        #  ADD TO AN EXISTING GROUP
                        new_clusters[new_root[target]].add(source)

                        # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                        compact[new_root[target]].append((source, target, link_strength))

                        # DOCUMENT THE NEW GROUP THE SOURCE BELONGS TO
                        new_root[source] = new_root[target]

                        # ADD A WITHIN GROUP LINK COUNT FOR THE GROUP
                        if new_root[target] in sub_cluster_link_count:
                            sub_cluster_link_count[new_root[target]] += 1
                        else:
                            sub_cluster_link_count[new_root[target]] = 1

                    else:
                        if new_root[source] == new_root[target]:
                            sub_cluster_link_count[new_root[source]] += 1
                            # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                            compact[new_root[source]].append((source, target, link_strength))
                        else:
                            # print("\t\t--------------- INTER COMMUNITY ---------------")
                            # print(source, "|", target)

                            update_inter_link()

                # 4. SOURCE AND TARGET ARE IN DIFFERENT GROUPS
                elif src_pos is not None and trg_pos is not None and src_pos != trg_pos:

                    # SOURCE IS IN THE BIGGEST CLUSTER
                    trg_grp = new_clusters[new_root[target]]
                    src_grp = new_clusters[new_root[source]]
                    if len(src_grp) > len(trg_grp):

                        big = src_grp
                        small = trg_grp
                        del_key = new_root[target]
                        source_id = new_root[source]

                        # THE LABEL OF THE SMALL GETS REMOVED
                        del label_map[new_root[target]]

                        # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                        compact[new_root[source]].append((source, target, link_strength))

                        compact[new_root[source]] += compact[new_root[target]]
                        del compact[new_root[target]]

                        for item in small:

                            big.add(item)

                            #  ADD TO AN EXISTING GROUP
                            new_clusters[source_id].add(item)

                            # DOCUMENT THE GROUP A NODE BELONGS TO
                            new_root[item] = new_root[source]

                        # A NEW LINK IS ADDED ==> 1 ADD THE LINK-COUNT OF THE SMALL GROUP
                        if del_key in sub_cluster_link_count:

                            sub_cluster_link_count[source_id] += 1 + sub_cluster_link_count[del_key]

                            # DELETE THE EXISTING COUNT
                            del sub_cluster_link_count[del_key]

                        else:
                            sub_cluster_link_count[source_id] += 1

                        update_inter_link(delete=del_key, is_source=False)

                        # REMOVE THE TARGET GROUP AS IT GOT MERGED
                        del new_clusters[del_key]

                        # REMOVE THE TARGET GROUP MERGED
                        del group_map[del_key]

                        # del sub_cluster_link_count[del_key]
                        # groups.__delitem__(trg_pos)
                        groups.remove(del_key)
                        # print("source")

                    # TARGET IS IN THE BIGGEST CLUSTER
                    else:
                        small = src_grp
                        big = trg_grp
                        del_key = new_root[source]
                        target_id = new_root[target]

                        # THE LABEL OF THE SMALL GETS REMOVED
                        del label_map[new_root[source]]

                        # EXTRACT CHILDREN OF COMPACT THAT ARE BIGGEST THAN 2
                        compact[new_root[target]].append((source, target, link_strength))

                        compact[new_root[target]] += compact[new_root[source]]
                        del compact[new_root[source]]

                        for item in small:

                            big.add(item)

                            #  ADD TO AN EXISTING GROUP
                            new_clusters[new_root[target]].add(item)

                            # DOCUMENT THE GROUP A NODE BELONGS TO
                            new_root[item] = new_root[target]

                        # A NEW LINK IS ADDED ==> 1 ADD THE LINK-COUNT OF THE SMALL GROUP
                        if del_key in sub_cluster_link_count:

                            if target_id in sub_cluster_link_count:
                                sub_cluster_link_count[target_id] += 1 + sub_cluster_link_count[del_key]
                            else:
                                sub_cluster_link_count[target_id] = 1 + sub_cluster_link_count[del_key]

                            # DELETE THE EXISTING COUNT
                            del sub_cluster_link_count[del_key]

                        else:
                            if target_id in sub_cluster_link_count:
                                sub_cluster_link_count[target_id] += 1
                            else:
                                sub_cluster_link_count[target_id] = 1

                        update_inter_link(delete=del_key, is_source=True)

                        del new_clusters[del_key]
                        del group_map[del_key]
                        # groups.__delitem__(src_pos)
                        groups.remove(del_key)
                        # print("target")

                # 5. SOURCE AND TARGETS ARE FOUND BUT NOT IN THE SAME GROUP
                elif src_pos is not None and trg_pos is not None and src_pos == trg_pos:
                    if new_root[source] in sub_cluster_link_count:
                        sub_cluster_link_count[new_root[source]] += 1
                    else:
                        sub_cluster_link_count[new_root[source]] = 1
                    compact[new_root[source]].append((source, target, link_strength))

            # except Exception as err:
            #     print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
            #     print(err)
            #     print(source, target)
            #     print(new_clusters)
            #     print(new_root)

        print(F"\t\tBIN {constraint_key:17} : {len(groups)} group(2)")

        # LONERS
        for group_id in groups:
            group = new_clusters[group_id]
            if len(group) == 1:
                # THE SOURCE OR TARGET IS USED AS THE KEY OF THE LONER
                loners[list(group)[0]] = constraint_key, group_id

    print(F"\t\tDONE WITH STEP 4 IN {datetime.timedelta(seconds=time.time() - step_4)}")

    # ####################################################################################
    print('\n\t5. GENERATE VISUALISATION NODES')
    # ####################################################################################

    # UPDATE THE LABEL IF THE PROPERTIES ARE GIVEN
    step_5 = time.time()
    if specs[St.properties] is None:
        properties_converted = None
    elif St.graph in specs[St.properties][0] and St.data in specs[St.properties][0]:
        properties_converted = specs[St.properties]
    else:
        properties_converted = convert_properties(properties) if properties is not None else None
    node_label()

    for key in new_clusters:

        group_size = len(new_clusters[key])
        possible = group_size * (group_size - 1) / 2

        # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # print(group_size)
        # print(possible)
        # print(sub_cluster_link_count[key] if key in sub_cluster_link_count else 0)

        # MISSING LINKS IS THE PERCENTAGE OF MISSING LINKS
        temp = possible - sub_cluster_link_count[key] if key in sub_cluster_link_count else 0
        temp = temp if temp > 0 else 0
        missing_links = temp / possible if possible > 0 else 0

        # nodes
        if key in group_map:

            if group_size > 1:
                parent_nodes[label_map[key]] = group_size

            node = compact_node(
                node_id=label_map[key], group_size=group_size, strength=group_map[key], missing_links=missing_links,
                group_color=color if color is not None else (1 if group_size == 1 else int(hash_number(key))),
                investigated=investigated, child=None, size=10)

            # COMPACT NODE: ADDING THE CHILD OF THE COMPACT NODE
            if key in compact:
                node['child'] = get_compact_child(key, compact[key], properties_converted, data_store)

            nodes_view += [node]

            if node['missing_links'] < 0:

                print("group_size             :", group_size)
                print("possible               :", possible)
                print("sub cluster link_count :", sub_cluster_link_count[key])
                print("missing                :", node['missing_links'])

    print(F"\t\tDONE WITH STEP 5 IN {datetime.timedelta(seconds=time.time() - step_5)}")

    # ***************************************************
    print('\n\t6. GENERATE VISUALISATION LINKS')
    # ***************************************************
    step_8 = time.time()

    for key, link in inter_links.items():
        # print(link)

        # [link[0]]     -> RETURNS THE RESOURCE
        # [new_root]    -> RETURNS THE SUB-CLUSTER TO WITCH THE RESOURCE BELONGS TO
        # [label_map]   -> RETURNS THE LABEL OF SUB-CLUSTER

        label_1, label_2 = label_map[link[0]], label_map[link[1]]
        strength,distance = link[2], short_distance

        # ORDERING THE LABELS
        if label_1 < label_2:
            source, target = label_1, label_2
            dist_factor = [len(new_clusters[link[0]]), len(new_clusters[link[1]])]
        else:
            source, target = label_2, label_1
            dist_factor = [len(new_clusters[link[1]]), len(new_clusters[link[0]])]

        # GENERATE THE KEY
        labels = F"{source}-{target}"

        current = edge(
            source=source, target=target, strength=strength, distance=distance,
            dist_factor=dist_factor, link_thickness=link_thickness, count=link[3])

        if labels not in link_checker:
            link_view += [current]
            link_checker.add(labels)

        else:

            # UPDATING THE STRENGTH OF THE CONNECTION TO IT MAX STRENGTH
            for dictionary in link_view:
                curr_label = F"{dictionary['source']}-{dictionary['target']}"
                if labels == curr_label:
                    dictionary['strength'] = max(dictionary['strength'], current['strength'])
                    break

    # VISUALISATION OBJECT
    if vis is None:

        vis = vis_object(
            cluster_id=specs["cluster_id"], confidence=0, decision=0, metric="e_Q MESSAGE",
            message_conf="", color=html_color, links=link_view, nodes=nodes_view)

    else:

        vis['links'] += link_view
        vis['nodes'] += nodes_view

    print(F"\t\tDONE WITH STEP 8 IN {datetime.timedelta(seconds=time.time() - step_8)}")
    print(F"\n\t9. THE ALGORITHM FOUND {len(compact)} COMPACT NODES")
    print(F"\n\tDONE IN {datetime.timedelta(seconds=time.time() - step)}")

    # print("\n\n2 CLUSTERS  -->", len(new_clusters), new_clusters)
    # # for key, item in new_clusters.items():
    # #     print("\t", key, len(item), )
    # print("\n\n2 ROOT        -->", len(new_root), new_root)
    # print("\n\n2 GROUP MAP   -->", len(group_map), group_map)
    # print("\n\n2 COUNTS      -->", len(sub_cluster_link_count), sub_cluster_link_count)
    # print("\n\n2 INTER LINKS -->", len(inter_links), inter_links)
    # print("\n\n2 LABEL MAP   -->", len(label_map), label_map)
    # # for item, value in inter_links.items():
    # #     print(item, value)
    # print("\n\n2 COMPACT     -->", len(compact), compact)
    # for ky, comp in compact.items():
    #     print(ky, compact)

    if community_only is False:
        return vis

    return vis_community(vis, strict=True, reducer=node_total_ratio)


def vis_community(vis, strict=True, reducer=sat_reducer, children=None, init=True):

    if children is None:
        children = defaultdict(list)
    else:
        children.clear()

    max = 0
    started = time.time()
    visited_parent = set()
    link_count = defaultdict(int)

    def swallow():

        if len(vis['links']) == 0:
            return

        # SATELLITE MOVES TO PARENT
        # parent_id = parents_id.pop()

        # NEW COMMUNITY
        if parent not in visited_parent:

            # SET THE PARENT AS VISITED
            visited_parent.add(parent)

            # RESET CHILD BY PUTTING THE COPY OF THE CURRENT NODE AS A CHILD
            nodes[parent]['child'] = vis_object(
                cluster_id="666", nodes=deepcopy(nodes[parent]))

            nodes[parent]['satellite'] = 'true'

        # CURRENT PAIR SPACE FOR COMPUTING MISSING LINKS
        pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2
        curr_link_count = round(pairs * (1 - nodes[parent]['missing_links']))

        # INCREMENT THE PARENT'S NODES COUNT
        nodes[parent]['nodes'] += nodes[child]['nodes']
        pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2

        # REMOVE LINK
        removals = []
        for counter, arc in enumerate(vis['links']):

            source_id, target_id = arc['source'], arc['target']
            if source_id == child or target_id == child:

                link_count[parent] = arc['count'] if arc['count'] > 0 else 1
                # print(parent_id, compacts[parent_id]['nodes'], link_count[parent_id], link['count'])

                # ADD THE NODE TO THE NEW CHILD NODE OBJECT
                if nodes[child] not in nodes[parent]['child']['nodes']:
                    nodes[parent]['child']['nodes'] += [nodes[child]]

                # REMOVE THE SATELLITES FROM THE NODE OBJECT
                if nodes[child] in vis['nodes']:
                    removals.append(counter)
                    vis['nodes'].remove(nodes[child])

        # ADD CHILD LINK COUNT IF IT IS A COMPACT NODE
        if nodes[child]['nodes'] > 1:
            child_pairs = nodes[child]['nodes'] * (nodes[child]['nodes'] - 1) / 2
            child_curr_link_count = round(child_pairs * (1 - nodes[child]['missing_links']))
            link_count[parent] += child_curr_link_count

        # REMOVE A SATELLITE LINK
        for remove_idx in removals:

            # ADD THE LINK TO THE NEW CHILD
            nodes[parent]['child']['links'] += [vis['links'][remove_idx]]

            # REMOVE THE SATELLITE=PARENT LINK FROM THE CURRENT VIS
            vis['links'].__delitem__(remove_idx)

        nodes[parent]['missing_links'] = (pairs - (curr_link_count + link_count[parent]))/float(pairs)

    def swallow_complex():

        global arc, parent
        biggest_list = []
        removals = []

        if len(vis['links']) == 0:
            return

        #  DECIDE THE PARENTS WHO GETS TO SWALLOW THE CHILD
        if strict is False:
            "NO NEED TO MODIFY SATELLITES WITH MORE THAN ONE PARENT"
            pass

        # print("CHILD", child)
        # FIND PARENTS WITH THE BIGGEST STRENGTH
        for arc in vis['links']:
            src_id, trg_id = arc['source'], arc['target']

            # THE TARGET IS THE PARENT
            if src_id == child:  # and trg_id in parents:

                if len(biggest_list) == 0 or biggest_list[0][1] < arc['strength']:
                    biggest_list = [(trg_id, arc['strength'])]
                elif biggest_list[0][1] == arc['strength']:
                    biggest_list += [(trg_id, arc['strength'])]

            # THE SOURCE IS THE PARENT
            elif trg_id == child:  # and src_id in parents:
                if len(biggest_list) == 0 or biggest_list[0][1] < arc['strength']:
                    biggest_list = [(src_id, arc['strength'])]
                elif biggest_list[0][1] == arc['strength']:
                    biggest_list += [(src_id, arc['strength'])]

        # FROM PARENTS WITH THE BIGGEST STRENGTH, GET THE ONE WITH THE MOST NODES
        biggest_parent = None
        for cid, strength in biggest_list:
            if biggest_parent is None:
                biggest_parent = cid
            else:
                if nodes[biggest_parent]['nodes'] <= nodes[cid]['nodes']:
                    biggest_parent = cid

        if biggest_parent is None:
            print(biggest_list)
            print("\t!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # print(parents)
            # print(children)
            # print(vis['links'])
            exit()
            return

        # SATELLITE MOVES TO PARENT
        parent = biggest_parent

        # NEW COMMUNITY
        if parent not in visited_parent:

            # SET THE PARENT AS VISITED
            visited_parent.add(parent)

            # RESET CHILD BY PUTTING THE COPY OF THE CURRENT NODE AS A CHILD
            nodes[parent]['child'] = vis_object(
                cluster_id="666", nodes=deepcopy(nodes[parent]))

        nodes[parent]['satellite'] = 'true'

        # CURRENT PAIR SPACE FOR COMPUTING MISSING LINKS
        pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2
        curr_link_count = round(pairs * (1 - nodes[parent]['missing_links']))

        # INCREMENT THE PARENT'S NODES COUNT
        nodes[parent]['nodes'] += nodes[child]['nodes']
        pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2

        # REMOVE A SATELLITE NODE FROM THE VIS OBJECT AND COLLECT THE LINKS TO BE REMOVED FROM THE VIS LINK OBJECT
        for counter, arc in enumerate(vis['links']):

            src_id, trg_id = arc['source'], arc['target']
            if src_id == child or trg_id == child:

                link_count[parent] = arc['count'] if arc['count'] > 0 else 1

                # ADD THE NODE TO THE NEW CHILD NODE OBJECT
                if nodes[child] not in nodes[parent]['child']['nodes']:
                    nodes[parent]['child']['nodes'] += [nodes[child]]

                # REMOVE THE SATELLITES FROM THE NODE OBJECT
                if nodes[child] in vis['nodes']:
                    vis['nodes'].remove(nodes[child])

                # COLLECT THE LINKS TO BE REMOVED FROM THE VIS LINK OBJECT
                removals.append(counter)

        # ADD CHILD LINK COUNT IF IT IS A COMPACT NODE
        if nodes[child]['nodes'] > 1:
            child_pairs = nodes[child]['nodes'] * (nodes[child]['nodes'] - 1) / 2
            child_curr_link_count = round(child_pairs * (1 - nodes[child]['missing_links']))
            link_count[parent] += child_curr_link_count

        # REORDER SO THAT THE DELETION OF SMALLER INDEX DO NOT MESS-UP THE DELETION OF LARGER INDEX
        removals = sorted(removals, reverse=True)

        # REMOVE A SATELLITE LINK
        for remove_idx in removals:

            # LINK TO REMOVE
            source, target = vis['links'][remove_idx]["source"], vis['links'][remove_idx]['target']

            if source == parent or target == parent:

                # ADD THE LINK TO THE NEW CHILD
                nodes[parent]['child']['links'] += [vis['links'][remove_idx]]

                # REMOVE THE SATELLITE=PARENT LINK FROM THE CURRENT VIS
                del vis['links'][remove_idx]

            else:

                check = False

                if source == child:

                    # MODIFY THE LINK TO POINT TO THE SATELLITE PARENT AND NOT TO THE SATELLITE ITSELF
                    # BUT BECAUSE THE LINK ALREADY EXIST, NOW ONLY INCREMENT THE INTER-LINK COUNT
                    for inter_link in vis['links']:
                        # for i in removals:
                        #     inter_link = vis['links'][i]
                        inter_source, inter_target = inter_link['source'], inter_link['target']

                        if inter_source in [parent, target] and inter_target in [parent, target]:
                            inter_link['count'] += vis['links'][remove_idx]['count']
                            check = True

                            # REMOVE THE SATELLITE-PARENT LINK FROM THE CURRENT VIS
                            del vis['links'][remove_idx]

                    # MODIFY THE LINK TO POINT TO THE SATELLITE PARENT AND NOT TO THE SATELLITE ITSELF
                    if check is False:
                        vis['links'][remove_idx]['source'] = parent
                        # removals.remove(remove_idx)

                elif target == child:

                    # MODIFY THE LINK TO POINT TO THE SATELLITE PARENT AND NOT TO THE SATELLITE ITSELF
                    # BUT BECAUSE THE LINK ALREADY EXIST, NOW ONLY INCREMENT THE INTER-LINK COUNT
                    for inter_link in vis['links']:
                        # for i in removals:
                        #     inter_link = vis['links'][i]
                        inter_source, inter_target = inter_link['source'], inter_link['target']

                        if inter_source in [parent, source] and inter_target in [parent, source]:
                            inter_link['count'] += vis['links'][remove_idx]['count']
                            check = True

                            # REMOVE THE SATELLITE=PARENT LINK FROM THE CURRENT VIS
                            del vis['links'][remove_idx]

                    # MODIFY THE LINK TO POINT TO THE SATELLITE PARENT AND NOT TO THE SATELLITE ITSELF
                    if check is False:
                        vis['links'][remove_idx]['target'] = parent
                        # removals.remove(remove_idx)

        nodes[parent]['missing_links'] = (pairs - (curr_link_count + link_count[parent]))/float(pairs)

    if len(vis['links']) == 0:
        return vis

    print_heading(F"CONVERTING THE VIS OBJECT INTO COMMUNITIES ONLY WITH REDUCER SET TO {reducer}")

    # DOCUMENTING IDS OF SOURCE OR TARGET AS KEY OR LIST IN THE VALUE POSITION
    nodes, parents = dict(), defaultdict(list)

    print("\n\t1. DICTIONARY OF THE NODES")
    for node in vis['nodes']:
        nodes[node['id']] = node
        if 'nodes' in node and max < node['nodes']:
            max = node['nodes']

    # ##################################################################################
    print("\t2. ALLOWING BIGGER COMPACT NODES TO BECOME SATELLITE")
    # ##################################################################################
    if reducer:
        if reducer >= max:
            reducer = max - 5
            print(F"\t5. THE CONVERSION NOW RETURN A VISUALISATION "
                  F"OF {len(vis['nodes'])} NODES WITH A REDUCER OF {reducer}.")

    # ##################################################################################
    so_far = datetime.timedelta(seconds=time.time() - started)
    print("\t{:55}{} SO FAR".format("3. PARENT VERSUS CHILDREN", so_far))
    # ##################################################################################
    for arc in vis['links']:

        source, target = arc['source'], arc['target']

        if 'nodes' in nodes[source] and nodes[source]['nodes'] > nodes[target]['nodes']:

            if nodes[target]['nodes'] <= reducer:
                parents[source].append(target)
                children[target].append(source)
                # if target in children:
                #     children[target].append(source)
                # else:
                #     children[target] = [source]
        else:
            if 'nodes' in nodes[source] and nodes[source]['nodes'] <= reducer:
                parents[target].append(source)
                children[source].append(target)
                # if source in children:
                #     children[source].append(target)
                # else:
                #     children[source] = [target]

    so_far = datetime.timedelta(seconds=time.time() - started)
    print("\t{:55}{} SO FAR".format("4. ORDER THE CHILDREN DICTIONARY", so_far))

    # ##################################################################################
    so_far = datetime.timedelta(seconds=time.time() - started)
    print("\t{:55}{} SO FAR".format("5. ITERATE THROUGH PARENTS FOR LEAVES", so_far))
    # ##################################################################################

    cond = False
    for parent, infants in parents.items():

        for child in infants:

            # SINGLE PARENT LEAF CHILD
            if child not in parents and len(children[child]) == 1:
                swallow()
                cond = True
                # print("\t\tDELETING CHILD 1:", child)
                del children[child]

    if cond:
        cond = False
        vis_community(vis, strict=strict, reducer=reducer, children=children, init=False)

        sorted_children = dict(sorted(children.items(), key=lambda item: nodes[item[0]]['nodes']))
        for child, parents_ in sorted_children.items():
            swallow_complex()
            cond = True
            # print("\t\tDELETING CHILD 2:", child)
            del children[child]

        if cond:
            vis_community(vis, strict=strict, reducer=reducer, children=children, init=False)

    if init is True:
        so_far = datetime.timedelta(seconds=time.time() - started)
        print("\t{:55}{}".format("DONE IN", so_far))
        print(F"\n\tTHE CONVERSION NOW RETURNS A VISUALISATION OF {len(vis['nodes'])} NODES WITH A REDUCER OF {reducer}.")

    return vis


def vis_object(
        cluster_id, confidence=0, decision=0, metric="", message_conf="", color='#FFFFE0', links=None, nodes=None):

    # CREATE A VISUALISATION OBJECT, UPDATE IT AND RETURN IT
    vis = {
        "id": cluster_id,
        "confidence": confidence,
        "decision": decision,
        "metric": metric,
        "messageConf": message_conf,
        "nodes": [],
        "links": [],
        "page_color": color
    }

    # LIST OF DICTIONARY OBJECTS (NODES)
    if nodes:

        vis['nodes'] += nodes if isinstance(nodes, list) else [nodes]

    # LIST OF DICTIONARY OBJECTS (LINKS)
    if links:
        vis['links'] += links if isinstance(links, list) else [links]

    return vis


def compact_node(node_id: str, group_size: int, strength: float, missing_links: int,
                 group_color: int, investigated: bool, child: vis_object, size: int = 10):

    node = {
        'id': node_id,
        'size': size,
        'nodes': group_size,
        'strength': strength,
        'group': group_color,
        'missing_links': missing_links,
        'investigated': str(investigated).lower(),
    }

    if child:
        node['child'] = child

    return node


def vis_node(node_id, uri, group_color, investigated):

    # CREATE THE NODE OBJECT FOR VISUALISATION
    node_dict = {
        'id': node_id,
        "uri": uri,
        "group": group_color,
        "size": 5
    }

    if investigated is True:
        node_dict['investigated'] = str(investigated).lower()
        node_dict["size"] = 8

    return node_dict


def edge(source, target, strength, distance, dist_factor, link_thickness=2, count=1):

    return {
        'source': source,
        'target': target,
        'count': count,
        'strength': strength,
        'distance': distance,
        'dist_factor': dist_factor,
        "dash": F"3,{20 * (1 - float(strength))}",
        'color': 'red' if float(strength) < 1 else "black",
        'value': 4 if count == 1 else count * link_thickness,
    }


def association_edge(source, target, dist_factor, count=1):

    return {
        'count': count,
        "value": 1,
        "color": "purple",
        "dash": "20,10,5,5,5,10",
        "distance": related_distance,
        'dist_factor': dist_factor,
        "source": source,
        "target": target,
    }


def get_compact_child(key, child, properties, data_store):

    # THIS FUNCTION COMPLEMENTS PLOT COMPACT AS IT PLOTS
    # THE COMPACT GROUPS FOUND BY THE PLOT COMPACT FUNCTION

    visualisation_obj = None
    investigated = True

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
            "distance": related_distance if association is True else short_distance, "value": 4,
            "color": "purple" if association is True else("black" if link[2] == 1 else "red"),
            "dash": "20,10,5,5,5,10" if association is True else F"3,{20 * (1 - link[2])}"
        }
        vis_data["links"].append(link_dict)

    # FETCH THE
    label_map = dict()
    resources = list(nodes)
    # print_object(resource, overview=False)
    # QUERY FOR FETCHING THE LABEL
    query = Middleware.node_labels_switcher[data_store](resources=resources, targets=properties)

    # FETCHING THE LABELS
    table = None
    if data_store in Middleware.run_query_matrix_switcher and query:
        result = Middleware.run_query_matrix_switcher[data_store](query)
        Stardog.display_matrix(result, spacing=130, is_activated=False)
        table = result[St.result] if isinstance(result, dict) else result

    if properties is not None and table is not None:

        for i in range(1, len(table)):
            formatted = to_nt_format(table[i][0])
            db_label = get_uri_local_name_plus(table[i][1])
            underscore = db_label.split("__")
            db_label = underscore[1] if len(underscore) > 1 else db_label
            label = F"-- {table[i][3]} ({db_label}_{hasher(formatted)})"

            if formatted not in label_map:
                label_map[formatted] = label
                node_dict = {
                    'id': label,
                    "uri": formatted,
                    "group": hash_number(hasher(db_label)),
                    "size": "8" if visualisation_obj is None else "5"
                }

                if investigated is True:
                    node_dict['investigated'] = str(investigated).lower()
                    node_dict["size"] = 8

                # print("node--> ", node_dict)
                vis_data["nodes"].append(node_dict)

            # else:
            #     print(F"DUPLICATED NODE: {formatted} {label_map[formatted]} !!!!!!!!!!!!!!!!!")

        for link in vis_data["links"]:
        # print("-->", link['source'],label_map[link['source']][0])
            link['source'] = label_map[link['source']]
            link['target'] = label_map[link['target']]

    else:

        # CREATE THE NODE OBJECT FOR VISUALISATION
        for node in resources:
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


    # for link in vis_data["links"]:
    #     # print("-->", link['source'],label_map[link['source']][0])
    #     link['source'] = label_map[link['source']]
    #     link['target'] = label_map[link['target']]

    # host = "http://localhost:63342/LenticularLens/src/LLData/Validation/{}"
    # with open(join(CLUSTER_VISUALISATION_DIR, "data_compact.json"), mode='w') as compact_file:
    #     json.dump(vis_data, compact_file)
    # web.open_new_tab(host.format('Compact_vis.html'))
    # time.sleep(3)

    return vis_data


def plot_compact_child(children):

    # THIS FUNCTION COMPLEMENTS PLOT COMPACT AS IT PLOTS
    # THE COMPACT GROUPS FOUND BY THE PLOT COMPACT FUNCTION

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
                "distance": related_distance if association is True else short_distance, "value": 4,
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

        # with open(join(CLUSTER_VISUALISATION_DIR, "data_compact.json"), mode='w') as compact_file:
        #     json.dump(vis_data, compact_file)
        # web.open_new_tab(host.format('Compact_vis.html'))
        # time.sleep(3)

        return vis_data


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

    delta = None
    the_delta = F"\nWITH A DELTA OF {delta}" if delta is not None else ""
    print_heading(F"PLOTTING THE ILN IN A COMPACT REPRESENTATION WITH EVIDENCE{the_delta}")

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

    association_file = join(CSV_ASSOCIATIONS_DIR, specs['associations'])

    # LOOK FOR THE NODES IN ASSOCIATION
    associations = find_associations(specs['cluster_data']['nodes'], association_file)

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
                    "distance": related_distance,
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
    reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt.gz")
    root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt.gz")

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
    association_file = join(CSV_ASSOCIATIONS_DIR, specs['associations'])

    # LOOK FOR THE NODES IN ASSOCIATION
    associations = find_associations(list(overall_nodes), association_file)

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
    root = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['sub_clusters']}-2.txt.gz")

    # THE DICTIONARY OF THE CLUSTERS
    clusters = pickle_deserializer(serialised_folder=CLUSTER_SERIALISATION_DIR, name=F"{specs['sub_clusters']}-1.txt.gz")

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
                        "distance": related_distance,
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
