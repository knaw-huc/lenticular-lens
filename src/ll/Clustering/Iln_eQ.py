import networkx as nx
from io import StringIO as Buffer
from ll.Generic.Utility import combinations
# from os.path import join
# import json
from ll.Generic.Utility import get_key, problem
# from ll.Clustering.SimpleLinkClustering import cluster_vis_input


def sigmoid(x):
    # return math.exp(x)/ (math.exp(x) + 1)
    # return x / float(math.fabs(x) + 1)
    # return math.exp(x) / (math.exp(x) + 10)
    return x / float(abs(x) + 1.6)


# METRIC DESCRIBING THE QUALITY OF A LINKED NETWORK
def metric(graph, strengths=None, alt_keys=None, hyper_parameter_1=0.1, hyper_parameter_2=0.25, has_evidence=False):

    # print "\n- STRENGTHS:", strengths
    # print "- ALT KEYS:", alt_keys

    """
    :param graph: THE GRAPH TO EVALUATE
                  IT IS THE LIST OF EDGES MODELLED AS TUPLES

    :param strengths: STRENGTH OF THE GRAPHS'S EDGES
                      IT IS A DICTIONARY WHERE THE KEY IS PROVIDED WITH THE
                      FUNCTION get_key(node_1, node_2) FROM THE UTILITY FILE

    :param alt_keys: IF GIVEN, IS THE KEY MAPPING OF GHE COMPUTED KEY HERE AND THE REAL KEY.
    AN EXAMPLE CA BE FOUND IN THE FUNCTION cluster_d_test IN THIS CODE

    :param hyper_parameter_1: = THE THRESHOLD FOR AN ILN TO BE FLAGGED GOOD

    :param hyper_parameter_2: THE GRAY ARRAY INTERVAL

    :param has_evidence: A BOOLEAN ATTRIBUTE FOR NOTIFYING WHETHER THE GRAPH HAS ASSOCIATION

    :return:
    """

    analysis_builder = Buffer()

    # def get_key(node_1, node_2):
    #     strength_key = "key_{}".format(str(hash((node_1, node_2))).replace("-", "N")) if node_1 < node_2 \
    #         else "key_{}".format(str(hash((node_2, node_1))).replace("-", "N"))
    #     return strength_key

    # CREATE THE NETWORKS GRAPH OBJECT
    g = nx.Graph()

    """""""""""""""""""""""""""""""""""""""
    LOADING THE NETWORK GRAPH OBJECT...
    """""""""""""""""""""""""""""""""""""""
    # ADD NODE TO THE GRAPH OBJECT
    # nodes = set([n1 for n1, n2 in graph] + [n2 for n1, n2 in graph])
    nodes = set([data[0] for data in graph] + [data[1] for data in graph])
    for node in nodes:
        g.add_node(node)

    # ADD EDGES TO THE GRAPH OBJECT
    for edge in graph:
        # print edge[0], edge[1],"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        # RECOMPOSE THE KEY FOR EXTRACTING THE WEIGHT OF AN EDGE
        # print("edge:", edge)

        strength_key = get_key(edge[0], edge[1])

        if alt_keys is not None:
            strength_key = alt_keys[strength_key]

        # MAXIMUM WEIGHT FROM THE LIST OF WEIGHTS AVAILABLE FOR THE CURRENT EDGE
        if strength_key in strengths:
            # print "strengths[strength_key] = ", strengths[strength_key]
            strength_value = max(strengths[strength_key])
            # g.add_edges_from([(edge[0], edge[1], {'capacity': 12, 'weight': 2 - float(strength_value)})])
            # ADDING THE EDGE, THE EDGE'S WEIGHT AND CAPACITY
            # print edge[0], edge[1]
            g.add_edge(edge[0], edge[1], capacity=2, weight=float(strength_value))

        else:
            problem(text="THE LINK KEY IS INCORRECT")
        #     g.add_edge(edge[0], edge[1], capacity=2, weight=float(1))

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    1. ORIGINAL METRIC COMPUTATIONS WITHOUT WEIGHT
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    bridges_list = []
    nb_used, nd_used, nc_used = "na", "na", "na"
    edge_discovered, node_count, edge_derived, bridges = 0, 0, 0, 0

    try:
        # TOTAL NUMBER OF NODES IN THE GRAPH
        node_count = len(nodes)

        # TOTAL NUMBER OF DISCOVERED EDGES
        edge_discovered = len(graph)

        # TOTAL NUMBER OF DERIVED EDGES (POSSIBLE EDGES)
        edge_derived = node_count * (node_count - 1) / 2

        # A LIST OF BRIDGES (BRIDGE EDGE)
        bridges_list = list(nx.bridges(g))

        # TOTAL NUMBER OF BRIDGES IN THE NETWORK
        bridges = 0 if has_evidence is True and node_count == 2 else len(bridges_list)
        # print "BRIDGES:", bridges

        "NEW CODE FOR PRINTING THE NETWORK"
        # nodes_print = list(dict(g.nodes(data=True)).keys())
        # edge_print = list(g.edges(data=True))
        # specs = {
        #
        #     # THE ACTIVATED DATA STORE
        #     "data_store": "STARDOG",
        #
        #     # 1. THE SERIALISED DATA
        #     "serialised": '_PHDemoClusters_',
        #
        #     # THE CLUSTER ID
        #     "cluster_id": "123",
        #
        #     # MORE INFORMATION ON THE CLUSTER TO VISUALISE
        #     "cluster_data": {
        #
        #         "nodes": nodes_print,
        #
        #         'strengths': strengths,
        #
        #         "links": edge_print
        #     },
        #
        #     # THE PROPERTIES SELECTED BY THE USER
        #     "properties": [
        #
        #         # MARRIAGE
        #         {"dataset": "http://goldenagents.org/datasets/Marriage003",
        #          "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
        #          "property": "http://goldenagents.org/uva/SAA/ontology/full_name"},
        #
        #         # ECARTICO
        #         {"dataset": "http://goldenagents.org/datasets/Ecartico",
        #          "entity_type": "http://www.vondel.humanities.uva.nl/ecartico/ontology/Person",
        #          "property": "http://www.vondel.humanities.uva.nl/ecartico/ontology/full_name"},
        #
        #         # BAPTISM
        #         {"dataset": "http://goldenagents.org/datasets/Baptism002",
        #          "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
        #          "property": "http://goldenagents.org/uva/SAA/ontology/full_name"},
        #
        #         # BURIAL
        #         {"dataset": "http://goldenagents.org/datasets/Burial008",
        #          "entity_type": "http://goldenagents.org/uva/SAA/ontology/Person",
        #          "property": "http://goldenagents.org/uva/SAA/ontology/full_name"},
        #
        #     ]
        # }
        #
        # vis = cluster_vis_input(specs, visualisation_obj=None, resources_obj=None,
        #                   dataset_obj=None, sub_clusters=None, root=None, investigated=True, activated=True)
        # from ll.LLData.Validation import CLUSTER_VISUALISATION_DIR
        # with open(join(CLUSTER_VISUALISATION_DIR, "eQ.json"), mode='w') as file:
        #     json.dump(vis, file)
        "END NEW CODE FOR PRINTING THE NETWORK"

        # THE NETWORK DIAMETER
        diameter = nx.diameter(g)
        # NETWORK METRIC ELEMENTS
        # try:
        normalised_closure = float(edge_discovered) / float(edge_derived) if edge_derived != 0 else 0
        normalised_bridge = float(bridges / float(len(nodes) - 1)) if node_count > 1 else 0
        normalised_diameter = (float(diameter - 1) / float(len(nodes) - 2)) \
            if len(nodes) > 2 else (float(diameter - 1) if diameter >= 1 else 0)
        # except:
        #     print "AN ERROR WITH THE COMPUTATION OF THE METRIC...."

        # FINAL NORMALISATION (NORMALISATION USED FOR NON WEIGHTED METRIC COMPUTATION)
        nb_used = sigmoid(bridges) if sigmoid(bridges) > normalised_bridge else normalised_bridge
        nd_used = sigmoid(diameter - 1) if sigmoid(diameter - 1) > normalised_diameter else normalised_diameter
        nc_used = 1 - normalised_closure

        # THE METRICS NEGATIVE IMPACTS
        impact = (nb_used + nd_used + nc_used) / float(3)

        # THE METRIC QUALITY EVALUATION
        estimated_quality = round(1 - impact, 3)

    except nx.NetworkXError as error:

        impact = 1
        estimated_quality = 0
        diameter = node_count - 1
        print("GRAPH:{}\nNODES: {}\nEDGE DISCOVERED: {}".format(g, node_count, edge_discovered))
        print(error)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    2. WEIGHTED METRIC COMPUTATIONS OPTION 1: AVERAGE AND MINIMUM
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    max_strengths = {}
    min_strength = 1
    average_strength = 1
    if strengths is not None:

        # MAXIMUM WEIGHT FOR EACH EDGE
        for key, val in strengths.items():
            max_strengths[key] = float(max(val))

        # MINIMUM WEIGHT IN THE CLUSTER
        min_strength = 0
        if len(strengths.items()) > 0:
            min_strength = min(strengths.items(), key=lambda strength_tuple: max(strength_tuple[1]))
            min_strength = float(max(min_strength[1]))

        average_strength = 0
        if len(max_strengths) > 0:
            average_strength = sum(max_strengths.values()) / float(len(max_strengths))

    weighted_eq = round(estimated_quality * min_strength, 3), round(estimated_quality * average_strength, 3)
    if len(str(estimated_quality)) > 5:
        print("BIGGER", estimated_quality)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    3. WEIGHTED METRIC COMPUTATIONS OPTION 2: ALL INTEGRATED / COMPLETE
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    biggest_cost = 0
    weighted_bridges = 0
    weighted_edge_discovered = 0
    weighted_nb_used, weighted_nd_used, weighted_nc_used = "na", "na", "na"
    try:

        # LIST OF NODES WITH AN ECCENTRICITY EQUAL TO THE NETWORK DIAMETER
        periphery = nx.periphery(g)

        # POSSIBLE PAIRWISE COMBINATIONS OF PERIPHERY NODES FOR COMPUTING BIGGEST COST OF SHORTEST PATH
        link_combinations = combinations(periphery)

        # COMPUTING THE WEIGHTED BRIDGE
        if has_evidence is True and node_count == 2:
            weighted_bridges = 0
        else:
            for node_1, node_2 in bridges_list:
                weighted_bridges += (g.get_edge_data(node_1, node_2))['weight']

        # COMPUTING THE WEIGHTED DIAMETER
        for start, end in link_combinations:

            # A TUPLE WHERE THE FIRST ELEMENT IS THE COST OF THE SHORTEST PATH FOUND (SECOND ELEMENT)
            shortest_path = nx.single_source_dijkstra(g, start, target=end, weight="weight")

            # UPDATING THE SHORTEST PATH COST WITH THE INVERTED WEIGHT PENALTY
            curr_cost = 2 * (len(shortest_path[1]) - 1) - shortest_path[0]

            # UPDATING THE BIGGEST COST
            biggest_cost = curr_cost if curr_cost > biggest_cost else biggest_cost

        # THE WEIGHTED DIAMETER IS THEN THE BIGGEST SHORTEST PATH COST
        weighted_diameter = biggest_cost

        # NORMALISING THE DIAMETER
        if len(nodes) > 2:
            weighted_normalised_diameter = (float(weighted_diameter - 1) / float(len(nodes) - 2))
        else:
            weighted_normalised_diameter = float(weighted_diameter - 1)
        weighted_normalised_diameter = 1 if weighted_normalised_diameter > 1 else weighted_normalised_diameter

        # FIRST NORMALISATION
        weighted_normalised_bridge = float(weighted_bridges / float(len(nodes) - 1)) if node_count > 1 else 0
        weighted_edge_discovered = g.size(weight="weight")

        # print("\tEDGE = {} WEIGHTED EDGE = {} AND DIAMETER = {} ON A GRAPH OF {} NODES".format(
        #     g.size(), weighted_edge_discovered, diameter, len(nodes)))

        weighted_closure = float(weighted_edge_discovered) / float(edge_derived) if edge_derived != 0 else 0

        # SECOND NORMALISATION
        weighted_nb_used = sigmoid(weighted_bridges) \
            if sigmoid(weighted_bridges) > weighted_normalised_bridge else weighted_normalised_bridge

        weighted_nd_used = sigmoid(weighted_diameter - 1) \
            if sigmoid(weighted_diameter - 1) > weighted_normalised_diameter else weighted_normalised_diameter

        weighted_nc_used = round(1 - weighted_closure, 2)

        # WEIGHTED IMPACT
        weighted_impact = (weighted_nb_used + weighted_nd_used + weighted_nc_used) / float(3)
        weighted_eq_2 = round(1 - weighted_impact, 3)

        # print "\t>>> biggest_cost", biggest_cost
        # print "\t>>> weight:", g.size(weight="weight")
        # print "\t>>> bridge weight:", weighted_bridges
        # print "\t>>> Quality [{}] Weighted-Min [{}] Weighted-Avg [{}] Weighted-eQ [{}]".format(
        #     estimated_quality, weighted_eq[0], weighted_eq[1], weighted_eq_2)

    except nx.NetworkXError:

        weighted_impact = 1
        weighted_eq_2 = 0

    """""""""""""""""""""""""""""""""""""""
    4. PRINTING MATRIX COMPUTATIONS
    """""""""""""""""""""""""""""""""""""""
    test = "[MIN: {}]   |   [AVERAGE: {}]   |   [COMPLETE: {}]".format(
        str(weighted_eq[0]), str(weighted_eq[1]), weighted_eq_2)
    # analysis_builder.write(
    #     # "\nMETRICS READING: THE CLOSER TO ZERO, THE BETTER\n"
    #     # "\n\tAverage Degree [{}] \nBridges [{}] normalised to [{}] {}\nDiameter [{}]  normalised to [{}] {}"
    #     # "\nClosure [{}/{}][{}] normalised to [{}]\n\n>>> Decision Support [{}] {} <<<".
    #     # format(average_node_connectivity, bridges, normalised_bridge, nb_used,
    #     #        diameter, normalised_diameter, nd_used,
    #     #        edge_discovered, edge_derived, closure, normalised_closure, interpretation, estimated_quality))
    #
    #         ">>>\tESTIMATED QUALITY [{} | {}]\t<<<"
    #         "\n\tBridges [{}]   Diameter [{}]   Closure [{}/{}] -> [{}]".
    #         format(estimated_quality, test, nb_used, nd_used, edge_discovered,
    #                edge_derived, normalised_closure))

    analysis_builder.write("\t{:25} :  [{}]   |   {}\t".format("ESTIMATED QUALITY", estimated_quality, test))

    # if ratio == 1:
    #     analysis_builder.write("\n\nDiagnose: VERY GOOD")
    # elif average_node_connectivity == 2 or bridges == 0:
    #     analysis_builder.write("\n\nDiagnose: ACCEPTABLE")
    # elif bridges > 0:
    #     analysis_builder.write("\n\nDiagnose : NEED BRIDGE INVESTIGATION")

    # AUTOMATED DECISION FOR WEIGHTED IMPACT RESULT
    # *********************************************
    weighted_quality = {}
    # hyper_parameter_1 = 0.1
    # hyper_parameter_2 = 0.25
    # WEIGHT USING MINIMUM STRENGTH
    if 1 - weighted_eq[0] <= hyper_parameter_1:
        weighted_quality["min"] = "GOOD [{}]".format(weighted_eq[0])
    else:
        weighted_quality["min"] = "BAD [{}]".format(weighted_eq[0])

    # WEIGHT USING AVERAGE STRENGTH
    if 1 - weighted_eq[1] <= hyper_parameter_1:
        weighted_quality["avg"] = "GOOD [{}]".format(weighted_eq[1])
    else:
        weighted_quality["avg"] = "BAD [{}]".format(weighted_eq[1])

    # WEIGHT USING BRIDGE-CLOSURE-DIAMETER STRENGTH
    if 1 - weighted_eq_2 <= hyper_parameter_1:
        weighted_quality["bcd"] = "GOOD [{}]".format(weighted_eq_2)
    else:
        weighted_quality["bcd"] = "BAD [{}]".format(weighted_eq_2)

    # AUTOMATED DECISION FOR NON WEIGHTED IMPACT RESULT
    # *************************************************
    if impact <= hyper_parameter_1:
        # analysis_builder.write("\n\nInterpretation: GOOD")
        auto_decision = "GOOD [{}]".format(estimated_quality)
        analysis_builder.write("\n{:25} : The network is a GOOD representation of a unique real world object".format(
            "INTERPRETATION"))

    elif (bridges == 0) and (diameter < 3):
        auto_decision = "ACCEPTABLE [{}]".format(estimated_quality)
        analysis_builder.write("\n{:25} : The network is an ACCEPTABLE representation of a unique real world object".
                               format("INTERPRETATION"))

    elif ((impact > hyper_parameter_1) and (impact < hyper_parameter_2)) or (bridges == 0):
        # analysis_builder.write("\n\nInterpretation: UNCERTAIN")
        auto_decision = "UNCERTAIN [{}]".format(estimated_quality)
        analysis_builder.write("\n{:25} : We are UNCERTAIN whether the network represents a unique real world object".
                               format("INTERPRETATION"))

    else:
        # analysis_builder.write("\n\nInterpretation: THE NETWORK IS NOT A GOOD REPRESENTATION OF A SINGLE RESOURCE")
        auto_decision = "BAD [{}]".format(estimated_quality)
        analysis_builder.write(
            "\n{:25} : The network is NOT A GOOD representation of a unique real world object".format("INTERPRETATION"))

    # DECISION SUPPORT EXPLAINING WHY A DECISION IS TAKEN
    # ***************************************************
    if bridges > 0:
        # analysis_builder.write("\n\nEvidence: NEED BRIDGE INVESTIGATION")
        analysis_builder.write(" BECAUSE it needs a bridge investigation")

    if diameter > 2:
        # analysis_builder.write("\n\nEvidence:  TOO MANY INTERMEDIATES")
        adding_2 = "and " if bridges > 0 else ""
        adding_1 = "\n" if bridges > 0 else ""
        analysis_builder.write(" {}{:>36}BECAUSE it has too many intermediates".format(adding_1, adding_2))

    if bridges == 0 and diameter <= 2:
        # analysis_builder.write("\n\nEvidence:  LESS INTERMEDIATES AND NO BRIDGE")
        analysis_builder.write(" and BECAUSE there are less intermediate(s) and no bridge")

    analysis_builder.write("\n{:33} : Bridges [{}]   Diameter [{}]   Closure [{}/{} = {}]".format(
        "NON WEIGHTED NETWORK METRICS USED", nb_used, nd_used, edge_discovered, edge_derived, nc_used))

    analysis_builder.write("\n{:33} : Bridges [{}]   Diameter [{}]   Closure [{}/{} = {}]"
                           "   impact: [{}]   quality: [{}]".
                           format("WEIGHTED NETWORK METRICS USED", weighted_nb_used, weighted_nd_used,
                                  round(weighted_edge_discovered, 3), edge_derived, weighted_nc_used,
                                  weighted_impact, 1 - weighted_impact))

    return {'message': analysis_builder.getvalue(), 'decision': impact,
            'AUTOMATED_DECISION': auto_decision, 'WEIGHTED_DECISION': weighted_quality}
