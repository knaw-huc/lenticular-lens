# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   RECONSTRUCTION OF A LINKSET/LENS SPECIFICATIONS USING THE FOLLOWING URL.                               #
#       Job     : https://recon.diginfra.net/job/[job_id]                                                 #
#       Cluster : https://recon.diginfra.net/job/[job_id]/clusterings                                     #
#       Linkset : https://recon.diginfra.net/job/[job_id]/linksets"                                       #
#                                                                                                         #
# #########################################################################################################

import requests
import traceback

from time import time
from io import StringIO
from copy import deepcopy
from datetime import timedelta
from csv import reader as csv_reader
from ll.org.Export.Scripts.General import printTime
from ll.org.Export.Scripts.AnnotatedLinkset import linkset
from ll.org.Export.Scripts.Specs2Metadata import printSpecs
from ll.org.Export.Scripts.General import getUriLocalNamePlus
from ll.org.Export.Scripts.LinkPredicates import LinkPredicates
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from ll.org.Export.Scripts.AnnotatedLinkset_Generic import toLinkset, toLens, clusterGraphGenerator
from ll.org.Export.Scripts.General import validateRDFStar, validateRDF
from ll.org.Export.Scripts.Resources import Resource as Rsc
import ll.org.Export.Scripts.General as Grl


from collections import defaultdict


def ERROR(page, function, location, message):

    return F"\n\t{'File':15} : {page}.py\n" \
           F"\t{'Function':15} : {function}\n"\
           F"\t{'Whereabouts':15} : {location}\n"\
           F"\t{'Error Message':15} : {message}\n"\
           F"\t{'Error Stack':15} : \t{'' if not traceback.print_exc() else ''}"


def getLinks(job_id, set_id, isLinkset: bool):
    try:
        home = "https://recon.diginfra.net"
        # csv_url = F"{home}/job/{job_id}/csv/{'linkset' if isLinkset else 'lens'}/{set_id}"
        # print(F"{home}/job/{job_id}/motivate/{'linkset' if isLinkset else 'lens'}/{set_id}")
        # return csv_reader(StringIO(requests.get(csv_url).text))

        links = F"{home}/job/{job_id}/links/{'linkset' if isLinkset else 'lens'}/{set_id}?with_properties=none&limit=200000&offset=0"
        print("\n\nLinks of the linkset" if isLinkset else "\n\nLinks of the lens\n\t", links)
        return requests.get(links).json()
    except Exception:
        return None


# CHECKS THE CORRECTNESS OF GHE LOCAL NAME IN A TURTLE RDF FORMAT
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
    # print(method_conditions_list)
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

        try:

            if 'conditions' in method:
                method_conditions(method['conditions'], entity_type_selections, dataset_specs, prefixes)

            else:

                # print("\n-->", method.keys())
                # printSpecs(method)
                # print("\n-->", method['method'].keys())
                # dict_keys(['fuzzy', 'list_matching', 'method', 'sim_method', 'sources', 'targets'])
                # --> dict_keys(['config', 'name'])
                # --> dict_keys(['list_matching', 'method_config', 'method_name', 'method_sim_config', 'method_sim_name', 'method_sim_normalized', 'sources', 't_conorm', 'targets', 'threshold'])
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

                        # print("\nPROPERTIES--->", dataset_specs[e_sel_id][
                        #     'collections'][e_type]['properties'])

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

                                    # print("--->", property_list_1, e_sel_id, e_type)
                                    # KeyError: 'roar_Doop'
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
                                # print('')

                            # update
                            choices['short_properties'] = short_uris
                            choices['long_properties'] = long_uris

        except KeyError as err:
            print(ERROR(page='SpecsBuilder', function='method_conditions',
                        location='Something went wrong with the method condition.\n'
                                 '\t\tFor loop with variable [method_conditions_list]',
                        message=err.__str__()))
            exit()


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

    center, line = 70, 70
    printTime()
    clusters = {}
    prefixes = {}
    data_collected = {}
    dataset_specs = None

    home = "https://recon.diginfra.net"

    # LINKSET URL
    linkset_url = F"{home}/job/{job}"

    # LINKSET STATS URIS
    stats_url_1 = F"{home}/job/{job}/clusterings"
    stats_url2 = F"{home}/job/{job}/linksets"
    stats_url_3 = F"{home}/job/{job}/links_totals/linkset/{linksetId}"

    # AVAILABLE DATASETS URI
    dataset_url = F"{home}/datasets?endpoint=https://repository.goldenagents.org/v5/graphql"

    # CLUSTER URI
    clusters_uri = F"{home}/job/{job}/clusters/linkset/{linksetId}?"

    print(F"\n{'':>16}{'-' * line:^{center}}\n{'|':>16}{'BUILDING THE SPECIFICATION':^{center}}|"
          F"\n{'|':>16}{F'JOB IDENTIFIER : {job}':^{center}}|\n"
          F"{'|':>16}{F'LINKSET INDEX : {linksetId}':^{center}}|\n{'':>16}{'-' * line:^{center}}\n")

    # ###############################################################################
    # 1. COLLECTING THE AVAILABLE DATASETS                                          #
    # ###############################################################################
    if True:

        # 1.1 REQUEST ON DATASET INFO
        try:
            dataset_specs = requests.get(dataset_url).json()
            data_collected['datasets'] = deepcopy(dataset_specs)
            print("\t1. Datasets info collected")
        except Exception as err:
            print(
                ERROR(
                    page='SpecsBuilder', function='linksetSpecsDataItr',
                    location='1.1 REQUEST ON DATASET INFO',
                    message="PROBLEM WITH REQUESTING INFO ON DATASETS FROM TIMBUKTU"
                )
            )
            return

        # 1.2 REQUEST ON LINKSET INFO
        try:
            lst_specs = requests.get(linkset_url).json()
            data_collected['linkset'] = deepcopy(lst_specs)
            print("\t2. Linkset specification gathered")

            # GETTING THE ENTITY SELECTION OBJECT FROM THE lst_specs
            entity_type_selections = lst_specs['entity_type_selections']
            print("\t3. Entity type selection extracted")

            # RESET THE RIGHT lst_specs WITH THE ACTUAL SPECS
            try:
                found = False
                for counter, spec in enumerate(lst_specs['linkset_specs']):
                    if spec['id'] == linksetId:
                        found, lst_specs = True, spec
                        break

                if found is False:
                    print(F"\nTHE LINKSET WITH ID: [{linksetId}] COULD NOT BE FOUND")
                    return
                else:
                    print(F"\t4. Linkset {linksetId} is found.")

            except IndexError as err:
                print(F"\n-> THE LINKSET [{linksetId}] CAN NOT BE FOUND DUE TO INDEX OUT OF RANGE ERROR")
                return

            # 3. MISSING SETTINGS
            linkset_name = lst_specs['id']
            lst_specs["job_id"] = job
            lst_specs["linkType"] = {
                'prefix': 'owl',
                'namespace': LinkPredicates.owl.__str__(),
                'long': LinkPredicates.sameAs,
                'short': LinkPredicates.sameAs_tt,
            }
            lst_specs["creator"] = "AL IDRISSOU"
            lst_specs["publisher"] = "GoldenAgents"
            lst_specs['clusters'] = clusters

        except ValueError as err:
            print("\nTHE JOB REQUEST CAN N0T BE PLACED")
            print(
                ERROR(
                    page='SpecsBuilder',
                    function='linksetSpecsDataItr',
                    location='LINKSET URI try clause for collecting information on the linkset under scrutiny'
                ))
            # print(
            #     F"\n{'File':15} : SpecsBuilder.py\n"
            #     F"{'Function':15} : linksetSpecsDataItr\n"
            #     F"{'Whereabouts':15} : LINKSET URI try clause for collecting information on the linkset under scrutiny\n"
            #     F"{'Error Message':15} : {err.__str__()}")
            return

    # ###############################################################################
    # 2. COLLECTION INFO ON CLUSTERED LINKS                                         #
    # ###############################################################################
    if True:

        start = time()
        limit, offset = 200000, 0

        try:
            print("\t5. Collecting the clustering file.")
            while True:

                cluster_limit = F"\t{clusters_uri}with_properties=none&limit={limit}&offset={offset}&include_nodes=true"
                print(F"\t{cluster_limit}")
                clusters_data = requests.get(cluster_limit).json()

                print(F"\t\t--> Limit: {limit:.>10}    "
                      F"Offset: {offset:.>10}    "
                      F"Fetched: {len(clusters_data):.>}    "
                      F"So far: {timedelta(seconds=time() - start)}")

                if 'error' not in clusters_data:
                    for item in clusters_data:
                        # Adding a set is better but will not work in the
                        # need of a deterministic hash output for the name of the cluster
                        # item['item'] = list()
                        clusters[item['id']] = item
                    print("\t\tThe linkset has been clustered.")
                else:
                    clusters_data = {}
                    print("\t\tThe linkset has not been clustered.")

                offset = offset + limit
                if len(clusters_data) < limit:
                    break

        except Exception as err:
            print("\t\tThe linkset has not been clustered.")
            print(F"\t\tERROR:{clusters_uri}limit={limit}&offset={offset}")
            if err.__str__() != 'Expecting value: line 1 column 1 (char 0)':
                print(
                    F"\n{'File':15} : SpecsBuilder.py\n"
                    F"{'Function':15} : linksetSpecsDataItr\n"
                    F"{'Whereabouts':15} : First try clause for collecting information on cluster if available\n"
                    F"{'Error Message':15} : {err.__str__()}\n"
                    F"{traceback.print_exc()}")

    # 4. ENTITY SELECTIONS IN A DICTIONARY AS {ID: SLECTION OBJECT}
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
                # print(info['property'])

                for i, i_property in enumerate(info['property']):

                    # Odds numbers slots are container of a property name
                    if (i + 1) % 2 != 0:

                        # print("\t\t", i, entity_type, i_property)

                        # getting the uri of the current property
                        long_uri = dataset_specs[id]['collections'][entity_type]['properties'][i_property]['uri'] \
                            if i_property != 'uri' else i_property

                        # getting the short version of the current property
                        short_uri = dataset_specs[id][
                            'collections'][entity_type]['properties'][i_property]['shortenedUri'] \
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
    # 8. MERGING STATS                                                              #
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

    # ###############################################################################
    # VALIDATION STATS                                                              #
    # ###############################################################################
    try:
        stats_specs3 = requests.get(stats_url_3).json()
        if stats_specs3:
            stats_specs.update(stats_specs3)
    except Exception as err:

        print("\tTHE LINKS HAVE NOT YET BEEN VALIDATED.")
        if err.__str__() != 'Expecting value: line 1 column 1 (char 0)':
            print(
                F"\n{'File':15} : SpecsBuilder.py\n"
                F"{'Function':15} : linksetSpecsDataItr\n"
                F"{'Whereabouts':15} : VALIDATION STATS clause.\n"
                F"{'Error Message':15} : {err.__str__()}\n"
                F"{traceback.print_exc()}")

    # if found is False:
    #     print("THE LINKSET HAS NOT BEEN EXECUTED")

    # GETTING THE
    if "sources_count" in stats_specs and "targets_count" in stats_specs \
            and stats_specs["sources_count"] and stats_specs["targets_count"]:
        stats_specs['entities'] = stats_specs["sources_count"] + stats_specs["targets_count"]
    else:
        stats_specs['entities'] = 0

    # printSpecs(stats_specs)
    # exit()

    # MISSING PARAMETERS IN LINKSET
    # 1. creator
    # 2. publisher
    # 3. linkType

    #  MISSING PARAMETERS IN in METHODS
    #   1. threshold_operator
    #   2. threshold
    #   3. property IRI

    # printSpecs(stats_specs)
    # exit()

    validationset = {'creator': job, 'publisher': 'GoldenAgents', 'items': dict()}
    link_type = lst_specs['linkType']
    import ll.org.Export.Scripts.General as Grl
    test = list(lst_result)
    for count, link in enumerate(test):
        # print("====>", len(row), count, row)
        # if count > 0 and len(row) > 2:
        small = link['source'] if link['source'] < link['target'] else link['target']
        big = link['target'] if small == link['source'] else link['source']
        validationset['items'][Grl.deterministicHash(F"{small}{big}{link_type['short']}")] = {
            "Status": link['valid'], "Motivation": link['motivation']}

    specs = {'linksetStats': stats_specs, 'linksetSpecs': lst_specs, 'validations': [validationset]}

    if printSpec:
        printSpecs(specs, tab=1)
    # print(specs)

    # CREATE THE LINKSET FILE
    linkset_path, cluster_path, validation_paths = toLinkset(
        specs=specs, save_in=save_in, linkset_result=test, rdfStarReification=starReification, prefixes=prefixes)

    # VALIDATE THE FILE SYNTAX CORRECTNESS
    if starReification:
        validateRDFStar(linkset_path, removeIt=True)
        if cluster_path:
            validateRDFStar(cluster_path, removeIt=True)
        for validation in validation_paths:
            validateRDFStar(validation, removeIt=True)
    else:
        validateRDF(linkset_path)
        if cluster_path:
            validateRDF(cluster_path)
        for validation in validation_paths:
            validateRDF(validation)

    return linkset_path, data_collected


def lensSpecsDataItr(
        lensId: int, job: str, lens_result, save_in: str, starReification: bool, printSpec: bool = True):
    """
    :param lensId           : An integer parameter denoting the ID of the linkset to convert into an RDF documentation.
    :param job              : A string parameter indicating the IF of job from which to find the selected linkset.
    :param lens_result      : An iterator object materializing a countable number of matching results to iterate through.
    :param save_in          : A string parameter materialising the directory in which to save the converted RDF version of the result.
    :param starReification  : A boolean parameter specifying whether the conversion should proceed with respect to
                              (1) the standard reification -> starReification = False or
                              (2) the RDFStar convebtion -> starReification = True.
    :param printSpec        : A boolean parameter for displaying the specification object if needed.
    :return:
    """

    center, line = 70, 70
    printTime()
    clusters = {}
    prefixes = {}
    data_collected = {}
    found = False
    lens_id = None
    dataset_specs = None
    job_specs = None
    lens_specs = None
    stats_specs = dict()
    entity_type_selections = None

    home = "https://recon.diginfra.net"

    # ###############################################################################
    # 1. FETCH THE LIST OF JOBS                                                     #
    # ###############################################################################
    try:
        # JOBS: dict_keys([
        #   'created_at',
        #   'entity_type_selections',
        #   'job_description',
        #   'job_id',
        #   'job_link',
        #   'job_title',
        #   'lens_specs',
        #   'linkset_specs',
        #   'updated_at',
        #   'views'])

        job_specs = requests.get(F"{home}/job/{job}").json()
        data_collected['lens'] = deepcopy(job_specs)
        print("\t1. Fetching the list of jobs.")

    except ValueError as err:
        print("\nTHE JOB REQUEST CAN N0T BE PLACED")
        print(
            ERROR(
                page='SpecsBuilder',
                function='lensSpecsDataItr',
                location='FETCH THE LIST OF JOBS',
                message=F'Fetching the list of jobs run under the job id: {job}'
            ))

    # ###############################################################################
    # 2. EXTRACT THE ENTITY SELECTION OBJECT FROM THE LIST OF JOB OBJECT            #
    # ###############################################################################
    if job_specs:
        entity_type_selections = job_specs['entity_type_selections']
        print("\t2. Extracting the entity-type selections from the list of jobs.")

    # ###############################################################################
    # 3. FETCH THE RIGHT LENS SPECS FROM THE LIST OF JOBS                           #
    # ###############################################################################
    try:
        print("\t3. Extracting the lens under scrutiny.")
        for counter, spec in enumerate(job_specs['lens_specs']):

            if spec['id'] == int(lensId):
                found, lens_specs = True, spec
                break

        if found is False:
            print(F"\nTHE LENS WITH ID:{lensId} from the JOB:{job} COULD NOT BE FOUND")
            return

        else:
            # 3. MISSING SETTINGS
            lens_id = lens_specs['id']
            lens_specs["job_id"] = job
            lens_specs["linkType"] = {
                'prefix': 'owl',
                'namespace': LinkPredicates.owl.__str__(),
                'long': LinkPredicates.sameAs,
                'short': LinkPredicates.sameAs_tt,
            }
            lens_specs["creator"] = "AL IDRISSOU"
            lens_specs["publisher"] = "GoldenAgents"

    except IndexError as err:
        print(F"\n-> THE LINKSET [{lensId}] CAN NOT BE FOUND DUE TO INDEX OUT OF RANGE ERROR")
        return

    # ###############################################################################
    # CLUSTER STATS                                                                 #
    # ###############################################################################
    print("\t4. Collecting cluster stats.")
    cluster_stats_url = stats_url_1 = F"{home}/job/{job}/clusterings"
    cluster_stats_specs = requests.get(cluster_stats_url).json()
    data_collected['cluster_stats'] = deepcopy(cluster_stats_specs)
    for data in cluster_stats_specs:
        if data['spec_id'] == lens_id:
            stats_specs = data
            break

    # ###############################################################################
    # LINK STATS                                                                    #
    # ###############################################################################
    print("\t5. Collecting link stats.")
    try:
        link_stats_url = F"{home}/job/{job}/lenses"
        link_stats_specs = requests.get(link_stats_url).json()
        data_collected['linkset_stats'] = deepcopy(link_stats_url)
        for data in link_stats_specs:
            if data['spec_id'] == lens_id:
                stats_specs.update(data)
                break

        # IF THE LENS HAS NO STATS YET, SET THE stats_specs OBJECT
        if isinstance(stats_specs, list):
            print("\t\tTHERE IS NOT CLUSTERING STATS")
    except Exception as err:
        print("\t\tTHERE IS NOT CLUSTERING STATS")
        # ERROR(page='SpecsBuilder.py', function="lensSpecsDataItr", location="L1175", message='THERE IS NOT CLUSTERING STATS')

    # ###############################################################################
    # VALIDATION STATS                                                              #
    # ###############################################################################
    print("\t6. Collecting validations stats.")
    try:
        val_stats_url = F"{home}/job/{job}/links_totals/lens/{lensId}"
        val_stats_specs = requests.get(val_stats_url).json()
        # printSpecs(val_stats_specs)
        if val_stats_specs:
            stats_specs.update(val_stats_specs)

    except Exception as err:

        print("\t\tTHE LINKS HAVE NOT YET BEEN VALIDATED.")
        if err.__str__() != 'Expecting value: line 1 column 1 (char 0)':
            print(
                F"\n{'File':15} : SpecsBuilder.py\n"
                F"{'Function':15} : lensSpecsDataItr\n"
                F"{'Whereabouts':15} : VALIDATION STATS clause.\n"
                F"{'Error Message':15} : {err.__str__()}\n"
                F"{traceback.print_exc()}")

    # ###############################################################################
    # 2. COLLECTION INFO ON CLUSTERED LINKS                                         #
    # ###############################################################################
    if True:

        print("\t7. Collecting the clustering files.")
        start = time()
        limit, offset = 200000, 0

        try:

            clusters_uri = F"{home}/job/{job}/clusters/lens/{lens_id}?"
            while True:

                cluster_limit = F"\t{clusters_uri}with_properties=none&limit={limit}&offset={offset}&include_nodes=true"
                print(F"\t{cluster_limit}")
                clusters_data = requests.get(cluster_limit).json()

                print(F"\t\t--> Limit: {limit:.>10}    "
                      F"Offset: {offset:.>10}    "
                      F"Fetched: {len(clusters_data):.>}    "
                      F"So far: {timedelta(seconds=time() - start)}")

                if 'error' not in clusters_data:
                    for item in clusters_data:
                        # Adding a set is better but will not work in the
                        # need of a deterministic hash output for the name of the cluster
                        # item['item'] = list()
                        clusters[item['id']] = item
                    print("\t\t--> THE LENS HAS BEEN CLUSTERED.")
                else:
                    clusters_data = {}
                    print("\t\t--> THE LENS HAS NOT BEEN CLUSTERED.")

                offset = offset + limit
                if len(clusters_data) < limit:
                    break

        except Exception as err:
            print(F"\t\tERROR:{clusters_uri}limit={limit}&offset={offset}")
            print("\t\tThe Lens has not been clustered.")
            if err.__str__() != 'Expecting value: line 1 column 1 (char 0)':
                print(
                    F"\n{'File':15} : SpecsBuilder.py\n"
                    F"{'Function':15} : linksetSpecsDataItr\n"
                    F"{'Whereabouts':15} : First try clause for collecting information on cluster if available\n"
                    F"{'Error Message':15} : {err.__str__()}\n"
                    F"{traceback.print_exc()}")

    # ==============================================================================
    print("\t8. Constructing the validation set object.")
    validationset = {'creator': job, 'publisher': 'GoldenAgents', 'items': dict()}
    link_type = lens_specs['linkType']

    test = list(lens_result) if lens_result else []
    if len(test) > 0 and test[0] != 'error':
        print("\t\t--> THE LENS HAS A VALIDATION SET.")
        for count, link in enumerate(test):
            small = link['source'] if link['source'] < link['target'] else link['target']
            big = link['target'] if small == link['source'] else link['source']
            validationset['items'][Grl.deterministicHash(F"{small}{big}{link_type}")] = {
                "Status": link['valid'], "Motivation": link['motivation']}
    else:
        print("\t\t--> THERE IS NO VALIDATION SET")

    specs = {'lensStats': stats_specs, 'lensSpecs': lens_specs, 'clusters': clusters, 'validations': [validationset]}

    if printSpec:
        printSpecs(specs, tab=1)
    # print(specs)

    print("\t9. Creating the lens annotation.")
    # CREATE THE LINKSET FILE
    lens_path, cluster_path, validation_paths = toLens(
        specs, save_in=save_in, linkset_result=test,
        rdfStarReification=starReification, prefixes=prefixes)

    # VALIDATE THE FILE SYNTAX CORRECTNESS
    if starReification:
        validateRDFStar(lens_path, removeIt=True)
        if cluster_path:
            validateRDFStar(cluster_path, removeIt=True)
        for validation in validation_paths:
            validateRDFStar(validation, removeIt=True)
    else:
        validateRDF(lens_path)
        if cluster_path:
            validateRDF(cluster_path)
        for validation in validation_paths:
            validateRDF(validation)

    return cluster_path, data_collected


