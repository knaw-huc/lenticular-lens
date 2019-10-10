import gzip
import re
import time
import datetime
import traceback
import networkx as nx
from os import stat, remove
from rdflib import util, Graph
import common.ll.Generic.Utility as Ut
import common.ll.Generic.Settings as St
from os.path import join, splitext as get_file_name, basename
from common.ll.Generic.Utility import pickle_serializer, hasher, problem


# TODO: GET PATH OF THE SERIALISED DIRECTORY
# from common.ll.LLData.Serialisation import CLUSTER_SERIALISATION_DIR
CLUSTER_SERIALISATION_DIR = ''


_format = "It is %a %b %d %Y %H:%M:%S"
date = datetime.datetime.today()
_line = "--------------------------------------------------------------" \
        "--------------------------------------------------------------"


# *************************************************************
# *************************************************************
""" USING [SET]  [TABLE OF RESOURCES] AND THEIR [STRENGTHS] """
# *************************************************************
# *************************************************************


def simple_csv_link_clustering(links_iter, key=None, activated=False):

    """
    :param links_iter: ITERABLE LINKS
    :param key:
    :param activated:
    :return:
    """

    if activated is False:
        problem(text="--> THE FUNCTION [simple_csv_link_clustering] IS NOT ACTIVATED.")
        return

    print("\n{:.^100}".format(" WE ARE ABOUT TO CLUSTER AND SERIALISE "))
    print("{:.^100}".format(" *** MAYBE TIME FOR A COFFEE? *** "))

    """
        EXAMPLE OF WHAT WE GET AS CLUSTER
            P1832892825 	{
                'nodes': set(['<http://www.grid.ac/institutes/grid.449957.2>',
                            '<http://risis.eu/eter_2014/resource/NL0028>']),

                'strengths': {('<http://risis.eu/eter_2014/resource/NL0028>',
                         '<http://www.grid.ac/institutes/grid.449957.2>'): ['1', '1']},

                'links': set([('<http://risis.eu/eter_2014/resource/NL0028>',
                         '<http://www.grid.ac/institutes/grid.449957.2>')])
        }
    """

    links = 0

    # THE ROOT KEEPS TRACK OF THE CLUSTER A PARTICULAR NODE BELONGS TOO
    root = dict()

    # THE CLUSTERS DICTIONARY
    clusters = dict()

    # THE FIRST CLUSTER IS UPDATED WITH UNIQUE NAMED AND SAVED IN NEW CLUSTER
    new_clusters = dict()

    # **************************************************************************************************
    # HELPER FUNCTIONS
    # **************************************************************************************************

    def cluster_helper_set(counter, annotate=False):

        counter += 1
        # child_1 = subject.strip()
        # child_2 = obj.strip()

        child_1, child_2 = subject.strip(), t_object.strip()
        child_1 = Ut.to_nt_format(child_1)
        child_2 = Ut.to_nt_format(child_2)

        # DATE CREATION
        the_date = "{}".format(datetime.datetime.today().strftime(_format))

        # CHECK WHETHER A CHILD HAS A PARENT
        has_parent_1 = True if child_1 in root else False
        has_parent_2 = True if child_2 in root else False
        # print "\n{}|{} Has Parents {}|{}".format(child_1, child_2, has_parent_1, has_parent_2)

        # *******************************************
        # 1. START BOTH CHILD ARE ORPHANS
        # *******************************************
        if has_parent_1 is False and has_parent_2 is False:

            # print "\nSTART {}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            # GENERATE THE PARENT
            hash_value = Ut.hasher(the_date + str(links))
            parent = "{}".format(str(hash_value).replace("-", "N")) if str(
                hash_value).startswith("-") \
                else "P{}".format(hash_value)

            # ASSIGN A PARENT TO BOTH CHILD
            root[child_1] = parent
            root[child_2] = parent

            # THE SUBJECT AND OBJECT LINK
            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)

            # THE CLUSTER COMPOSED OF NODES, LINKS AND STRENGTHS
            key_1 = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
            clusters[parent] = {
                'nodes': {child_1, child_2}, 'links': {link}, 'strengths': {key_1: strengths}}
            # print "1",clusters[parent]

            # print parent, child_1, child_2
            if annotate:
                clusters[parent][St.annotate] = "\n\tSTART {} | {}".format(child_1, child_2)

        # *******************************************
        # 2. BOTH CHILD HAVE A PARENT OF THEIR OWN
        # *******************************************
        elif has_parent_1 is True and has_parent_2 is True:

            # 2.1 BOTH CHILD DO NOT HAVE THE SAME PARENT
            if root[child_1] != root[child_2]:

                parent1 = root[child_1]
                parent2 = root[child_2]
                # root2[child_2] = parent1

                if annotate:
                    clusters[parent1][St.annotate] += "\n\tCHOOSE A PARENT {} | {}".format(child_1, child_2)
                # print parent1, parent2

                if parent2 in clusters:

                    # check this
                    # ALL CHILD OF PARENT (SMALL) ARE REASSIGNED A NEW PARENT
                    for child in clusters[parent2]['nodes']:
                        root[child] = parent1

                    # print 'before', clusters2[parent1]['nodes']
                    # RE-ASSIGNING THE NODES OF CHILD 2
                    clusters[parent1]['nodes'] = clusters[parent1]['nodes'].union(clusters[parent2]['nodes'])

                    # RE-ASSIGNING THE LINKS OF CHILD 2
                    clusters[parent1]['links'] = clusters[parent1]['links'].union(clusters[parent2]['links'])

                    # RE-ASSIGNING THE STRENGTHS OF CHILD 2
                    for i_key, link_strengths in clusters[parent2]['strengths'].items():
                        if i_key not in clusters[parent1]['strengths']:
                            clusters[parent1]['strengths'][i_key] = link_strengths
                        else:
                            clusters[parent1]['strengths'][i_key] += link_strengths

                    # print 'after', clusters2[parent1]['nodes']

                    # add the current link (child_1, child_2)
                    link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                    clusters[parent1]['links'].add(link)

                    # link_hash = str(hash(link))
                    link_hash = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
                    if link_hash in clusters[parent1]['strengths']:
                        clusters[parent1]['strengths'][link_hash] += strengths
                    else:
                        clusters[parent1]['strengths'][link_hash] = strengths

                    clusters.pop(parent2)

            # 2.2 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            else:
                parent = root[child_1]
                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += strengths
                else:
                    clusters[parent]['strengths'][link_hash] = strengths

                if annotate:
                    clusters[root[child_1]][St.annotate] += "\n\tSAME PARENTS {} | {}".format(child_1, child_2)

        # *******************************************
        # 3. BOTH CHILD HAVE DIFFERENT PARENTS
        # *******************************************
        elif has_parent_1 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_1]
            root[child_2] = parent

            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
            clusters[parent]['links'].add(link)
            clusters[parent]['nodes'].add(child_2)

            # link_hash = str(hash(link))
            link_hash = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
            if link_hash in clusters[parent]['strengths']:
                clusters[parent]['strengths'][link_hash] += strengths
            else:
                clusters[parent]['strengths'][link_hash] = strengths

            if annotate:
                clusters[parent][St.annotate] += "\n\tONLY 1 {} HAS A PARENT COMPARED TO {}".format(
                    child_1, child_2)

        # *******************************************
        # 4. BOTH CHILD HAVE DIFFERENT PARENTS
        # *******************************************
        elif has_parent_2 is True:

            # THE CHILD WITH NO PARENT IS ASSIGNED TO THE PARENT OF THE CHILD WITH PARENT
            # print "\n{}:{} | {}:{}".format(child_1, has_parent_1, child_2, has_parent_2)

            parent = root[child_2]
            root[child_1] = parent

            link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
            clusters[parent]['links'].add(link)
            clusters[parent]['nodes'].add(child_1)

            # link_hash = str(hash(link))
            link_hash = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
            if link_hash in clusters[parent]['strengths']:
                clusters[parent]['strengths'][link_hash] += strengths
            else:
                clusters[parent]['strengths'][link_hash] = strengths

            if annotate:
                clusters[parent][St.annotate] += "\n\tONLY 2 {} HAS A PARENT COMPARED TO {}".format(
                    child_2, child_1)

        return counter

    # **************************************************************************************************
    # RUNNING THE LINK CLUSTER ALGORITHM
    # **************************************************************************************************
    try:

        standard = 1000000
        check = 1
        iteration = 1

        # **************************************************************************************************
        print(F'\n1. ITERATING THROUGH THE LINKS')
        # **************************************************************************************************
        start = time.time()
        for link in links_iter:
            subject, t_object, strengths = link['source'], link['target'], link['strengths']

            # CALLING THE MAIN HELPER FUNCTION
            # *************************************************
            links = cluster_helper_set(links, annotate=False)
            # *************************************************

            # PRINT EVERY STANDARD (X) ITERATION THE CREATED CLUSTERS ON THE SERVER SCREEN EVERY STANDARD ITERATIONS
            if iteration == check:
                print(F"\tRESOURCE {links:>10}:   {subject:>40}    =    {t_object}")
                check += standard
            iteration += 1

            elapse = datetime.timedelta(seconds=time.time() - start)
            print(F"\t>>> {links} links clustered in {elapse}")
            print(F"\t>>> {len(clusters)} NUMBER OF CLUSTER FOUND")

        # **************************************************************************************************
        print("\n2. PROCESSING THE CLUSTERS FOR UNIQUE ID AND PREPARING FOR SERIALISATION")
        # **************************************************************************************************

        start_2 = time.time()
        for (key, data) in clusters.items():

            popped = data['nodes'].pop()
            data['nodes'].add(popped)
            smallest_hash = Ut.hasher(popped)

            # 2.1 RESETTING THE CLUSTER ID
            for node in data['nodes']:
                # CREATE THE HASHED ID AS THE CLUSTER NAME
                hashed = Ut.hasher(Ut.hasher(node))
                if hashed <= smallest_hash:
                    smallest_hash = hashed

            # 2.2 CREATE A NEW KEY
            new_key = "{}".format(str(smallest_hash).replace("-", "N")) if str(
                smallest_hash).startswith("-") else "P{}".format(smallest_hash)

            if new_key in new_clusters:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            # 2.3 CONVERTING SET TO LIST AS AST OR JASON DO NOT DEAL WITH SET
            new_clusters[new_key] = {'nodes': [], 'strengths': [], 'links': []}
            new_clusters[new_key]['nodes'] = list(data['nodes'])
            new_clusters[new_key]['strengths'] = data['strengths']
            new_clusters[new_key]['links'] = list(data['links'])

            # 2.4 UPDATE THE ROOT WITH THE NEW KEY
            for node in data['nodes']:
                root[node] = new_key

        elapse = datetime.timedelta(seconds=time.time() - start_2)
        print(F"\t>>> RE-SETTING THE CLUSTER WITH UNIQUE CLUSTER iDS in {elapse}")
        print(F"\t>>> {len(new_clusters)} NUMBER OF CLUSTER FOUND IN THE NEW CLUSTER")

        # **************************************************************************************************
        print("\n4. CLUSTERING IS COMPLETED...")
        # **************************************************************************************************
        elapse = datetime.timedelta(seconds=time.time() - start)
        print(F"\t\t{links} LINKS CLUSTERED AND SERIALIZED in {elapse}")
        print("\n5. JOB DONE!!!\n\t>>> DATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n")

    except Exception as err:
        traceback.print_exc()
        print(err.__str__())

    return new_clusters


# *************************************************************
" EXTENDS EXISTING CLUSTERS WITH EVENT-BASED ASSOCIATION"
# *************************************************************


def extend_cluster(serialisation_dir, serialized_cluster_name, csv_association_file,
                   save_in, reconciled_name=None, condition_30=False, activated=False):

    """
    :param serialisation_dir: THE DIRECTORY OF BOTH THE SERIALISED CLUSTERS TO EXTEND AND THE ASSOCIATION FILE
    :param serialized_cluster_name: THE NAME OF THE SERIALISED CLUSTER FILE (THE MAIN NAME WITHOUT NUMBER OF EXTENSION)
    :param csv_association_file: THE NAME OF THE ASSOCIATION [CSV] FILE (THE MAIN NAME WITHOUT NUMBER OF EXTENSION)
    :param save_in: THE DIRECTORY IN WHICH THE GENERATED FILES ARE SAVED
    :param reconciled_name: THE NAME OF THE SERIALISED RECONCILED DICTIONARY OBJECT
    (THE MAIN NAME WITHOUT NUMBER OF EXTENSION)
    :param condition_30: FOR SPEED, DO NOT BOTHER COMPUTING DATA ON CLUSTERS BIGGER THAN 30 "FALSE"
    :param activated: JUS A BOOLEAN ARGUMENT FOR MAKING SURE THE FUNCTION IS TO RUN
    :return:
        dictionary  if there is a result
        False       if [activated is false] [no cycle] or [empty serialised file] or [problem]
    """

    if activated is False:
        problem(text="--> THE FUNCTION [extend_cluster] IS NOT ACTIVATED.")
        return False

    position = 0    # THE LINK POSITION IN THE CSV FILE
    cycle_paths = {}
    dict_clusters_pairs = {}
    extended_clusters = set()  # LIST OF ALL CLUSTERS THAT EXTEND
    list_extended_clusters_cycle = set()  # LIST OF ALL CLUSTERS THAT EXTENDS AND CONTAIN A CYCLES
    reconciled_nodes = {}  # ABOUT THE RECONCILED NODES ==> BUILDING A DICT WITH NODES - LINKS - STRENGTHS
    extended_file_name = None

    def cycle(src_node, trg_node, source_cluster, target_cluster, detail=False):

        # print '\n Starting helper for'
        # print '\t Source:', source_cluster, src_node
        # print '\t Target:', target_cluster, trg_node

        # CHECK WHETHER THE PAIR OF CLUSTERS IS IN A CYCLE.
        # THIS IS THE CASE IF THE PAIR OF CLUSTER HAS AT LEAST TWO RELATED LINKS
        list_of_related = dict_clusters_pairs[(source_cluster, target_cluster)]

        # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
        # if list_of_related >= 2:

        for related_nodes in list_of_related:

            # 1.1 COMPUTE THE SHORTEST PATH SIZE (DIAMETER) FOR THESE START AND END NODES (SUBJECT)
            sub_link_network = clusters[source_cluster]['links']
            sub_strengths = clusters[source_cluster]['strengths']

            # 1.2 COMPUTE THE SHORTEST PATH SIZE FOR T(DIAMETER) THESE START AND END NODES (TARGET)
            obj_link_network = clusters[target_cluster]['links']
            obj_strengths = clusters[target_cluster]['strengths']

            # 2.1 GET THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT
            # print "\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t\v ", related_nodes[0], "AND", src_node
            sub_diameter_weighted_diameter = shortest_paths_lite(
                sub_link_network, start_node=related_nodes[0], end_node=src_node, strengths=sub_strengths)

            # 2.2 GET THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT
            # print "\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t\v ", related_nodes[1], "AND", trg_node
            obj_diameter_weighted_diameter = shortest_paths_lite(
                obj_link_network, start_node=related_nodes[1], end_node=trg_node, strengths=obj_strengths)

            # 3.1 [SOURCE] FETCH THE STRENGTH OF THE RECONCILED NODES IF THE LINK EXISTS
            link_1 = (related_nodes[0], src_node) if related_nodes[0] < src_node else (src_node, related_nodes[0])
            key_1 = "key_{}".format(str(Ut.hasher(link_1))).replace("-", "N")
            if key_1 in sub_strengths:
                sub_strength = max(sub_strengths[key_1])
            else:
                # print "\nNO KEY FOR: {}\n\t{}".format(key_1, link)
                sub_strength = 0

            # 3.2 [TARGET] FETCH THE STRENGTH OF THE RECONCILED NODES IF THE LINK EXISTS
            link_2 = (related_nodes[1], trg_node) if related_nodes[1] < trg_node else (trg_node, related_nodes[1])
            key_2 = "key_{}".format(str(Ut.hasher(link_2))).replace("-", "N")
            if key_2 in obj_strengths:
                obj_strength = max(obj_strengths[key_2])
            else:
                # print "\nNO KEY FOR: {}\n\t{}".format(key_2, link)
                obj_strength = 0

            # 4.1 COMPUTE THE EVIDENCE'S STRENGTH OF THE SUBJECT
            # print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE SUBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", obj_diameter_weighted_diameter, \
            #     "ev_W_diameter = ", obj_diameter_weighted_diameter
            subj_r_strength = reconciliation_strength(
                sub_strength, ev_diameter=obj_diameter_weighted_diameter[0],
                ev_w_diameter=obj_diameter_weighted_diameter[1], c_penalty=10)
            # print "\t\t>>> RECONCILED:", 0 if strength < 0 else strength

            # 4.2 COMPUTE THE EVIDENCE'S STRENGTH OF THE OBJECT
            # print "\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE OBJECT CLUSTER FOR START AND END NODES:"
            # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", sub_diameter_weighted_diameter, \
            #     "ev_W_diameter = ", sub_diameter_weighted_diameter
            obj_r_strength = reconciliation_strength(
                obj_strength, ev_diameter=sub_diameter_weighted_diameter[0],
                ev_w_diameter=sub_diameter_weighted_diameter[1], c_penalty=10)
            # print "\t\t>>> RECONCILED:", 0 if strength < 0 else strength

            # BUILDING THE NETWORKS FOR RECONCILED NODES
            key_1 = Ut.get_key(related_nodes[0], src_node)
            key_2 = Ut.get_key(related_nodes[1], trg_node)
            if source_cluster not in reconciled_nodes:
                reconciled_nodes[source_cluster] = {"links": [(related_nodes[0], src_node, "R")],
                                                    "strengths": {key_1: [subj_r_strength]}}
            else:
                if "links" not in reconciled_nodes[source_cluster]:
                    reconciled_nodes[source_cluster]["links"] = [(related_nodes[0], src_node, "R")]
                    reconciled_nodes[source_cluster]["strengths"] = {key_1: [subj_r_strength]}
                else:
                    reconciled_nodes[source_cluster]["links"] += [(related_nodes[0], src_node, "R")]

                    if key_1 in reconciled_nodes[source_cluster]["strengths"]:
                        reconciled_nodes[source_cluster]["strengths"][key_1] += [subj_r_strength]
                    else:
                        reconciled_nodes[source_cluster]["strengths"][key_1] = [subj_r_strength]

            # BUILDING THE  NETWORKS
            if target_cluster not in reconciled_nodes:
                reconciled_nodes[target_cluster] = {"links": [(related_nodes[1], trg_node, "R")],
                                                    "strengths": {key_2: [obj_r_strength]}}
            else:
                if "links" not in reconciled_nodes[target_cluster]:
                    reconciled_nodes[target_cluster]["links"] = [(related_nodes[1], trg_node, "R")]
                    reconciled_nodes[target_cluster]["strengths"] = {key_2: [obj_r_strength]}
                else:
                    reconciled_nodes[target_cluster]["links"] += [(related_nodes[1], trg_node, "R")]

                    if key_2 in reconciled_nodes[target_cluster]["strengths"]:
                        reconciled_nodes[target_cluster]["strengths"][key_2] += [obj_r_strength]
                    else:
                        reconciled_nodes[target_cluster]["strengths"][key_2] = [obj_r_strength]

            if detail:

                # ****************************************************************************************************
                # PROCESS COMMENT FOR SUBJECT CLUSTER
                # ****************************************************************************************************
                print("\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE SUBJECT CLUSTER FOR START AND END NODES:")
                print("\t\t\v {} AND {}".format(related_nodes[0], src_node))
                print("\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE SUBJECT CLUSTER FOR START AND END NODES:")
                print("\t\t>>> SIM DATA: sim={} ev_diameter={} ev_W_diameter={}\n\t\t>>> RECONCILED: {}".format(
                    sub_strength, sub_diameter_weighted_diameter[0],
                    sub_diameter_weighted_diameter[1], subj_r_strength))

                # ****************************************************************************************************
                # PROCESS COMMENT FOR OBJECT CLUSTER
                # ****************************************************************************************************
                print("\n\tGETTING THE DIAMETER AND WEIGHTED DIAMETER OF THE OBJECT CLUSTER FOR START AND END NODES:")
                print("\t\t\v {} AND {}".format(related_nodes[1], trg_node))
                print("\t", "COMPUTING THE EVIDENCE'S STRENGTH OF THE OBJECT CLUSTER FOR START AND END NODES:")
                print("\t\t>>> SIM DATA: sim={} ev_diameter={} ev_W_diameter={}\n\t\t>>> RECONCILED: {}".format(
                    obj_strength, sub_diameter_weighted_diameter[0], sub_diameter_weighted_diameter[1], obj_r_strength))

            # print '\n\t Computed strengths:'
            # print '\t\t Source start_node={}, end_node={}, strength={}'.format(
            #   related_nodes[0], src_node, subj_strength)
            # print '\t\t Target start_node={}, end_node={}, strength={}'.format(
            #   related_nodes[1], trg_node, obj_strength)

            # MAKING SURE WE HAVE THE HIGHEST WEIGHT FOR THE LINKS IN THE SHORTEST PATH
            if source_cluster not in cycle_paths or len(cycle_paths[source_cluster]) == 0:
                cycle_paths[source_cluster] = [(related_nodes[0], src_node, subj_r_strength)]
                # print '\n\t\tThe was no path-strength at all for {}, adding ({}, {}, {})'.format(
                #     source_cluster, related_nodes[0], src_node, subj_strength)

            else:
                # print '\t\tThe was some path-strengths there, ',
                add = True
                for start_n, end_n, link_strength in cycle_paths[source_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[0], src_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if link_strength < subj_r_strength:
                            list(cycle_paths[source_cluster]).remove((start_n, end_n, link_strength))
                            # print 'and there was this particular one with smaller strength, removing... '

                        # THE DISCOVERED PATH IS NOT UPDATED FOR ITS STRENGTH IS BIGGER OR EQUAL
                        else:
                            add = False
                            # print 'and there was this particular one with bigger or equal strength, let it there... '

                # WE REACH THIS POINT IF THE PATH WAS NOT THERE OR IF THE STRENGTH IS SMALLER AND NEEDS UPDATE
                if add is True:
                    # print 'adding new path-strength for {}, adding ({}, {}, {})'.format(
                    #   source_cluster, related_nodes[0], src_node, subj_strength)
                    cycle_paths[source_cluster] += [(related_nodes[0], src_node, subj_r_strength)]

            if target_cluster not in cycle_paths or len(cycle_paths[target_cluster]) == 0:
                # print '\n\t\tThe was no path-strength at all for {}, adding ({}, {}, {})'.format(
                #   target_cluster, related_nodes[1], trg_node, obj_strength)
                cycle_paths[target_cluster] = [(related_nodes[1], trg_node, obj_r_strength)]

            else:
                # print '\t\tThe was some path-strengths there, ',
                add = True
                for start_n, end_n, link_strength in cycle_paths[target_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[1], trg_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if link_strength < obj_r_strength:
                            list(cycle_paths[target_cluster]).remove((start_n, end_n, link_strength))
                            # print 'and there was this particular one with smaller strength, removing... '

                        # THE DISCOVERED PATH IS NOT UPDATED FOR ITS STRENGTH IS BIGGER OR EQUAL
                        else:
                            add = False
                            # print 'and there was this particular one with bigger or equal strength, let it there... '

                # WE REACH THIS POINT IF THE PATH WAS NOT THERE OR IF THE STRENGTH IS SMALLER AND NEEDS UPDATE
                if add is True:
                    cycle_paths[target_cluster] += [(related_nodes[1], trg_node, obj_r_strength)]
                    # print 'adding new path-strength for {}, adding ({}, {}, {})'.format(
                    # target_cluster, related_nodes[1], trg_node, obj_strength)
    "END OF THE CYCLE HELPER FUNCTION"

    def derive_reconciliation(cluster_id, detail=False):

        # print("CLUSTER: {}".format(cluster_id))
        temp = []
        investigated = reconciled_nodes[cluster_id]

        if 'links' not in investigated:
            return

        # POSSIBLE CONNECTIONS IN A DIRECTED GRAPH
        combinations = Ut.ordered_combinations(list(investigated["nodes"]))
        # NETWORK OF ALL POSSIBLE LINKS BASED ON ALL NODE RECONCILED
        network = nx.DiGraph(Ut.full_combinations(list(investigated["nodes"])))
        # print Ut.print_dict(dict_clusters_pairs)
        # print Ut.print_dict(reconciled_nodes)

        # test = nx.DiGraph(investigated["links"])
        # nx.draw(test)
        # plt.show()

        while True:

            remain = 0

            for c1, c2 in combinations:

                # THIS IS A RECONCILED LINK
                # [R] STANDS FOR RECONCILED AND [D] STANDS FOR DERIVED
                if (c1, c2, "R") in investigated["links"] or (c1, c2, "D") in investigated["links"]:
                    if detail:
                        print("\tIN: ", (c1, c2, "R/D"))

                # THIS HAS NOT BEEN RECONCILED BUT CAN BE DERIVED
                else:

                    if detail:
                        print("\tOUT:", (c1, c2, "R"))

                    # FIND ALL BASE CYCLES FROM THE FULLY CONNECTED GRAPH
                    base_cycles = filter(lambda x: len(x) == 3, list(nx.all_simple_paths(network, c1, c2, cutoff=2)))
                    # if len(base_cycles) > 0:
                    #     remain += 1

                    for base_cycle in base_cycles:

                        if detail:
                            print("CYCLE BASE", base_cycle)

                        key_1 = Ut.get_key(base_cycle[0], base_cycle[1])
                        key_2 = Ut.get_key(base_cycle[1], base_cycle[2])

                        if key_1 in investigated["strengths"]:

                            if key_2 in investigated["strengths"]:
                                remain += 1
                                curr_strength = max(investigated["strengths"][key_2]) * max(
                                    investigated["strengths"][key_1])

                                if detail:
                                    print("\t>> Keys {} * {} = {}".format(
                                        investigated["strengths"][key_1],
                                        investigated["strengths"][key_2], curr_strength))

                                temp += [(c1, c2, Ut.get_key(c1, c2), curr_strength)]

            # END OF THE FOR LOOP COMBINATION

                                # else:
                                #     remain = 0 if remain - 1 < 0 else remain - 1

                                # else:
                                #     remain = 0 if remain - 1 < 0 else remain - 1
            if detail:
                print("\n\t******************************************************************************\n")

            if remain == 0:
                break

            for node1, node2, link_key, link_strength in temp:

                # NEW LINK
                if (node1, node2, "D") not in investigated["links"]:
                    investigated["links"] += [(node1, node2, "D")]

                # NEW STRENGTH
                if link_key in investigated["strengths"]:
                    investigated["strengths"][link_key] += [link_strength]
                else:
                    investigated["strengths"][link_key] = [link_strength]
            temp = []

        if "strengths" in investigated:
            for inv_key, inv_value in investigated["strengths"].items():
                if len(inv_value) > 1:
                    investigated["strengths"][inv_key] = [max(inv_value)]

                    # if detail:
                    #     Ut.print_list(investigated["links"], comment="LINKS")
                    #     Ut.print_dict(investigated["strengths"], comment="STRENGTHS")
                    # print metric(investigated["links"], investigated["strengths"])
    "END OF THE derive_reconciliation FUNCTION"

    print('\n{:.^100}'.format(" EXTENDING {} ".format(serialized_cluster_name)))
    print('{:.^100}'.format(' USING ASSOCIATION FROM {} '))
    print('{:.^100}'.format(' {} '.format(csv_association_file)))
    print("{:.^100}".format(" *** MAYBE TIME FOR A COFFEE? *** "))
    start = time.time()

    # **************************************************************************************************
    print('\n--> 1. DE-SERIALIZING THE CLUSTERS AND ROOT DICTIONARY')
    # **************************************************************************************************
    # 1. DESERIALIZE THE CLUSTER DICTIONARY NAD THE CLUSTER ROOT DICTIONARY
    # ID OF THE SERIALIZED FILE. IF THE PATTERN IS NOT FOUND IT WILL NOT WORK!!!!
    serialised_id = re.findall(pattern="_(PH.*)_", string=serialized_cluster_name)

    # EXIT THE CODE BECAUSE THE FILE NAME HAS A MISSING PATTERN
    if len(serialised_id) == 0:
        Ut.problem(tab="\t", text="MISSING PATTERN [_(PH.*)_] IN THE DESERIALIZED FILE NAME")
        serialised_id = hasher(reconciled_name) if reconciled_name is not None else None

        if serialised_id is None:
            return False
    else:
        serialised_id = serialised_id[0]

    clusters_dictionary = link_cluster_deserialization(serialisation_dir, main_file_name=serialized_cluster_name)
    clusters = clusters_dictionary['clusters']

    # EXIT THE CODE AS THE CLUSTER HAS NO NODE
    if clusters is None:
        Ut.problem(tab="\t",
                   text=F"\tFILE: {serialized_cluster_name} "
                   F"\nIF YOU ARE EXPECTING TO READ SOME DATA, WE ARE AFRAID, THE CLUSTER HAS NO NODES. "
                   F"\nEITHER IT WAS NOT POSSIBLE TO READ THE PROVIDED FILE OR THE FILE NAME IS INCORRECT.")
        return False
    node2cluster = clusters_dictionary['node2cluster_id']
    print("\t[{}] ILNs CLUSTERED FROM [{}] RESOURCES".format(len(clusters), len(node2cluster)))

    # **************************************************************************************************
    print('\n--> 2. ITERATING THROUGH THE ASSOCIATION FILE FOR SEARCH OF CLUSTER EXTENSIONS AND CYCLES')
    # **************************************************************************************************
    try:

        with gzip.open(csv_association_file, mode='rt', encoding='utf-8') as csv:

            print('\t1. READING FROM FILE: {}'.format(csv_association_file))
            for line in csv:

                position += 1

                # SPLIT THE CSV TO EXTRACT THE SUBJECT OBJECT AND STRENGTH
                split = (line.strip()).split(sep=',')

                # PRINT PROBLEM IF ANY
                if len(split) != 2:
                    print(F'PROBLEM WITH THE DATA AT LINE {position}')

                # CLUSTER THE LINKS
                else:
                    # GETTING RID OF THE HEADER
                    if position > 1:

                        # 2.1 GET THE RELATED NODES
                        sub, obj = Ut.to_nt_format(split[0]), Ut.to_nt_format(split[1])

                        # 2.2 CHECK WHETHER EACH SIDE BELONG TO A CLUSTER
                        if sub in node2cluster and obj in node2cluster:

                            # 2.2.1 FETCH THE CLUSTER ID OF THE NODES IN THE ASSOCIATION
                            src_cluster_id, trg_cluster_id = node2cluster[sub], node2cluster[obj]

                            # ***********************************************************************
                            # 2.2.2 TO SAVE TIME, WE DO NOT EVALUATE CLUSTERS OF SIZE BIGGER THAN 30
                            # ***********************************************************************
                            if condition_30 is True:
                                condition = \
                                    len(clusters[src_cluster_id]['nodes']) <= 30 and len(
                                        clusters[trg_cluster_id]['nodes']) <= 30

                                if condition is False:
                                    continue

                            # 2.2.3 EXTENSION - CYCLE AND RECONCILIATION
                            if src_cluster_id != trg_cluster_id:

                                # **********************************************************************************
                                # 1. CHECKING FOR EXTENSION
                                # IF THE CLUSTER TO WHICH THE NODES BELONG ARE NOT THE SAME THEN THE CLUSTERS EXTEND
                                # **********************************************************************************
                                # THE CLUSTERS EXTEND BECAUSE EACH NODE OF
                                # THE ASSOCIATION BELONGS TO A DIFFERENT CLUSTER
                                extended_clusters.add(src_cluster_id)
                                extended_clusters.add(trg_cluster_id)

                                # **********************************************************************************
                                # CHECKING AND DOCUMENTING CYCLES IN A SPECIFIC ORDER TO MAKE SURE OF A UNIQUE LIST
                                # **********************************************************************************

                                # DOCUMENT PAIR STARTING FROM THE SOURCE
                                if src_cluster_id < trg_cluster_id:

                                    # IF THE PAIR OR CLUSTER ALREADY EXIST IN GHE CLUSTER PAIR DICTIONARY
                                    # IT MEANS THAT THERE IS A CYCLE BETWEEN THE TWO EXTENDED CLUSTERS
                                    if (src_cluster_id, trg_cluster_id) in dict_clusters_pairs.keys():

                                        # IT HAS A CYCLE
                                        list_extended_clusters_cycle.add(src_cluster_id)
                                        list_extended_clusters_cycle.add(trg_cluster_id)

                                        # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
                                        cycle(
                                            src_node=sub, trg_node=obj,
                                            source_cluster=src_cluster_id, target_cluster=trg_cluster_id)

                                        # DOCUMENTING THE EXTENDED CLUSTERS AND RELATED NODES THAT EXTEND THE CLUSTERS
                                        dict_clusters_pairs[(src_cluster_id, trg_cluster_id)] += [(sub, obj)]

                                    # THE PAIR OF EXTENDED CLUSTER WAS NEVER DOCUMENTED BEFORE
                                    else:
                                        # WE DO NOT USE THE VALUE OF THE DICTIONARY SO ITS EMPTY
                                        # DOCUMENTING FIRST OCCURRENCE
                                        dict_clusters_pairs[(src_cluster_id, trg_cluster_id)] = [(sub, obj)]

                                # DOCUMENT PAIRS STARTING FROM THE TARGET
                                else:

                                    if (trg_cluster_id, src_cluster_id) in dict_clusters_pairs.keys():

                                        # IT HAS A CYCLE
                                        list_extended_clusters_cycle.add(src_cluster_id)
                                        list_extended_clusters_cycle.add(trg_cluster_id)

                                        # DOCUMENTING THE CYCLE START AND END FOR THIS SPECIFIC ORDER
                                        cycle(
                                            src_node=obj, trg_node=sub,
                                            source_cluster=trg_cluster_id, target_cluster=src_cluster_id)

                                        # DOCUMENTING THE EXTENDED CLUSTERS AND RELATED NODES THAT EXTEND THE CLUSTERS
                                        dict_clusters_pairs[(trg_cluster_id, src_cluster_id)] += [(obj, sub)]

                                    else:
                                        # WE DO NOT USE THE VALUE OF THE DICTIONARY SO ITS EMPTY
                                        # DOCUMENTING FIRST OCCURRENCE
                                        dict_clusters_pairs[(trg_cluster_id, src_cluster_id)] = [(obj, sub)]
                            # else:
                            #     print(F'{sub}\t{obj}')

            # file_stats = stat(join(serialisation_dir, csv_association_file))
            print('\t\tTHE FILE IS OF SIZE [{}]'.format(Ut.file_size(join(serialisation_dir, csv_association_file))))
            print('\t\tTHE FILE IS OF [{}] LINES'.format(position))
            elapse = datetime.timedelta(seconds=time.time() - start)
            print(F'\t\t{elapse} SO FAR...')

    except FileNotFoundError as err:
        problem(text=err)
        return False

    # ***************************************************************************************************
    print("\n--> 3. SERIALISING THE EXTENDED CLUSTERS DICTIONARIES AND THE LIST OF CLUSTERS IN A CYCLE...")
    # ***************************************************************************************************
    if len(extended_clusters) != 0 and len(list_extended_clusters_cycle) != 0:
        # start = time.time()
        # SERIALISATION

        f_name = get_file_name(basename(csv_association_file))[0]
        related_graph_mane = Ut.get_uri_local_name_plus(f_name)
        extended_file_name = F"{serialized_cluster_name}_ExtendedBy_{related_graph_mane}_{serialised_id}"

        s_file_1 = join(save_in, F"{extended_file_name}-1.txt.gz")
        s_file_2 = join(save_in, F"{extended_file_name}-2.txt.gz")
        s_file_3 = join(save_in, F"{extended_file_name}-3.txt.gz")
        s_file_4 = join(save_in, F"{extended_file_name}-4.txt.gz")

        data = {'extended_clusters': list(extended_clusters),
                'list_extended_clusters_cycle': list(list_extended_clusters_cycle),
                'cycle_paths': cycle_paths}

        # LIST OF CLUSTERS THAT EXTEND THE CURRENT CLUSTER
        pickle_serializer(CLUSTER_SERIALISATION_DIR, data['extended_clusters'], s_file_1, zip_it=True)

        # LIST OF CLUSTERS FOR WITCH A CYCLE EXISTS
        pickle_serializer(CLUSTER_SERIALISATION_DIR, data['list_extended_clusters_cycle'], s_file_2, zip_it=True)

        # DICTIONARY OF THE CYCLE PATHS
        pickle_serializer(CLUSTER_SERIALISATION_DIR, cycle_paths, s_file_3, zip_it=True)

        # DICTIONARY OF THE RECONCILED NODES
        pickle_serializer(CLUSTER_SERIALISATION_DIR, reconciled_nodes, s_file_4, zip_it=True)

        # print("\n6. SAVING THE HASH OF EXTENDED CLUSTERS TO THE TRIPLE STORE AS: {}".format(file_name))
        # Qry.endpoint("""INSERT DATA {{
        # <{0}> <{1}extendedClusters> '''{2}''' .
        # }}""".format(graph, Ns.alivocab, file_name))

        print("\t1. SERIALISATION IS COMPLETED...")
        print("\t2. RESULTS...")
        print("\t\t2.1 FOUND [{}] EXTENDED CLUSTERS".format(len(extended_clusters)))
        print("\t\t2.2 FOUND [{}] CLUSTERS WITH CYCLES".format(len(list_extended_clusters_cycle)))
        elapse = datetime.timedelta(seconds=time.time() - start)
        print(F'\t\t{elapse} SO FAR...')
        # print("\nJOB DONE!!!\nDATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n")

    # **************************************************************************************************
    # **************************************************************************************************
    print('\n--> 4. EXTRACTING ALL RECONCILED NODES PER EXTENDED CLUSTERS')
    "==> INSTANTIATING reconciled_nodes WITH THE NODES"
    # **************************************************************************************************
    # **************************************************************************************************
    # start = time.time()
    for key, value in reconciled_nodes.items():
        # GET THE RECONCILED LINKS
        links = value['links']
        # EXTRACT THE RECONCILED NODES IN A SET FOR UNIQUENESS
        nodes = list(set([data[0] for data in links] + [data[1] for data in links]))
        # ASSIGN THE SET OF NODES
        reconciled_nodes[key]['nodes'] = nodes

    print("\t1. COMPUTING THE DERIVED STRENGTHS")
    # -------------------------------------------
    strength_start = time.time()
    for key in reconciled_nodes.keys():
        # reconciled_nodes[key]['nodes'] = list(reconciled_nodes[key]['nodes'])
        derive_reconciliation(key, detail=False)
    elapse_s = datetime.timedelta(seconds=time.time() - strength_start)
    elapse = datetime.timedelta(seconds=time.time() - start)
    print(F'\t\tDERIVED STRENGTHS COMPUTED IN {elapse_s} BUT IS HAS BEEN {elapse} SO FAR...')

    print("\t2. BUILDING UP THE REFINED CLUSTER DATA")
    # ------------------------------------------------
    # refined_start = time.time()
    # THE RECONCILIATION FILE IS CREATED WITH LINKS AND STRENGTHS FOR TIME COMPLEXITY
    # THE RECONCILED NODES ARE FOUND USING THE CYCLE HELPER IN THE ASSOCIATION
    # -------------------------------------------------------------------------------
    reconciled_clusters_serialised_file = None
    if len(reconciled_nodes) > 0:
        date_formatted = datetime.datetime.today().strftime('%a %b %d %Y %H:%M:%S.%f')
        file_name = F"reconciled_file_{Ut.hasher(date_formatted)}"
        reconciled_file_path = join(serialisation_dir, F"{file_name}.csv")
        with gzip.open(reconciled_file_path, mode='wt', encoding='utf-8') as reconciled_file:
            for key, reconciled in reconciled_nodes.items():
                strengths = reconciled['strengths']
                for link in reconciled['links']:
                    # c_data += [(link[0], link[1], strengths[Ut.get_key(link[0], link[1])])]
                    strength = strengths[Ut.get_key(link[0], link[1])]
                    max_strength = max(map(float, strength))
                    line = F"{link[0]},{link[1]},{max_strength}\n"
                    reconciled_file.write(line)

        # CLUSTERING FHE RECONCILED NODES ...............................
        if not reconciled_name:
            reconciled_name = F"{serialized_cluster_name}_Reconciled_{serialised_id}"

        reconciled_clusters_serialised_file = simple_csv_link_clustering(
            csv_path=reconciled_file_path, save_in=serialisation_dir,
            file_name=reconciled_name, key=F"Reconciled_{serialised_id}", activated=True)

        reconciled_clusters_serialised_file = reconciled_clusters_serialised_file['file_name'] \
            if reconciled_clusters_serialised_file else None

        # THE FILE IS AGAIN REMOVED TO SAVE HARD DISC SPACE
        # *************************************************
        remove(reconciled_file_path)
        # *************************************************

    else:
        print("\t3. NO RECONCILIATION AS NO CYCLE COULD BE FOUND.")

    elapse = datetime.timedelta(seconds=time.time() - start)
    print(F'\t{elapse} SO FAR...')

    print("\t3. CLUSTERING THE NEW REFINED LINKS")
    print("\n4. results\n\t1. FOUND [{}] EXTENDED CLUSTERS".format(len(extended_clusters)))
    print("\t2. FOUND [{}] CYCLES".format(len(list_extended_clusters_cycle)))
    elapse = datetime.timedelta(seconds=time.time() - start)
    Ut.completed(start)
    # print('{:.^100}'.format(F" COMPLETED IN {elapse} "))
    # print('{:.^100}'.format(F" JOB DONE! "))
    # print("\n{:.^100}".format(" WE ARE ABOUT TO CLUSTER AND SERIALISED"))

    # EXTENDED FILE NAME IS NONE IF WE DO NOT FINE ANY CYCLES.
    # EVEN IF THE CLUSTERS EXTEND, NO EXTENDED FILE WILL BE GENERATED IF NO CYCLE IS FOUND
    return {
        'extended_file_name': extended_file_name,
        'reconciled_clusters_serialised_file_name': reconciled_clusters_serialised_file,
        'extended_clusters_count': len(extended_clusters),
        'cycles_count': len(list_extended_clusters_cycle)
    }


# *************************************************************
# *************************************************************
"THESE FUNCTIONS BELOW ARE USED IN THE EXTENSION AND FOR COMPUTING CYCLES AND RESOURCES RECONCILIATIONS"
# *************************************************************
# *************************************************************

# **************************************************************************************
# GIVEN TWO NODES, FIND THE SHORTEST PATHS
# THE LINK NETWORK INPUT IS A LIST OF TUPLES WHERE A TUPLE REPRESENTS LINKS BETWEEN
# A PAIR OF NODES. THE FUNCTION MAKES USE OF THE NETWORKS LIBRARY
# **************************************************************************************


def shortest_paths(link_network, start_node, end_node):

    # EXTRACT THE NODES FROM THE NETWORK OF LINKS
    nodes = set([n1 for n1, n2 in link_network] + [n2 for n1, n2 in link_network])

    # INSTANTIATE THE GRAPH
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in link_network:
        g.add_edge(edge[0], edge[1])

    problem(label=" COMPUTING SHORTEST PATH ",
            text="--> LENGTH : {}\n--> CONNECTED : {}\n--> DIRECTED : {}".format(g.order(), nx.is_connected(g), g.is_directed()))
    # print(g.nodes(data=True))
    # print(g.edges(data=True))
    # print(str(g))
    # print("LENGTH", len(g))
    # print(start_node, end_node)
    # print(g.order())
    # exit()

    # GET THE LIT OF PATHS
    # results = list(nx.shortest_simple_paths(g, source=start_node, target=end_node))
    # if start_node not in g or end_node+" " not in g:
    #     print(start_node in g, end_node in g)
    #
    #     print(len(g))
    # exit()
    # print("nx.is_connected(g)", nx.is_connected(g))
    results = shortest_paths_lite(g, start_node=start_node, end_node=end_node)

    # EXTRACT THE SHORTEST PATH  OF THE SMALLEST SIZE
    # for item in results:
    #
    #     if len(item) == len(results[0]):
    #         final += [item]
    #
    #     else:
    #         break

    print("DONE COMPUTING PATH!")
    return results


def link_cluster_deserialization(serialisation_dir, main_file_name):

    print("\n{:>13}: {}".format("DIRECTORY ", serialisation_dir))
    print("{:>13}: {}".format("FILE ", main_file_name))

    # try:
    if True:
        # DE-SERIALISING THE MAIN DICTIONARY OF CLUSTER
        print("\n\tREADING FROM SERIALISED FILE 1...")
        clusters = Ut.pickle_deserializer(serialised_folder=serialisation_dir, name=F"{main_file_name}-1.txt.gz")

        # DE-SERIALISING THE ROOT DICTIONARY SUPPORTING THE MAIN DICTIONARY OF CLUSTERS
        print("\tREADING FROM SERIALISED FILE 2...")
        node2cluster_id = Ut.pickle_deserializer(serialised_folder=serialisation_dir, name=F"{main_file_name}-2.txt.gz")

        return {'clusters': clusters, 'node2cluster_id': node2cluster_id}

    # except (IOError, ValueError):
    #     print(F"\nRE-RUNNING IT ALL BECAUSE THE SERIALISED FILE [{main_file_name}].txt COULD NOT BE FOUND.")


def shortest_paths_lite(link_network, start_node, end_node, strengths=None):

    # print "\nCOMPUTING PATH USING [shortest_paths_lite]..."
    # EXTRACT THE NODES FROM THE NETWORK OF LINKS
    nodes = set([data[0] for data in link_network] + [data[1] for data in link_network])

    # INSTANTIATE THE GRAPH
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in link_network:
        g.add_edge(edge[0], edge[1])

    # g = g.to_undirected()

    # GET THE SHORTEST PATH (THE FUNCTION RETURNS ONLY ONE PATH)
    result = nx.shortest_path(g, source=start_node, target=end_node)
    diameter = len(result) - 1
    results = []

    # FIND OTHER PATHS OF THE SAME SIZE
    if g.order() > 30:
        results = [result]

    # FINDING ALL SHORTEST PATHS AND GET THE HIGHEST WEIGHTED ONE
    # HOWEVER, IF THE CLUSTER IS TOO BIG, DO NO BOTHER USE THE ONLY ONE PROVIDED BY RESULT
    elif result is not None:

        # print("LOOKING FOR OTHER PATHS")
        # g = deepcopy(link_network)
        results = [result]
        size = len(result)
        diameter = size - 1

        # for each of the results of same size found, remove edges to try and find other paths
        for result in results:
            # print result
            partials = []

            # for each pair in the path, remove the link and check the shortest path and add it again
            for i in range(len(result)-1):

                g.remove_edge(result[i], result[i+1])
                # print "REMOVED:", result[i], result[i+1]
                try:
                    partial = nx.shortest_path(g, source=start_node, target=end_node)

                except IOError:
                    partial = []

                except nx.NetworkXNoPath:
                    partial = []

                # if there is a path of same size, keep it in a set (there can be repetition)
                if len(partial) == size:
                    if partial not in partials:
                        partials += [partial]

                g.add_edge(result[i], result[i+1])

            # add whatever path found if so
            for p in partials:
                if p not in results:
                    results += [p]
            # print 'new paths: ', partials

    # NOW WE HAVE ALL POSSIBLE SHORTEST PATHS
    weighted_paths = []
    for path in results:
        weight = 0
        for i in range(0, diameter):
            link = (path[i], path[i + 1]) if path[i] < path[i + 1] else (path[i + 1], path[i])
            key = "key_{}".format(str(Ut.hasher(link))).replace("-", "N")
            # print( F"strengths[key]: {strengths[key]}")
            weight += max(map(float, strengths[key]))
        weighted_paths += [weight]

    weighted_diameter = max(weighted_paths) if len(weighted_paths) > 0 else 0

    return diameter, weighted_diameter


def shortest_paths_lite_size(link_network, start_node, end_node):

    print("COMPUTING SHORTEST PATH USING [shortest_paths_lite]...")

    # EXTRACT THE NODES FROM THE NETWORK OF LINKS
    nodes = set([data[0] for data in link_network] + [data[1] for data in link_network])

    # INSTANTIATE THE GRAPH
    g = nx.Graph()

    # add nodes
    for node in nodes:
        g.add_node(node)

    # add edges
    for edge in link_network:
        g.add_edge(edge[0], edge[1])

    # GET THE SHORTEST PATH (THE FUNCTION RETURNS ONLY ONE PATH)
    # THE PATH IS A SET OF NODES IN SEQUENCE
    result = nx.shortest_path(g, source=start_node, target=end_node)

    if result is not None:
        return len(result) - 1
    else:
        return 0


def reconciliation_strength(sim, ev_diameter, ev_w_diameter, c_penalty=10):

    # print "\t\t>>> SIM DATA:", "sim = ", "ev_diameter = ", ev_diameter, "ev_W_diameter = ", ev_w_diameter

    # ITS A CLUSTER OF ONE NODE
    if ev_diameter == 0:
        return 1

    validation_strength = (100 - c_penalty * abs(2 * ev_diameter - ev_w_diameter - 1)) / float(100)
    strength = min(float(sim), validation_strength) if float(sim) > 0 else validation_strength
    strength = 0 if strength < 0 else strength

    return strength


def evidence_penalty(investigated_diameter, evidence_diameter, penalty_percentage=10):

    penalty = (100 - penalty_percentage * (evidence_diameter - 1)) / float(100)
    return 0 if penalty < 0 else (1 / float(investigated_diameter)) * penalty


# ****************************************************
"             COMPRESSED VISUALISATION               "
# ****************************************************


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


def convert_rdf(source, save_in, convert_to="nt"):

    data = Graph()
    start = time.time()
    data.parse(source, format=util.guess_format(source))
    elapse = datetime.timedelta(seconds=time.time() - start)
    print(F"\t>>> {len(data)} links clustered in {elapse}")

    serialising_time = time.time()
    data.serialize(destination=save_in, format=convert_to)
    elapse = datetime.timedelta(seconds=time.time() - serialising_time)
    print(F"\t>>> {len(data)} links clustered in {elapse}")

    # for stmt in data:
    #     print(stmt)

    # convert_rdf(source="C:\Productivity\\3-MatchingTools\Data\grid-2019-02-17\grid.ttl",
    #     save_in= "C:\Productivity\\3-MatchingTools\Data\grid-2019-02-17\grid.nt")


def file_sample(source, save_as, sample_size):
    with open(source, mode="r", encoding="utf-8") as nt:
        line = 0
        new_file = open(save_as, mode="w", encoding="utf-8")
        for triple in nt:
            new_file.write(triple)
            line += 1
            if line == sample_size:
                break
