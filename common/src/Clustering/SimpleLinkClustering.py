

import re
import time
import datetime
import traceback
import networkx as nx
from os.path import join, splitext as get_file_name, basename
from os import stat, remove
import src.Generic.Utility as Ut
import src.Generic.Settings as St
from src.Generic.Utility import print_object
import src.DataAccess.Middleware as Middleware
from src.Generic.Utility import pickle_serializer, pickle_deserializer, \
    to_nt_format, get_uri_local_name_plus, undo_nt_format, hash_number
import src.DataAccess.Stardog.Query as Stardog

# GET PATH OF THE SERIALISED DIRECTORY
from src.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
from src.LLData.Serialisation import CLUSTER_SERIALISATION_DIR

_format = "It is %a %b %d %Y %H:%M:%S"
date = datetime.datetime.today()
_line = "--------------------------------------------------------------" \
        "--------------------------------------------------------------"

# *************************************************************
# *************************************************************
""" USING [SET]  [TABLE OF RESOURCES] AND THEIR [STRENGTHS] """
# *************************************************************
# *************************************************************

def simple_csv_link_clustering(csv_path, save_in, file_name=None, key=None, activated=False):

    """
    :param csv_path: THE PATH OF THE CSV FILE
    :param file_name: THE NAME OF THE GRAPH TO CLUSTER WITHOUT -1 (CLUSTERS) OR -2(ROOT) OR EXTENTION
    :param serialisation_dir: THE DIRECTORY TO SAVE THE CLUSTER SERIALIZATIONS
    :return:
    """

    if activated is False:
        return

    print("\n{:.^100}".format(" WE ARE ABOUT TO CLUSTER AND SERIALISED "))
    print("{:.^100}".format(" FOM " + csv_path + " "))
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
    local_key = key

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
                'nodes': set([child_1, child_2]), 'links': set([link]), 'strengths': {key_1: [strength]}}
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
                        clusters[parent1]['strengths'][link_hash] += [strength]
                    else:
                        clusters[parent1]['strengths'][link_hash] = [strength]

                    clusters.pop(parent2)

            # 2.2 BOTH CHILD HAVE THE SAME PARENT, DO NOTHING
            else:
                parent = root[child_1]
                link = (child_1, child_2) if child_1 < child_2 else (child_2, child_1)
                clusters[parent]['links'].add(link)

                # link_hash = str(hash(link))
                link_hash = "key_{}".format(str(Ut.hasher(link)).replace("-", "N"))
                if link_hash in clusters[parent]['strengths']:
                    clusters[parent]['strengths'][link_hash] += [strength]
                else:
                    clusters[parent]['strengths'][link_hash] = [strength]

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
                clusters[parent]['strengths'][link_hash] += [strength]
            else:
                clusters[parent]['strengths'][link_hash] = [strength]

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
                clusters[parent]['strengths'][link_hash] += [strength]
            else:
                clusters[parent]['strengths'][link_hash] = [strength]

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
        file_size = Ut.file_size(csv_path)

        # **************************************************************************************************
        print(F'\n1. ITERATING THROUGH THE CSV FILE OF SIZE {file_size}')
        # **************************************************************************************************
        start = time.time()
        with open(csv_path, mode="r", encoding="utf-8") as csv:

            # ITERATE THROUGH THE FILE
            position = 0
            for line in csv:
                position += 1

                # SPLIT THE CSV TO EXTRACT THE SUBJECT OBJECT AND STRENGTH
                split = (line.strip()).split(sep=',')

                # PRINT PROBLEM IF ANY
                if len(split) != 3:
                    print(F'PROBLEM WITH THE DATA AT LINE {position}')

                # CLUSTER THE LINKS
                else:
                    # GETTING READ OF THE HEADER
                    if position > 1:
                        subject, t_object, strength = split[0].strip(), split[1].strip(), split[2].strip()

                        # CALLING THE MAIN HELPER FUNCTION
                        # *************************************************
                        links = cluster_helper_set(links, annotate=False)
                        # *************************************************

                        # PRINT EVERY STANDARD (X) ITERATION THE CREATED CLUSTERS ON THE SERVER SCREEN EVERY STANDARD ITERATIONS
                        if iteration == check:
                            print(F"\tRESOURCE {links:>10}:   {subject:>40}    =    {t_object}")
                            check += standard
                        iteration += 1
                        # print(iteration)

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

        if file_name is None:
            extra = F"_{local_key}" if local_key is not None else F""
            print("extra:", local_key)
            returned = {'clusters': new_clusters, 'node2cluster_id': root}
            file_name = str(Ut.hasher(returned.__str__()))
            file_name = F"Serialized_Cluster_P{file_name}" if len(extra) == 0 else F"Serialized_Cluster{extra}"
        # else F"Serialized_Cluster{extra}_P{file_name}"
        elapse = datetime.timedelta(seconds=time.time() - start_2)
        print(F"\t>>> RE-SETTING THE CLUSTER WITH UNIQUE CLUSTER iDS in {elapse}")
        print(F"\t>>> {len(new_clusters)} NUMBER OF CLUSTER FOUND IN THE NEW CLUSTER")

        # **************************************************************************************************
        print("\n3. SERIALISING THE DICTIONARIES...")
        # **************************************************************************************************

        # WRITE TO FILE ONLY IF WE HAVE MORE THAN 0 CLUSTER
        start_3 = time.time()
        s_file_1 = s_file_2 = ""
        f_stat_1 = f_stat_2 = 0
        if len(new_clusters) != 0 and len(root) != 0:

            # SERIALISATION FILES
            s_file_1 = "{}-1.txt".format(file_name)
            s_file_2 = "{}-2.txt".format(file_name)

            # SERIALISING THE CLUSTER DICTIONARY
            f_stat_1 = Ut.pickle_serializer(
                directory=save_in, data_object=new_clusters, name=s_file_1)

            # SERIALISING THE CLUSTER ROOT DICTIONARY
            f_stat_2 = Ut.pickle_serializer(
                directory=save_in, data_object=root, name=s_file_2)

        # f_stat_1 = round(stat(f_stat_1).st_size / (1024 * 1024 * 1024), 3)
        f_stat_1 = Ut.file_size(f_stat_1)
        f_stat_2 = Ut.file_size(f_stat_2)
        elapse = datetime.timedelta(seconds=time.time() - start_3)
        print(F"\t>>> DONE SERIALISING THE DICTIONARIES in {elapse}")

        # **************************************************************************************************
        print("\n4. SERIALISATION IS COMPLETED...")
        # **************************************************************************************************
        elapse = datetime.timedelta(seconds=time.time() - start)
        text = ["CLUSTER FILE", "ROOT FILE"]
        print(F"\t\t{links} LINKS CLUSTERED AND SERIALIZED in {elapse}")
        print(F"\tDIRECTORY : {save_in}")
        print(F"\t\t{text[0]:<13}: {s_file_1:>30} \tSIZE: {f_stat_1:>6}")
        print(F"\t\t{text[1]:<13}: {s_file_2:>30} \tSIZE: {f_stat_2:>6}")
        print("\n5. JOB DONE!!!\n\t>>> DATA RETURNED TO THE CLIENT SIDE TO BE PROCESSED FOR DISPLAY\n")
        round(stat(csv_path).st_size / (1024 * 1024 * 1024), 3)

        return file_name

    except Exception as err:
        traceback.print_exc()
        print(err.__str__())
        return file_name


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
    :param condition_30: FOR SPEED, DO NOT BOTHER COMPUTING DATA ON CLUSTERS BIGGER THAN 30
    :param activated: JUS A BOOLEAN ARGUMENT FOR MAKING SURE THE FUNCTION IS TO RUN
    :return:
    """

    if activated is False:
        return

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
                for start_n, end_n, strength in cycle_paths[source_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[0], src_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if strength < subj_r_strength:
                            list(cycle_paths[source_cluster]).remove((start_n, end_n, strength))
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
                for start_n, end_n, strength in cycle_paths[target_cluster]:

                    # UPDATING AN EXISTING PATH-STRENGTH
                    if (start_n, end_n) == (related_nodes[1], trg_node):

                        # THE DISCOVERED PATH IS UPDATED FOR ITS STRENGTH IS SMALLER
                        if strength < obj_r_strength:
                            list(cycle_paths[target_cluster]).remove((start_n, end_n, strength))
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
                if (c1, c2, "R") in investigated["links"] or (c1, c2, "D") in investigated["links"]:
                    if detail:
                        print("\tIN: ", (c1, c2, "R/D"))

                # THIS HAS NOT BEEN RECONCILED BUT CAN BE DERIVED
                else:

                    if detail:
                        print("\tOUT:", (c1, c2, "R"))

                    # FIND ALL BASE CYCLE FROM THE FULLY CONNECTED GRAPH
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
                                strength = max(investigated["strengths"][key_2]) * max(
                                    investigated["strengths"][key_1])

                                if detail:
                                    print("\t>> Keys {} * {} = {}".format(
                                        investigated["strengths"][key_1], investigated["strengths"][key_2], strength))
                                temp += [(c1, c2, Ut.get_key(c1, c2), strength)]

                                # else:
                                #     remain = 0 if remain - 1 < 0 else remain - 1

                                # else:
                                #     remain = 0 if remain - 1 < 0 else remain - 1
            if detail:
                print("\n\t******************************************************************************\n")

            if remain == 0:
                break

            for node1, node2, link_key, strength in temp:

                # NEW LINK
                if (node1, node2, "D") not in investigated["links"]:
                    investigated["links"] += [(node1, node2, "D")]

                # NEW STRENGTH
                if link_key in investigated["strengths"]:
                    investigated["strengths"][link_key] += [strength]
                else:
                    investigated["strengths"][link_key] = [strength]
            temp = []

        if "strengths" in investigated:
            for inv_key, inv_value in investigated["strengths"].items():
                if len(inv_value) > 1:
                    investigated["strengths"][inv_key] = [max(inv_value)]

                    # if detail:
                    #     Ut.print_list(investigated["links"], comment="LINKS")
                    #     Ut.print_dict(investigated["strengths"], comment="STRENGTHS")
                    # print metric(investigated["links"], investigated["strengths"])

    print('\n{:.^100}'.format(" EXTENDING {} ".format(serialized_cluster_name)))
    print('{:.^100}'.format(' USING ASSOCIATION FROM {} '.format(csv_association_file)))
    print("{:.^100}".format(" *** MAYBE TIME FOR A COFFEE? *** "))
    start = time.time()
    # **************************************************************************************************
    print('\n--> 1. DE-SERIALIZING THE CLUSTERS AND ROOT DICTIONARY')
    # **************************************************************************************************
    # 1. DESERIALIZE THE CLUSTER DICTIONARY NAD THE CLUSTER ROOT DICTIONARY
    # ID OF THE SERIALIZED FILE. IF THE PATTERN IS NOT FOUND IT WILL NOT WORK!!!!
    serialised_id = re.findall(pattern="_(PH.*)_",string=serialized_cluster_name)

    # EXIT THE CODE BECAUSE THE FILE NAME HAS A MISSING PATTERN
    if len(serialised_id) == 0:
        Ut.problem(tab="\t")
        print("\tMISSING PATTERN [_(PH.*)_] IN THE DESERIALIZED FILE NAME")
        # return None, None
        serialised_id = serialized_cluster_name
    else:
        serialised_id = serialised_id[0]

    clusters_dictionary = link_cluster_deserialization(serialisation_dir, main_file_name=serialized_cluster_name)
    clusters = clusters_dictionary['clusters']

    # EXIT THE CODE AS THE CLUSTER HAS NO NODE
    if clusters is None:
        Ut.problem(tab="\t")
        print(F"\tFILE: {serialized_cluster_name}"
              F"\n\tIF YOU ARE EXPECTING TO READ SOME DATA, WE ARE AFRAID, THE CLUSTER HAS NO NODES."
              F"\n\tEITHER IT WAS NOT POSSIBLE TO READ THE PROVIDED FILE OR THE FILE NAME IS INCORRECT.")
        return None, None
    node2cluster = clusters_dictionary['node2cluster_id']
    print("\t[{}] ILNs CLUSTERED FROM [{}] RESOURCES".format(len(clusters), len(node2cluster)))

    # **************************************************************************************************
    print('\n--> 2. ITERATING THROUGH THE ASSOCIATION FILE FOR SEARCH OF CLUSTER EXTENSIONS AND CYCLES')
    # **************************************************************************************************
    with open(csv_association_file, mode='r', encoding='utf-8') as csv:

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

                        # ****************************************************************
                        # 2.2.2 TO SAVE TIME, WE DO NOT EVALUATE CLUSTERS OF SIZE BIGGER THAN 30
                        # ****************************************************************
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
                            # =THE CLUSTERS EXTEND BECAUSE EACH NODE OF THE ASSOCIATION BELONGS TO A DIFFERENT CLUSTER
                            extended_clusters.add(src_cluster_id)
                            extended_clusters.add(trg_cluster_id)

                            # **********************************************************************************
                            # CHECKING AND DOCUNENTING CYCLES IN A SPECIFIC ORDER TO MAKE SURE OF A UNIQUE LIST
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
        file_stats = stat(join(serialisation_dir, csv_association_file))
        print('\t\tTHE FILE IS OF SIZE [{}]'.format(Ut.file_size(join(serialisation_dir, csv_association_file))))
        print('\t\tTHE FILE IS OF [{}] LINES'.format(position))
        elapse = datetime.timedelta(seconds=time.time() - start)
        print(F'\t\t{elapse} SO FAR...')

    # ***************************************************************************************************
    print("\n--> 3. SERIALISING THE EXTENDED CLUSTERS DICTIONARIES AND THE LIST OF CLUSTERS IN A CYCLE...")
    # ***************************************************************************************************
    if len(extended_clusters) != 0 and len(list_extended_clusters_cycle) != 0:
        # start = time.time()
        # SERIALISATION
        if reconciled_name is None:
            f_name = get_file_name(basename(csv_association_file))[0]
            related_graph_mane = Ut.get_uri_local_name_plus(f_name)
            extended_file_name = "ExtendedBy_{}_{}".format(related_graph_mane, serialised_id)

            s_file_1 = join(save_in, F"{extended_file_name}-1.txt")
            s_file_2 = join(save_in, F"{extended_file_name}-2.txt")
            s_file_3 = join(save_in, F"{extended_file_name}-3.txt")
            s_file_4 = join(save_in, F"{extended_file_name}-4.txt")

        else:

            s_file_1 = join(save_in, F"{reconciled_name}-1.txt")
            s_file_2 = join(save_in, F"{reconciled_name}-2.txt")
            s_file_3 = join(save_in, F"{reconciled_name}-3.txt")
            s_file_4 = join(save_in, F"{reconciled_name}-4.txt")

        data = {'extended_clusters': list(extended_clusters),
                'list_extended_clusters_cycle': list(list_extended_clusters_cycle),
                'cycle_paths': cycle_paths}

        pickle_serializer(CLUSTER_SERIALISATION_DIR, data['extended_clusters'], s_file_1)

        pickle_serializer(CLUSTER_SERIALISATION_DIR, data['list_extended_clusters_cycle'], s_file_2)

        # DICTIONARY OF THE CYCLE PATHS
        pickle_serializer(CLUSTER_SERIALISATION_DIR, cycle_paths, s_file_3)

        # DICTIONARY OF THE RECONCILED NODES
        pickle_serializer(CLUSTER_SERIALISATION_DIR, reconciled_nodes, s_file_4)

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
    strength_start = time.time()
    for key in reconciled_nodes.keys():
        # reconciled_nodes[key]['nodes'] = list(reconciled_nodes[key]['nodes'])
        derive_reconciliation(key, detail=False)
    elapse_s = datetime.timedelta(seconds=time.time() - strength_start)
    elapse = datetime.timedelta(seconds=time.time() - start)
    print(F'\t\tDERIVED STRENGTHS COMPUTED IN {elapse_s} BUT IS HAS BEEN {elapse} SO FAR...')

    print("\t2. BUILDING UP THE REFINED CLUSTER DATA")
    refined_start = time.time()

    # THE FILE IS CREATED FOR TIME COMPLEXITY
    date = datetime.datetime.today().strftime('%a %b %d %Y %H:%M:%S.%f')
    file_name = F"reconciled_file_{Ut.hasher(date)}"
    reconciled_file_path = join(serialisation_dir, F"{file_name}.csv")
    with open(reconciled_file_path, mode='w', encoding='utf-8') as reconciled_file:
        for key, reconciled in reconciled_nodes.items():
            strengths = reconciled['strengths']
            for link in reconciled['links']:
                # c_data += [(link[0], link[1], strengths[Ut.get_key(link[0], link[1])])]
                strength = strengths[Ut.get_key(link[0], link[1])]
                max_strength = max(map(float, strength))
                line = F"{link[0]},{link[1]},{max_strength}\n"
                reconciled_file.write(line)

    # CLUSTERING FHE RECONCILED NODES ...............................
    reconciled_clusters_serialised_file = simple_csv_link_clustering(
        csv_path=reconciled_file_path, save_in=serialisation_dir,
        file_name=reconciled_name, key=F"Reconciled_{serialised_id}", activated=True)

    # THE FILE IS AGAIN REMOVED TO SAVE HARD DISC SPACE
    # *************************************************
    remove(reconciled_file_path)
    # *************************************************

    elapse = datetime.timedelta(seconds=time.time() - start)
    print(F'\t{elapse} SO FAR...')

    print("\t3. CLUSTERING THE NEW REFINED LINKS")
    print("\n4. results\n\t1. FOUND [{}] EXTENDED CLUSTERS".format(len(extended_clusters)))
    print("\t2. FOUND [{}] CYCLES".format(len(list_extended_clusters_cycle)))
    elapse = datetime.timedelta(seconds=time.time() - start)
    Ut.completed(elapse)
    # print('{:.^100}'.format(F" COMPLETED IN {elapse} "))
    # print('{:.^100}'.format(F" JOB DONE! "))
    # print("\n{:.^100}".format(" WE ARE ABOUT TO CLUSTER AND SERIALISED"))

    return extended_file_name, reconciled_clusters_serialised_file


# *************************************************************
# *************************************************************
"THESE FUNCTIONS BELOW ARE USED IN THE EXTENSION AND" \
"FOR COMPUTING CYCLES AND RESOURCES RECONCILIATIONS"
# *************************************************************
# *************************************************************


def link_cluster_deserialization(serialisation_dir, main_file_name):

    print("\n{:>13}: {}".format("DIRECTORY ", serialisation_dir))
    print("{:>13}: {}".format("FILE ", main_file_name))

    # try:
    if True:
        # DE-SERIALISING THE MAIN DICTIONARY OF CLUSTER
        print("\n\tREADING FROM SERIALISED FILE 1...")
        clusters = Ut.pickle_deserializer(serialised_folder=serialisation_dir, name=F"{main_file_name}-1.txt")

        # DE-SERIALISING THE ROOT DICTIONARY SUPPORTING THE MAIN DICTIONARY OF CLUSTERS
        print("\tREADING FROM SERIALISED FILE 2...")
        node2cluster_id = Ut.pickle_deserializer(serialised_folder=serialisation_dir, name=F"{main_file_name}-2.txt")

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

    # GET THE SHORTEST PATH (THE FUNCTION RETURNS ONLY ONE PATH)
    # print "GRAPH-1:", g.__str__()
    # print "\t\t\v ", start_node, "AND", end_node
    result = nx.shortest_path(g, source=start_node, target=end_node)
    diameter = len(result) - 1
    # print "RESULT-1:", result
    results = []

    # FIND OTHER PATHS OF THE SAME SIZE
    if len(nodes) > 30:
        results = [result]

    # FINDING ALL SHORTEST PATHS AND GET THE HIGHEST WEIGHTED ONE
    # HOWEVER, IF THE CLUSTER IS TOO BIG, DO NO BOTHER USE THE ONLY ONE PROVIDED BY RESULT
    elif result is not None:

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
    validation_strength = (100 - c_penalty * (2 * ev_diameter - ev_w_diameter - 1)) / float(100)
    strength = min(float(sim), validation_strength) if float(sim) > 0 else validation_strength
    return 0 if strength < 0 else strength


def evidence_penalty(investigated_diameter, evidence_diameter, penalty_percentage=10):

    penalty = (100 - penalty_percentage * (evidence_diameter - 1)) / float(100)
    return 0 if penalty < 0 else (1 / float(investigated_diameter)) * penalty



# ****************************************************
# ****************************************************
" STATISTICS"
# ****************************************************
# ****************************************************


def ilns_distribution(serialisation_dir, serialized_cluster_name,
                      label="ILNs DISTRIBUTION", print_latex=False, xmax=None, activated=False):

    print(serialisation_dir)
    print(serialized_cluster_name)
    print(label)
    print(print_latex)
    print(xmax)
    print(activated)


    if activated is False:
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
    ilns = link_cluster_deserialization(serialisation_dir, serialized_cluster_name)
    distribution = {}

    # COMPUTE THE FREQUENCY
    for id, cluster in ilns['clusters'].items():
        size = len(cluster['nodes'])
        if size not in distribution:
            distribution[size] = 1
        else:
            distribution[size] += 1

    for key in sorted(distribution.keys()):

        # COUNT CLUSTER BELOW 31 AND ABOVE 30
        if key < 31:
            first += distribution[key]
        else:
            second += distribution[key]

        total += distribution[key]

        # BUILDING THE HISTOGRAM FOR LATEX
        if count == 0:
            hist += (F'\n\t\t({key}, {distribution[key]}) ')
        elif count % 5 == 0:
            hist += (F'\n\t\t({key}, {distribution[key]}) ')
        else:
            hist += (F'\t\t({key}, {distribution[key]}) ')

        count += 1

    accumulated = 0
    count_20 = 0
    x_max = 0
    x_95 = 0
    y_95 = 0
    for key in sorted(distribution.keys()):
        if round(((accumulated / float(total)) * 100 ), 2) < 95:
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
    \\addplot [ybar, bar width=6pt, color=red] coordinates {{ ({x_95}.5, {y_95}) }};
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

    stat_up = round((first/ (first + second)) * 100, 2)
    stat_down = round((second / (first + second)) * 100, 2)
    print("{:.^100}".format(' DISTRIBUTION RESULTS '))
    print("\tTHE TOTAL NUMBER OF CLUSTERS        {} ".format(first + second))
    print("\t95% CLUSTERS IS REACHED AT SIZE     {} ".format(x_95))
    print("\tNUMBER OF CLUSTERS OF SIZE BELOW 31 {} REPRESENTING {}% OF THE TOTAL".format(first, stat_up))
    print("\tNUMBER OF CLUSTERS OF SIZE ABOVE 30 {} REPRESENTING {}% OF THE TOTAL".format(second, stat_down))
    print("{:.^100}".format(''))

    return hist


# ****************************************************
"       VISUALISATION: INVESTIGATED vs EVIDENCE     "
# ****************************************************

def cluster_vis_input(specs, visualisation_obj=None, resources_obj=None, dataset_obj=None, activated=False):
    # print_object(specs)
    """
    :param specs: CONTAINS ALL INFORMATION FOR GENERATING
                  THE CLUSTER FOR VISUALISATION PURPOSES.
    :param activated: BOOLEAN ARGUMENT FOR NOT RUNNING THE FUNCTION UNLESS SPECIFICALLY REQUESTED
    param visualisation_obj: A DICTIONARY ABOUT LIST OF NODES AND LINKS AND MORE. T
                             HIS IS THE NEEDED OBJECT FOR VISUALISATION
    param resources_obj: THIS IS A DICTIONARY THAT MAPS THE URI OF A NODE TO ITS UNIQUE LABEL
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

    if activated is False:
        return

    start = time.time()
    tab = "" if visualisation_obj is None else "\t"
    fill = 100 if visualisation_obj is None else 96

    print("\n{}{:.^{}}".format(tab, F"", fill))
    print("{}{:.^{}}".format(tab,
        F" VISUALISING CLUSTER {specs['cluster_id']} OF SIZE {len(specs['cluster_data']['nodes'])} ", fill))
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

                    # THE DATATYPE EXISTS ALREADY FOR THIS DATASET
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
            ext_cluster = clusters[evidence_id]
            ext_specifications = {

                "data_store": specs['data_store'],
                "cluster_id": evidence_id,
                # "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
                # "associations": 'GA-related-paper.csv',
                # "serialised": 'Serialized_Cluster_PH1f99c8924c573d6_ga',
                "cluster_data": {

                    "nodes": ext_cluster['nodes'] if ext_cluster else [],

                    'strengths': ext_cluster['strengths'] if ext_cluster else {},

                    "links": ext_cluster["links"] if ext_cluster else []
                },
                "properties": specs['properties']
            }

            # RECURSIVE CALL
            cluster_vis_input(
                ext_specifications, visualisation_obj=vis_data,
                resources_obj=resources, dataset_obj=dataset_index, activated=activated)


    # ***************************************************************
    print(F"\n{tab}--> 3. FETCHING THE QUERY RESULT DEPENDING ON THE QUERY TYPE")
    # ***************************************************************
    # NOW, CONVERTS THE SET OF NODE TO A LIST FOR FETCHING THE LABELS
    specs["cluster_data"]["nodes"] = list(overall_nodes)

    try:
        query = Middleware.node_labels_switcher[data_store](
            resources=specs["cluster_data"]["nodes"], targets=nodes_vis_properties)
        # print(query)

    except KeyError as err:
        query = None
        print(F"\tKEY ERROR: {err}")

    # ***************************************************************
    print(F"\n{tab}--> 4. RUNNING THE QUERY")
    # ***************************************************************
    # query = "select distinct ?subject " \
    #         "{ GRAPH <http://risis.eu/dataset/eter_2014> {?subject a ?o} } limit 3"
    result = None
    if data_store in Middleware.run_query_matrix_switcher:
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
            formated_uri = to_nt_format(uri)
            if i_dataset not in dataset_index:
                dataset_index[i_dataset] = hash_number(i_dataset)

            # DOCUMENTING THE RESOURCE LABELS.
            # THIS MAKES SURE NODE WITH ALTERNATIVE NAME DO NOT CAME MORE THAN ONCE
            if formated_uri not in resources:

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                db_label = get_uri_local_name_plus(i_dataset)

                underscore = db_label.split('__')
                db_label = underscore[1] if len(underscore) > 1 else db_label
                label = f'-- {label}'

                resources[formated_uri] = F"{label} ({db_label} {get_uri_local_name_plus(uri)})"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formated_uri],
                    "uri": uri,
                    "group": dataset_index[i_dataset],
                    "size": "8" if visualisation_obj is None else "5"}

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
            Ut.completed(datetime.timedelta(seconds=time.time() -start))
        return vis_data

    # RETURN FEEDBACK
    else:

        print('\n\tTHE QUERY DID NOT YEILD ANY RESULT...'
              '\n\tIF YOU ARE EXPECTING RESULTS, PLEASE CHECK THE AUTOMATED QUERY FOR FURTHER DEBUGGING.')

        if len(specs["cluster_data"]["nodes"]) == 0:
            print('\tA QUICK CHECK SHOWS THAT THE CLUSTER HAS NO RESOURCE (NO NODES).')

            # IF THE INVESTIGATED CLUSTER EXTENDS, COLLECT ALL ILNS IT EXTENDS TO
            # FOR EACH EXTENDED CLUSTER, ADD THE NODES
            # FOR EACH EXTENDED CLUSTER, ADD THE LINKS
            # ADD THE ASSOCIATION

            # LIST OF CLUSTERS THAT EXTEND

            # print_object(root_reconciled)
            # print(type(root_reconciled))


# ****************************************************
"    VISUALISATION: INVESTIGATED vs SUB-CLUSTERS     "
# ****************************************************

def cluster_vis_input_2(specs, visualisation_obj=None, activated=False):

    """
    :param specs: CONTAINS ALL INFORMATION FOR GENERATING
                  THE CLUSTER FOR VISUALISATION PURPOSES.
    param visualisation_obj: A DICTIONARY ABOUT LIST OF NODES AND LINKS AND MORE. T
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

    if activated is False:
        return

    start = time.time()
    tab = "" if visualisation_obj is None else "\t"
    fill = 100 if visualisation_obj is None else 96
    print("\n{}{:.^{}}".format(tab, F"", fill))
    print("{}{:.^{}}".format(tab,
        F" VISUALISING CLUSTER {specs['cluster_id']} OF SIZE {len(specs['cluster_data']['nodes'])} ", fill))
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

                    # THE DATATYPE EXISTS ALREADY FOR THIS DATASET
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
    if is_restructured is True:
        reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-1.txt")
        root_reconciled = pickle_deserializer(CLUSTER_SERIALISATION_DIR, F"{specs['sub_clusters']}-2.txt")

    # NO NEED TO CONTINUE AS NO RESULT WAS FETCHED FROM THE DB SEVER
    sub_vis = None
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

                if is_restructured is True and formatted_uri in root_reconciled:
                    sub_clusters_id.add(root_reconciled[formatted_uri])

                # REFORMATTING THE NODE'S LABEL FOR GENERATING A UNIQUE IDEA
                db_label = get_uri_local_name_plus(i_dataset)

                underscore = db_label.split('__')
                db_label = underscore[1] if len(underscore) > 1 else db_label
                label = f'-- {label}'

                resources[formatted_uri] = F"{label} ({db_label} {get_uri_local_name_plus(uri)})" \
                    if visualisation_obj is None else F"{label} ({db_label} {get_uri_local_name_plus(uri)})"

                # CREATE THE NODE OBJECT FOR VISUALISATION
                node_dict = {
                    'id': resources[formatted_uri],
                    "uri": uri,
                    "group": dataset[i_dataset],
                    "size": "8" if visualisation_obj is not None else "5" }

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

            for id in sub_clusters_id:
                temp = reconciled[id]
                specifications = {

                    "data_store": specs['data_store'],
                    "cluster_id": id,

                    # "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
                    "associations": specs['associations'],
                    "serialised": specs['serialised'],


                    "cluster_data": {

                        "nodes": temp['nodes'] if temp else [],

                        'strengths': temp['strengths'] if temp else {},

                        "links": temp["links"] if temp else []
                    },

                    "properties": specs['properties']
                }

                cluster_vis_input_2(specifications, visualisation_obj=sub_vis, activated=activated)
                # cluster_vis_input_2(specifications, visualisation_obj=vis_data, activated=activated)

                add_vis_evidence(specifications, sub_vis, specs['sub_clusters'],
                                 resources_obj=resources, dataset_obj=dataset, activated=activated)

                # print_object(sub_vis)


        # --> 3. RETURNING THE VISUALISATION OBJECT FOR RENDERING
        # print_object(vis_data)
        if visualisation_obj is None:
            Ut.completed(datetime.timedelta(seconds=time.time() - start))
        return vis_data, sub_vis
        # return vis_data

    # RETURN FEEDBACK
    else:

        print('\n\tTHE QUERY DID NOT YEILD ANY RESULT...'
              '\n\tIF YOU ARE EXPECTING RESULTS, PLEASE CHECK THE AUTOMATED QUERY FOR FURTHER DEBUGGING.')

        if len(specs["cluster_data"]["nodes"]) == 0:
            print('\tA QUICK CHECK SHOWS THAT THE CLUSTER HAS NO RESOURCE (NO NODES).')

    # IF THE INVESTIGATED CLUSTER EXTENDS, COLLECT ALL ILNS IT EXTENDS TO
    # FOR EACH EXTENDED CLUSTER, ADD THE NODES
    # FOR EACH EXTENDED CLUSTER, ADD THE LINKS
    # ADD THE ASSOCIATION

    # LIST OF CLUSTERS THAT EXTEND

    # print_object(root_reconciled)
    # print(type(root_reconciled))


def find_associations(nodes, text):

    associated = []

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
                # "sub_clusters": 'Serialized_Cluster_Reconciled_PH1f99c8924c573d6',
                # "associations": 'GA-related-paper.csv',
                # "serialised": 'Serialized_Cluster_PH1f99c8924c573d6_ga',
                "cluster_data": {

                    "nodes": ext_cluster['nodes'] if ext_cluster else [],

                    'strengths': ext_cluster['strengths'] if ext_cluster else {},

                    "links": ext_cluster["links"] if ext_cluster else []
                },
                "properties": specs['properties']
            }

            # RECURSIVE CALL
            cluster_vis_input(
                ext_specifications, visualisation_obj=vis_obj,
                resources_obj=resources_obj, dataset_obj=dataset_obj, activated=activated)

    # ADDING THE ASSOCIATION LINKS
    if associations is not None:
        for link in associations:
            formatted_src = to_nt_format(link[0])
            formatted_trg = to_nt_format(link[1])
            if formatted_src in resources_obj and formatted_src in resources_obj:
                link_dict = {
                    "source": resources_obj[formatted_src],
                    "target": resources_obj[formatted_trg],
                    "distance": 250, "value": 4,
                    "color": "purple",
                    "dash": "20,10,5,5,5,10"
                }
                vis_obj["links"].append(link_dict)

# lavale












import rdflib
from rdflib import Graph
def convert_rdf(source, save_in, convert_to="nt"):

    data = Graph()
    start = time.time()
    data.parse(source, format=rdflib.util.guess_format(source))
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


source_file = "C:\Productivity\\3-MatchingTools\Data\grid-2019-02-17\grid.nt"
save_file_as = "C:\Productivity\\3-MatchingTools\Data\grid-2019-02-17\grid-02.nt"
# file_sample(source=source_file, save_as=save_file_as, sample_size=500000)


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
"RETESTING GOLDEN AGENT 50 YEARS RESTRICTION"
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




# GOLDEN_DIR = "C:\Productivity\ALenticularLens\Golden_50_Years"
# GOLDEN_LINKSET_CSV = "GA-linkset-paper.csv"
#
# # 1. GENERATE THE ILN CLUSTERS
# SCA = simple_csv_link_clustering(
#     csv_path=join(GOLDEN_DIR, GOLDEN_LINKSET_CSV),
#     graph_name="GOLDEN AGENT 50 YEARS RESTRICTION", save_in=GOLDEN_DIR, activated=False)
#
# # 2. EXTEND THE CLUSTERS
# extend_cluster(
#     GOLDEN_DIR, serialized_cluster_name="Serialized_Cluster",
#     csv_association_file=join(GOLDEN_DIR, "GA-related-paper.csv"),
#     save_in=GOLDEN_DIR,  condition_30=True, activated=False)
#
# # 3. OUTPUTS THE DISTRIBUTION OF THE CLUSTERS FOR LATEX VISUALISATION
# distributions = ilns_distribution(
#     GOLDEN_DIR, serialized_cluster_name="Serialized_Cluster",
#     label="golden agent data II",  print_latex=True, xmax=None, activated=False)

# import sys
# def current_line(n=1):
#     CURSOR_UP_ONE = '\x1b[1A'
#     ERASE_LINE = '\x1b[2K'
#     for _ in range(n):
#         sys.stdout.write(CURSOR_UP_ONE)
#         sys.stdout.write(ERASE_LINE)
#
#
# for i in range(1000000):
#     # print(i)
#     sys.stdout.write('\r'+str(i)+",")


# print(max(map(float, [1, 2, 3, 4])))



# # PLOTS
# import matplotlib.pyplot as plt
#
# # An "interface" to matplotlib.axes.Axes.hist() method
# n, bins, patches = plt.hist(x=d, bins='auto', color='#0504aa',
#                             alpha=0.7, rwidth=0.85)
# plt.grid(axis='y', alpha=0.75)
# plt.xlabel('Value')
# plt.ylabel('Frequency')
# plt.title('My Very Own Histogram')
# plt.text(23, 45, r'$\mu=15, b=3$')
# maxfreq = n.max()
# # Set a clean upper y-axis limit.
# plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

# DISTRIBUTION
golden = 'Serialized_Cluster_P5033440649046249801'
# cedric = 'Serialized_Cluster_PHfbfe75a2326666c2ef85'
# ludo = "Serialized_Cluster_PH76371785fe735ad1b74f"
# ilns_distribution = ilns_distribution("C:\Productivity\ALenticularLens", golden,
#                                  label="golden agent data",  print_latex=False, xmax=None, activated=False)
# print(distributions)

# f_name = simple_csv_link_clustering(
#     "C:\Productivity\ALenticularLens\export.csv", "mygraph", "C:\Productivity\ALenticularLens")
# sca = link_cluster_deserialization("C:\Productivity\ALenticularLens", "Serialized_Cluster_PH76371785fe735ad1b74f")


# extend_cluster("C:\Productivity\ALenticularLens", "Serialized_Cluster_PH76371785fe735ad1b74f", "related.csv")
# print(sys.version)

# DEDRIC
# f_name = simple_csv_link_clustering(
#     "C:\Productivity\ALenticularLens\\14dfe6fbe0fd677288ae055ede75f49b_output.csv",
#     "mygraph", "C:\Productivity\ALenticularLens")
# link_cluster_deserialization("C:\Productivity\ALenticularLens", "Serialized_Cluster_PHfbfe75a2326666c2ef85")



# cedric = "E:\\14dfe6fbe0fd677288ae055ede75f49b_output.nq\\14dfe6fbe0fd677288ae055ede75f49b_output.nq"
#
# with open(cedric, encoding='utf-8', mode='r') as linkset:
#     temp = ""
#     count, pair = 0, 0
#     patern = "(<.*>) <http://www.w3.org/2002/07/owl#sameAs> (<.*>)"
#     for line in linkset:
#         # print(line)
#         count += 1
#         if line.__contains__("<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "):
#             continue
#         else:
#             result = re.findall(pattern=patern, string=line)
#             if result:
#                 pair += 1
#                 temp = "{}".format(result[0][0])
#                 if pair == 2:
#                     pair = 0
#                     temp += " {} 1".format(result[0][0])
#                     print(temp)
#
#         if count == 50:
#             break