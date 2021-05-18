# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   RECONSTRUCTION OF A LINKSET/LES SPECIFICATIONS USING THE FOLLOWING URL.                               #
#       Job     : https://recon.diginfra.net/job/[job_id]                                                 #
#       Cluster : https://recon.diginfra.net/job/[job_id]/clusterings                                     #
#       Linkset : https://recon.diginfra.net/job/[job_id]/linksets"                                       #
#                                                                                                         #
# #########################################################################################################

import requests
from copy import deepcopy
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from ll.org.Export.Scripts.General import getUriLocalNamePlus
from ll.org.Export.Scripts.LinkPredicates import LinkPredicates
from ll.org.Export.Scripts.AnnotatedLinkset import linkset
from ll.org.Export.Scripts.AnnotatedLinkset_Generic import toLinkset
from ll.org.Export.Scripts.General import validateRDFStar, validateRDF
from ll.org.Export.Scripts.Specs2Metadata import printSpecs
from ll.org.Export.Scripts.General import printTime
from ll.org.Export.Scripts.Resources import Resource as Rsc


# Checks the correctness of the local name in a turtle RDF format
def checkLocalName(string):

    """
    This code checks whether the provided local name of a turtle RDF format is correct indeed.
    It returns TRUE if the input string does not contain irregularities and FALSE otherwise.
    For example:
        - in [sem:#Time], "#Time" is not a correct local name.
        - in [ns2:ontology/HuwelijkseVoorwaarden] "ontology/HuwelijkseVoorwaarden" is not a correct local name
    """

    if True in [s in ['/', '#', '\\'] for s in string]:
        # print(F"{string:20} : {False}")
        return False
    # print(F"{string:20} : {True}")
    return True


def method_conditions(method_conditions_list, entity_type_selections, dataset_specs, prefixes):

    problems = {}

    def intermediate(i_path):

        keys = ['intermediate_source', 'intermediate_target']
        ent_sel_id = entity_type_selections[i_path['entity_type_selection']]['dataset']['dataset_id']
        ent_type = entity_type_selections[i_path['entity_type_selection']]['dataset']['collection_id']

        for key in keys:

            temp_ent_type = ent_type
            s_uris, l_uris = [], []

            # SINGLE PROPERTY HAS BEEN SELECTED
            if len(i_path[key][0]) == 1:

                l_uri = dataset_specs[
                    ent_sel_id]['collections'][temp_ent_type]['properties'][i_path[key][0][0]]['uri']

                s_uri = dataset_specs[
                    ent_sel_id]['collections'][temp_ent_type]['properties'][i_path[key][0][0]]['shortenedUri']

                # Collect namespaces
                if s_uri:
                    ns = s_uri.split(':')
                    if len(ns) == 2:
                        if l_uri and checkLocalName(ns[1]) is False:
                            ns[1] = getUriLocalNamePlus(l_uri)
                            s_uri = F"{ns[0]}:{ns[1]}"

                        ns[1] = l_uri.replace(ns[1], '') if l_uri else "http://problem/long-uri-not-provided"
                        prefixes[ns[1]] = ns[0]

                s_uris.append(s_uri)
                l_uris.append(l_uri)

            # A PROPERTY PATH HAS BEEN SELECTED
            else:

                for features in i_path[key]:

                    for idx, feature in enumerate(features):

                        if (idx + 1) % 2 != 0:

                            if 'uri' == feature:
                                l_uri = feature
                                s_uri = feature

                            else:
                                l_uri = dataset_specs[ent_sel_id][
                                    'collections'][temp_ent_type]['properties'][feature]['uri']

                                s_uri = dataset_specs[ent_sel_id][
                                    'collections'][temp_ent_type]['properties'][feature]['shortenedUri']

                            # Collect namespaces
                            if l_uri and s_uri and l_uri != s_uri:

                                ns = s_uri.split(':')
                                if len(ns) == 2:
                                    if checkLocalName(ns[1]) is False:
                                        ns[1] = getUriLocalNamePlus(l_uri)
                                        s_uri = F"{ns[0]}:{ns[1]}"

                                    ns[1] = l_uri.replace(ns[1], '')
                                    prefixes[ns[1]] = ns[0]

                            if l_uri is None and feature not in problems:
                                problems[feature] = True
                                print(F"\n\t{len(problems):3}. DATA PROBLEM: Long URI is none.\n"
                                      F"\n\t\t\t{entity_type_selections[i_path['entity_type_selection']]['label']}"
                                      F"\n\t\t\t{feature} ==-> [ short: {s_uri} ] [ long: {l_uri} ]")

                            # UPDATE SHORT AND LONG URI
                            s_uris.append(s_uri)
                            l_uris.append(l_uri)

                        else:
                            temp_ent_type = feature

                            # print(F"{e_type} -> {dataset_specs[id]['collections'][e_type]['shortenedUri']}")
                            if temp_ent_type in dataset_specs[ent_sel_id]['collections']:
                                s_uri = dataset_specs[ent_sel_id]['collections'][temp_ent_type]['shortenedUri']
                                l_uri = dataset_specs[ent_sel_id]['collections'][temp_ent_type]['uri']
                            else:
                                s_uri = temp_ent_type
                                l_uri = temp_ent_type

                            # Collect namespaces
                            if l_uri != s_uri:
                                ns = s_uri.split(':')
                                if len(ns) == 2:
                                    if checkLocalName(ns[1]) is False:
                                        ns[1] = getUriLocalNamePlus(l_uri)
                                        s_uri = F"{ns[0]}:{ns[1]}"
                                    ns[1] = l_uri.replace(ns[1], '')
                                    prefixes[ns[1]] = ns[0]

                            s_uris.append(s_uri)
                            l_uris.append(l_uri)

            # update
            i_path[F'short_{key}'] = s_uris
            i_path[F'long_{key}'] = l_uris

    for method in method_conditions_list:

        if 'conditions' in method:
            method_conditions(method['conditions'], entity_type_selections, dataset_specs, prefixes)

        else:
            # print("\n-->", method['method'])
            if 'date_part' in method['method']:
                prefixes[Sns.Time.time] = "time"

            if 'intermediate_source' in method['method']['config']:
                method_config = method['method']['config']
                entity_type_selection_id = method_config['entity_type_selection']
                intermediate(method_config)
                method_config[entity_type_selection_id] = entity_type_selections[entity_type_selection_id]

            for rsc_trg in ['sources', 'targets']:

                # A DICTIONARY OF SELECTED ENTITY-TYPE IDS
                for e_sel_idx, property_list in method[rsc_trg]['properties'].items():

                    e_sel_idx = int(e_sel_idx)
                    e_sel_id = entity_type_selections[e_sel_idx]['dataset']['dataset_id']
                    e_type = entity_type_selections[e_sel_idx]['dataset']['collection_id']

                    # A LIST OF SELECTED PROPERTIES FOR THE CURRENTLY SELECTED ENTITY TYPE
                    for choices in property_list:

                        short_uris, long_uris = [], []
                        choice = choices['property']

                        # SINGLE PROPERTY HAS BEEN SELECTED
                        if len(choice) == 1:
                            long_uri = dataset_specs[e_sel_id]['collections'][e_type]['properties'][
                                choice[0]]['uri'] if choice[0] != 'uri' else Rsc.ga_resource_ttl('uri')

                            short_uri = dataset_specs[
                                e_sel_id]['collections'][e_type]['properties'][choice[0]][
                                'shortenedUri'] if choice[0] != 'uri' else Rsc.ga_resource_ttl('uri')

                            # Collect namespaces
                            if long_uri and short_uri and long_uri != short_uri:
                                ns = short_uri.split(':')
                                if len(ns) == 2:
                                    if checkLocalName(ns[1]) is False:
                                        ns[1] = getUriLocalNamePlus(long_uri)
                                        short_uri = F"{ns[0]}:{ns[1]}"

                                    ns[1] = long_uri.replace(ns[1], '')
                                    prefixes[ns[1]] = ns[0]

                            short_uris.append(short_uri)
                            long_uris.append(long_uri)

                        # A PROPERTY PATH HAS BEEN SELECTED
                        else:

                            for i, property_list_1 in enumerate(choice):

                                if (i + 1) % 2 != 0:

                                    if property_list_1 == 'uri':
                                        long_uri = property_list_1
                                        short_uri = property_list_1

                                    else:

                                        long_uri = dataset_specs[e_sel_id][
                                            'collections'][e_type]['properties'][property_list_1]['uri']

                                        short_uri = dataset_specs[e_sel_id][
                                            'collections'][e_type]['properties'][property_list_1]['shortenedUri']

                                    # Collect namespaces
                                    if long_uri and short_uri and long_uri != short_uri:

                                        ns = short_uri.split(':')
                                        if len(ns) == 2:
                                            if checkLocalName(ns[1]) is False:
                                                ns[1] = getUriLocalNamePlus(long_uri)
                                                short_uri = F"{ns[0]}:{ns[1]}"

                                            ns[1] = long_uri.replace(ns[1], '')
                                            prefixes[ns[1]] = ns[0]

                                    if long_uri is None and property_list_1 not in problems:
                                        problems[property_list_1] = True
                                        print(F"\n\t{len(problems):3}. DATA PROBLEM: Long URI is none.\n"
                                              F"\n\t\t\t{choice}"
                                              F"\n\t\t\t{property_list_1} ==-> [ short: {short_uri} ] [ long: {long_uri} ]")

                                    # UPDATE SHORT AND LONG URI
                                    short_uris.append(short_uri)
                                    long_uris.append(long_uri)

                                else:
                                    e_type = property_list_1

                                    # print(F"{e_type} -> {dataset_specs[id]['collections'][e_type]['shortenedUri']}")
                                    if e_type in dataset_specs[e_sel_id]['collections']:
                                        short_uri = dataset_specs[e_sel_id]['collections'][e_type]['shortenedUri']
                                        long_uri = dataset_specs[e_sel_id]['collections'][e_type]['uri']
                                    else:
                                        short_uri = e_type
                                        long_uri = e_type

                                    # Collect namespaces
                                    if long_uri != short_uri:
                                        ns = short_uri.split(':')
                                        if len(ns) == 2:
                                            if checkLocalName(ns[1]) is False:
                                                ns[1] = getUriLocalNamePlus(long_uri)
                                                short_uri = F"{ns[0]}:{ns[1]}"
                                            ns[1] = long_uri.replace(ns[1], '')
                                            prefixes[ns[1]] = ns[0]

                                    short_uris.append(short_uri)
                                    long_uris.append(long_uri)

                        # update
                        choices['short_properties'] = short_uris
                        choices['long_properties'] = long_uris


# GIVEN A LINKSET, COLLECT ITS SPECIFICATION
def linksetSpecsData(linksetId, job, filePath, save_in, starReification, printSpec=True):

    printTime()
    prefixes = {}

    # 1. Collecting information on the available datasets
    dataset_url = "https://recon.diginfra.net/datasets?endpoint=https://repository.goldenagents.org/v5/graphql"
    dataset_specs = requests.get(dataset_url).json()

    # 1.1 LINKSET URI
    try:
        url = F"https://recon.diginfra.net/job/{job}"
        lst_specs = requests.get(url).json()
        # print(lst_specs)
    except ValueError:
        print("\nTHE JOB REQUEST CAN N0T BE PLACED")
        return

    # 1.2 LINKSET STATS
    stats_url_1 = F"https://recon.diginfra.net/job/{job}/clusterings"
    stats_url2 = F"https://recon.diginfra.net/job/{job}/linksets"

    # 1.3 GETTING THE ENTITY SELECTION OBJECT FROM THE lst_specs
    entity_type_selections = lst_specs['entity_type_selections']

    # 2. RESET THE RIGHT lst_specs WITH THE ACTUAL SPECS
    try:

        found = False
        for counter, spec in enumerate(lst_specs['linkset_specs']):
            # print(spec['id'], linksetId)
            if spec['id'] == linksetId:
                # print(F"DESCRIPTION: {spec['label']}")
                found, lst_specs = True, spec
                break

        if found is False:
            print(F"\nTHE LINKSET WITH ID: [{linksetId}] COULD NOT BE FOUND")
            return

    except IndexError as err:
        print(F"\n-> THE LINKSET [{linksetId}] CAN NOT BE FOUND DUE TO INDEX OUT OF RANGE ERROR")
        return

    # 3. MISSING SETTINGS
    linkset_name = lst_specs['id']
    lst_specs["job_id"] = job
    lst_specs["linkType"] = LinkPredicates.sameAs_tt
    lst_specs["creator"] = "AL IDRISSOU"
    lst_specs["publisher"] = "GoldenAgents"

    # 4. ENTITY SELECTIONS IN A DICTIONARY AS {ID: SELECTION OBJECT}
    # entity_type_selections = lst_specs['entity_type_selections']
    entity_type_selections = {selection['id']: selection for selection in entity_type_selections}

    # 5. UPDATING SOURCE AND TARGET WITH THEIR RESPECTIVE OBJECTS
    sources, targets, methods = lst_specs['sources'], lst_specs['targets'], lst_specs['methods']['conditions']

    # #######################################################
    # 6. UPDATE OF SOURCE AND TARGET                        #
    # #######################################################
    def method_conditions(conditions_list):

        for method in conditions_list:

            if 'conditions' in method:
                # print(method, "\n")
                method_conditions(method['conditions'])

            else:
                for selected in [method['sources'], method['targets']]:
                    for path in selected:
                        ttl_uri, uris = [], []
                        id = entity_type_selections[path['entity_type_selection']]['dataset']['dataset_id']
                        e_type = entity_type_selections[path['entity_type_selection']]['dataset']['collection_id']

                        for i, path_item in enumerate(path['property']):

                            # THE ACTUAL PROPERTY
                            if (i + 1) % 2 != 0:
                                uri = dataset_specs[id]['collections'][e_type]['properties'][path_item]['uri']
                                short = dataset_specs[id]['collections'][e_type]['properties'][path_item]['shortenedUri']

                                if uri is None:
                                    print(F"\n- DATA PROBLEM:\n\tShort : {short}\n\tLong  : {uri}")

                                # Collect namespaces
                                if uri and short and uri != short:
                                    ns = short.split(':')
                                    if len(ns) == 2:
                                        if checkLocalName(ns[1]) is False:
                                            ns[1] = getUriLocalNamePlus(uri)
                                            short = F"{ns[0]}:{ns[1]}"

                                        ns[1] = uri.replace(ns[1], '')
                                        prefixes[ns[1]] = ns[0]

                                ttl_uri.append(short)
                                uris.append(uri)

                            # THE ENTITY TYPE OF THE RESOURCE
                            else:
                                e_type = path_item

                                # print(F"{e_type} -> {dataset_specs[id]['collections'][e_type]['shortenedUri']}")
                                if e_type in dataset_specs[id]['collections']:
                                    short = dataset_specs[id]['collections'][e_type]['shortenedUri']
                                    uri = dataset_specs[id]['collections'][e_type]['uri']
                                else:
                                    short = e_type
                                    uri = e_type

                                print("==>>", short)

                                # Collect namespaces
                                if uri != short:
                                    ns = short.split(':')
                                    if len(ns) == 2:
                                        if checkLocalName(ns[1]) is False:
                                            ns[1] = getUriLocalNamePlus(uri)
                                            short = F"{ns[0]}:{ns[1]}"
                                        ns[1] = uri.replace(ns[1], '')
                                        prefixes[ns[1]] = ns[0]

                                ttl_uri.append(short)
                                uris.append(uri)

                        # update
                        path['short_properties'] = ttl_uri
                        path['uri_properties'] = uris

    method_conditions(methods)

    # #######################################################
    # 7. UPDATE OF SOURCE AND TARGET PROPERTIES OF FILTERS  #
    # #######################################################

    def update(item_list):

        for info in item_list:

            if 'property' in info:
                # print(F"\nX ---> {item_list}\n")
                # New list of property short names and uri
                short_properties, long_properties = [], []
                # the original entity type of the collection
                entity_type = collection_id

                for i, i_property in enumerate(info['property']):

                    # Odds numbers slots are container of a property name
                    if (i + 1) % 2 != 0:

                        # getting the short version of the current property
                        short_uri = dataset_specs[id]['collections'][entity_type]['properties'][i_property]['shortenedUri']

                        # getting the uri of the current property
                        long_uri = dataset_specs[id]['collections'][entity_type]['properties'][i_property]['uri']

                        if short_uri is None:
                            print(F"\n+ DATA PROBLEM:\n\tShort : {short_uri}\n\tLong  : {long_uri}")

                        # Collect namespaces
                        if long_uri and short_uri and long_uri != short_uri:

                            ns = short_uri.split(':')
                            # print(ns, "\n", short_uri, long_uri)
                            if len(ns) == 2:
                                if checkLocalName(ns[1]) is False:
                                    ns[1] = getUriLocalNamePlus(long_uri)
                                    short_uri = F"{ns[0]}:{ns[1]}"
                                ns[1] = long_uri.replace(ns[1], '')
                                prefixes[ns[1]] = ns[0]

                        short_properties.append(short_uri)
                        long_properties.append(long_uri)

                    # Even numbers slots are container of an entity type
                    else:

                        entity_type = i_property
                        curr_data = dataset_specs[id]['collections'][entity_type]

                        # print(id, "\n", entity_type, "\n", dataset_specs[id], "\n")

                        # # getting the short version of the current entity-type
                        # # getting the uri version of the current entity-type
                        short_uri, long_uri = curr_data['shortenedUri'], curr_data['uri']
                        # print(dataset_specs[id]['collections'][entity_type])

                        # Collect namespaces
                        if long_uri != short_uri:
                            ns = short_uri.split(':')
                            if len(ns) == 2:
                                if checkLocalName(ns[1]) is False:
                                    ns[1] = getUriLocalNamePlus(long_uri)
                                    short_uri = F"{ns[0]}:{ns[1]}"
                                ns[1] = long_uri.replace(ns[1], '')
                                prefixes[ns[1]] = ns[0]

                        short_properties.append(short_uri if short_uri else "...........")
                        long_properties.append(long_uri if long_uri else "...........")

                # update
                info['short_properties'] = short_properties
                info['uri_properties'] = long_properties

            if 'conditions' in info:
                # print(F"\nY ---> {item_list}\n")
                update(info['conditions'])

        # Reset the source or target selection
        selections[idx] = entity_type_selections[item_id]

    for selections in [sources, targets]:

        for idx, item_id in enumerate(selections):
            id = entity_type_selections[item_id]['dataset']['dataset_id']
            collection_id = entity_type_selections[item_id]['dataset']['collection_id']

            # RESOURCE TYPE SHORT AND LONG URI
            if 'shortenedUri' in dataset_specs[id]['collections'][collection_id] \
                    and len(dataset_specs[id]['collections'][collection_id]['shortenedUri']) > 0:
                entity_type_selections[item_id]['dataset']['short_uri'] = dataset_specs[id]['collections'][collection_id]['shortenedUri']
            else:
                entity_type_selections[item_id]['dataset']['short_uri'] = "......"

            if 'uri' in dataset_specs[id]['collections'][collection_id] \
                    and len(dataset_specs[id]['collections'][collection_id]['uri']) > 0:
                entity_type_selections[item_id]['dataset']['long_uri'] = dataset_specs[id]['collections'][collection_id]['uri']
            else:
                entity_type_selections[item_id]['dataset']['long_uri'] = "......"

            # Set the selected resource's name
            entity_type_selections[item_id]['dataset']['name'] = dataset_specs[id]['name']

            # Set the property/entity-type names
            condition_list = entity_type_selections[item_id]['filter']['conditions']

            # selection_rsc_type = dataset_specs[id]['name']
            # print(collection_id)

            # Property path condition
            update(condition_list)

            # Reset the source or target selection
            selections[idx] = entity_type_selections[item_id]

    # #######################################################
    # MERGING STATS
    # #######################################################
    stats_specs = requests.get(stats_url_1).json()
    for data in stats_specs:
        if data['spec_id'] == linkset_name:
            stats_specs = data
            break

    # IF THE LINKSET HAS NO STATS YET, SET THE stats_specs OBJECT
    if isinstance(stats_specs, list):
        stats_specs = {}
        print("\n\tTHERE IS NOT CLUSTERING STATS")

    # MOVE CLUSTER STATS TO LINKSET STATS
    stats_specs2 = requests.get(stats_url2).json()
    # found = False
    for data in stats_specs2:
        if data['spec_id'] == linkset_name:
            stats_specs.update(data)
            break

    # if found is False:
    #     print("THE LINKSET HAS NOT BEEN EXECUTED")

    # GETTING THE
    if "sources_count" in stats_specs and "targets_count" in stats_specs \
            and stats_specs["sources_count"] and stats_specs["targets_count"]:
        stats_specs['entities'] = stats_specs["sources_count"] + stats_specs["targets_count"]
    else:
        stats_specs['entities'] = 0

    # MISSING PARAMETERS IN LINKSET
    # 1. creator
    # 2. publisher
    # 3. linkType

    #  MISSING PARAMETERS IN in METHODS
    #   1. threshold_operator
    #   2. threshold
    #   3. property IRI

    specs = {'linksetStats': stats_specs, 'linksetSpecs': lst_specs}
    if printSpec:
        printSpecs(specs, tab=1)

    linkset_path = linkset(specs=specs, csv_linkset_file=filePath, save_in=save_in, rdfStarReification=starReification, prefixes=prefixes)

    if starReification:
        validateRDFStar(linkset_path, removeIt=True)
    else:
        validateRDF(linkset_path)


# GIVEN A LINKSET, COLLECT ITS SPECIFICATION
def linksetSpecsDataItr(
        linksetId: int, job: str, lst_result, save_in: str, starReification: bool, printSpec: bool = True):

    """
    :param linksetId        : An integer parameter denoting the ID of the linkset to convert into an RDF documentation.
    :param job              : A string parameter indicating the IF of job from which to find the selected linkset.
    :param lst_result       : An iterator object materializing a countable number of matching results to iterate through.
    :param save_in          : A string parameter materialising the directory in which to save the converted RDF version of the result.
    :param starReification  : A boolean parameter specifying whether the conversion should proceed with respect to
                              (1) the standard reification -> starReification = False or
                              (2) the RDFStar convebtion -> starReification = True.
    :param printSpec        : A boolean parameter for displaying the specification object if needed.
    :return:
    """

    printTime()
    prefixes = {}
    data_collected = {}
    home = "https://recon.diginfra.net"
    print(F"\n{'-' * 70}\n{'BUILDING THE SPECIFICATION':^70}\n{F'JOB IDENTIFIER : {job}':^70}\n{F'LINKSET INDEX : {linksetId}':^70}\n{'-' * 70}")

    clusters = {}
    try:
        limit, offset = 200000, 0

        while True:
            print(offset)
            clusters_uri = F"{home}/job/{job}/clusters/linkset/{linksetId}?apply_filters=false&with_properties=none&limit={limit}&offset={offset}"
            clusters_data = requests.get(clusters_uri).json()
            for item in clusters_data:
                clusters[item['id']] = item['size']
            offset = offset + limit
            if len(clusters_data) < limit:
                break
        print(clusters)
    except Exception as err:
        # clusters = None
        print("Problem", err)

    # print(clusters, clusters.__len__())
    # exit()

    # 1. Collecting information on the available datasets
    dataset_url = F"{home}/datasets?endpoint=https://repository.goldenagents.org/v5/graphql"
    dataset_specs = requests.get(dataset_url).json()
    data_collected['datasets'] = deepcopy(dataset_specs)

    # 1.1 LINKSET URI
    try:
        url = F"{home}/job/{job}"
        lst_specs = requests.get(url).json()
        data_collected['linkset'] = deepcopy(lst_specs)

    except ValueError:
        print("\nTHE JOB REQUEST CAN N0T BE PLACED")
        return

    # 1.2 LINKSET STATS
    stats_url_1 = F"{home}/job/{job}/clusterings"
    stats_url2 = F"{home}/job/{job}/linksets"

    # 1.3 GETTING THE ENTITY SELECTION OBJECT FROM THE lst_specs
    entity_type_selections = lst_specs['entity_type_selections']

    # 2. RESET THE RIGHT lst_specs WITH THE ACTUAL SPECS
    try:

        found = False
        for counter, spec in enumerate(lst_specs['linkset_specs']):
            if spec['id'] == linksetId:
                found, lst_specs = True, spec
                break

        if found is False:
            print(F"\nTHE LINKSET WITH ID: [{linksetId}] COULD NOT BE FOUND")
            return

    except IndexError as err:
        print(F"\n-> THE LINKSET [{linksetId}] CAN NOT BE FOUND DUE TO INDEX OUT OF RANGE ERROR")
        return

    # 3. MISSING SETTINGS
    linkset_name = lst_specs['id']
    lst_specs["job_id"] = job
    lst_specs["linkType"] = LinkPredicates.sameAs_tt
    lst_specs["creator"] = "AL IDRISSOU"
    lst_specs["publisher"] = "GoldenAgents"
    lst_specs['clusters'] = clusters

    # 4. ENTITY SELECTIONS IN A DICTIONARY AS {ID: SELECTION OBJECT}
    # entity_type_selections = lst_specs['entity_type_selections']
    entity_type_selections = {selection['id']: selection for selection in entity_type_selections}

    # 5. UPDATING SOURCE AND TARGET WITH THEIR RESPECTIVE OBJECTS
    sources, targets, methods = lst_specs['sources'], lst_specs['targets'], lst_specs['methods']['conditions']

    # ###############################################################################
    # 6. UPDATE OF SOURCE AND TARGET ALSO WITH SHORT AND LONG URIS                  #
    # ###############################################################################

    method_conditions(methods, entity_type_selections, dataset_specs, prefixes)

    # ###############################################################################
    # 7. UPDATE OF SOURCE AND TARGET PROPERTIES OF FILTERS WITH SHORT AND LONG URIS #
    # ###############################################################################

    def update(item_list):

        for info in item_list:

            if 'property' in info:

                # New list of property short names and uri
                short_properties, long_properties = [], []

                # the original entity type of the collection
                entity_type = collection_id

                for i, i_property in enumerate(info['property']):

                    # Odds numbers slots are container of a property name
                    if (i + 1) % 2 != 0:

                        # getting the short version of the current property
                        short_uri = dataset_specs[id][
                            'collections'][entity_type]['properties'][i_property]['shortenedUri'] \
                            if i_property != 'uri' else i_property

                        # getting the uri of the current property
                        long_uri = dataset_specs[id]['collections'][entity_type]['properties'][i_property]['uri'] \
                            if i_property != 'uri' else i_property

                        if short_uri is None:
                            print(F"\n+ DATA PROBLEM:\n\tShort : {short_uri}\n\tLong  : {long_uri}")

                        # Collect namespaces
                        if long_uri and short_uri and long_uri != short_uri:

                            ns = short_uri.split(':')
                            if len(ns) == 2:
                                if checkLocalName(ns[1]) is False:
                                    ns[1] = getUriLocalNamePlus(long_uri)
                                    short_uri = F"{ns[0]}:{ns[1]}"
                                ns[1] = long_uri.replace(ns[1], '')
                                prefixes[ns[1]] = ns[0]

                        short_properties.append(short_uri)
                        long_properties.append(long_uri)

                    # Even numbers slots are container of an entity type
                    else:

                        entity_type = i_property
                        curr_data = dataset_specs[id]['collections'][entity_type]

                        # # getting the short version of the current entity-type
                        # # getting the uri version of the current entity-type
                        short_uri, long_uri = curr_data['shortenedUri'], curr_data['uri']

                        # Collect namespaces
                        if long_uri != short_uri:
                            ns = short_uri.split(':')
                            if len(ns) == 2:
                                if checkLocalName(ns[1]) is False:
                                    ns[1] = getUriLocalNamePlus(long_uri)
                                    short_uri = F"{ns[0]}:{ns[1]}"
                                ns[1] = long_uri.replace(ns[1], '')
                                prefixes[ns[1]] = ns[0]

                        short_properties.append(short_uri if short_uri else "...........")
                        long_properties.append(long_uri if long_uri else "...........")

                # update
                info['short_properties'] = short_properties
                info['uri_properties'] = long_properties

            if 'conditions' in info:
                update(info['conditions'])

        # Reset the source or target selection
        selections[idx] = entity_type_selections[item_id]

    for selections in [sources, targets]:

        for idx, item_id in enumerate(selections):
            id = entity_type_selections[item_id]['dataset']['dataset_id']
            collection_id = entity_type_selections[item_id]['dataset']['collection_id']

            l_uri = dataset_specs[id]['collections'][collection_id]['uri']

            # RESOURCE TYPE SHORT AND LONG URI
            if 'shortenedUri' in dataset_specs[id]['collections'][collection_id] and len(
                    dataset_specs[id]['collections'][collection_id]['shortenedUri']) > 0:

                s_uri = dataset_specs[id]['collections'][collection_id]['shortenedUri']

                # COLLECTING NAMESPACES
                if l_uri and s_uri and l_uri != s_uri:
                    ns = s_uri.split(':')
                    if len(ns) == 2:
                        if checkLocalName(ns[1]) is False:
                            ns[1] = getUriLocalNamePlus(l_uri)
                            s_uri = F"{ns[0]}:{ns[1]}"
                        ns[1] = l_uri.replace(ns[1], '')
                        prefixes[ns[1]] = ns[0]

                entity_type_selections[item_id]['dataset']['short_uri'] = s_uri
                entity_type_selections[item_id]['dataset']['long_uri'] = l_uri

            else:

                entity_type_selections[item_id]['dataset']['long_uri'] = l_uri

                if 'uri' in dataset_specs[id]['collections'][collection_id] and len(
                        dataset_specs[id]['collections'][collection_id]['uri']) > 0:

                    local_name = getUriLocalNamePlus(l_uri)
                    prefix_uri = l_uri.replace(local_name, "")
                    prefix = getUriLocalNamePlus(prefix_uri)

                    entity_type_selections[item_id]['dataset']['long_uri'] = dataset_specs[
                        id]['collections'][collection_id]['uri']

                    entity_type_selections[item_id]['dataset']['short_uri'] = F"{prefix}:{local_name}"
                    prefixes[prefix_uri] = prefix

                else:
                    entity_type_selections[item_id]['dataset']['short_uri'] = "...... NO SHORT URI FOR THE RESOURCE ......"
                    entity_type_selections[item_id]['dataset']['long_uri'] = "...... NO LONG URI FOR THE RESOURCE ......"

            # Set the selected resource's name
            entity_type_selections[item_id]['dataset']['name'] = dataset_specs[id]['name']

            # Set the property/entity-type names
            condition_list = entity_type_selections[item_id]['filter']['conditions']

            # selection_rsc_type = dataset_specs[id]['name']
            # print(collection_id)

            # Property path condition
            update(condition_list)

            # Reset the source or target selection
            selections[idx] = entity_type_selections[item_id]

    # ###############################################################################
    # 8. MERGING STATS                                                                 #
    # ###############################################################################
    stats_specs = requests.get(stats_url_1).json()
    data_collected['cluster_stats'] = deepcopy(stats_specs)

    for data in stats_specs:
        if data['spec_id'] == linkset_name:
            stats_specs = data
            break

    # IF THE LINKSET HAS NO STATS YET, SET THE stats_specs OBJECT
    if isinstance(stats_specs, list):
        stats_specs = {}
        print("\n\tTHERE IS NOT CLUSTERING STATS")

    # MOVE CLUSTER STATS TO LINKSET STATS
    stats_specs2 = requests.get(stats_url2).json()
    data_collected['linkset_stats'] = deepcopy(stats_specs2)

    # found = False
    for data in stats_specs2:
        if data['spec_id'] == linkset_name:
            stats_specs.update(data)
            break

    # if found is False:
    #     print("THE LINKSET HAS NOT BEEN EXECUTED")

    # GETTING THE
    if "sources_count" in stats_specs and "targets_count" in stats_specs \
            and stats_specs["sources_count"] and stats_specs["targets_count"]:
        stats_specs['entities'] = stats_specs["sources_count"] + stats_specs["targets_count"]
    else:
        stats_specs['entities'] = 0

    # MISSING PARAMETERS IN LINKSET
    # 1. creator
    # 2. publisher
    # 3. linkType

    #  MISSING PARAMETERS IN in METHODS
    #   1. threshold_operator
    #   2. threshold
    #   3. property IRI

    specs = {'linksetStats': stats_specs, 'linksetSpecs': lst_specs}

    if printSpec:
        printSpecs(specs, tab=1)
    # print(specs)

    # CREATE THE LINKSET FILE
    linkset_path = toLinkset(
        specs=specs, save_in=save_in, linkset_result=lst_result, rdfStarReification=starReification, prefixes=prefixes)

    # VALIDATE THE FILE SYNTAX CORRECTNESS
    if starReification:
        validateRDFStar(linkset_path, removeIt=True)
    else:
        validateRDF(linkset_path)

    return linkset_path, data_collected
