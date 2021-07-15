# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   CREATION OF AN ANNOTATED LINKSET USING STANDARD REIFICATION FORMAT OR RDFSTAR                         #
#                                                                                                         #
# #########################################################################################################

from os.path import join
from time import time
from datetime import timedelta
from rdflib import URIRef, Literal, Graph
import ll.org.Export.Scripts.Variables as Vars
from collections import defaultdict
import ll.org.Export.Scripts.General as Grl
from ll.org.Export.Scripts.Specs2Metadata import \
    uri2ttl, reconstructTurtle, preVal, linksetNamespaces, subHeader,\
    unboxingLinksetSpecs as getMetadata,  clearBuffer, unboxingLensSpecs as getLensMetadata
from ll.org.Export.Scripts.VoidPlus import VoidPlus
from ll.org.Export.Scripts.Resources import Resource as Rsc
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from ll.org.Export.Scripts.Algotithms import Algorithm
from io import StringIO as Buffer
from ll.org.Export.Scripts.Validation import Validate
MANAGER = Graph().namespace_manager

validate = Validate()

# FORMATTING SPACE
space = "    "

# MAPPING OF LINKSET HEADERS
CSV_HEADERS = {
    "Valid": VoidPlus.has_validation_ttl,
    "Max Strength": VoidPlus.strength_ttl,
    "Strength": VoidPlus.strength_ttl,
    "Cluster ID": VoidPlus.cluster_ID_ttl,
    "Source Intermediates": VoidPlus.hasSourceEvidence_ttl,
    "Target Intermediates": VoidPlus.hasTargetEvidence_ttl
}
JSON_HEADERS = {
    "valid": VoidPlus.has_validation_ttl,
    "similarity": VoidPlus.strength_ttl,
    "cluster_id": VoidPlus.cluster_ID_ttl,
    "source_intermediates": VoidPlus.hasSourceEvidence_ttl,
    "target_intermediates": VoidPlus.hasTargetEvidence_ttl
}


# Shared prefixes to remove from the set of automated prefixes
SHARED = [
    'http://www.w3.org/2000/01/rdf-schema#', 'http://www.w3.org/2000/01/rdf-schema#', 'http://www.w3.org/2002/07/owl#',
    'http://rdfs.org/ns/void#', 'http://purl.org/dc/terms/', 'http://www.w3.org/ns/formats/',
    'http://purl.org/ontology/similarity/', 'http://creativecommons.org/ns#', 'http://www.w3.org/2001/XMLSchema#']


def header(message, lines=2):
    liner = "\n"
    return F"{liner * lines}{'#' * 80:^110}\n{' ' * 15}#{message:^78}#\n{'#' * 80:^110}{liner * (lines - 1)}"


def rdfStarLinkGenerator_fromCSV(link_predicate: str, result_batch, offset=0):

    errors = ""
    vars_size = 0
    buffer = Buffer()
    vars_dic = defaultdict(int)

    for count, row in enumerate(result_batch):

        if True:

            # THE FIRST LINE IS ASSUMED TO BE THE HEADER
            if count > 0 and len(row) > 1:

                # GET THE SOURCE AND TARGET URIS
                src_data, trg_data = row[0], row[1]

                # GENERATION OF THE LINK
                if src_data and trg_data:

                    # The RDFStar subject
                    buffer.write(F"{space}### LINK Nbr: {count + offset}\n"
                                 F"{space}<<<{src_data}>    {link_predicate}    <{trg_data}>>>\n"
                                 if len(vars_dic) > 0
                                 else F"{space}<{src_data}>    {link_predicate}    <{trg_data}> .\n")

                    # ANNOTATION OF THE LINK
                    # ll_val:has-link-validation               "not_validated" .
                    for counter, (predicate, index) in enumerate(vars_dic.items()):
                        end = ".\n" if counter == vars_size - 1 else ";"

                        # APPENDING THE CLUSTER SIZE
                        # if clusters and predicate == VoidPlus.cluster_ID_ttl and int(row[index]) in clusters:
                        #     buffer.write(F"{space * 2}{VoidPlus.cluster_size_ttl:{Vars.PRED_SIZE}}"
                        #                  F"{Literal(clusters[int(row[index])]['size']).n3(MANAGER)} ;\n")

                        # APPENDING THE VALIDATION FLAG
                        # if predicate == VoidPlus.has_validation_flag_ttl:
                        #     triple_value = validate.get_resource[row[index]]

                        # APPENDING THE VALIDATION FLAG RESOURCE
                        if predicate == VoidPlus.has_validation_ttl:
                            small = src_data if src_data < trg_data else trg_data
                            big = trg_data if small == src_data else src_data
                            key = Grl.deterministicHash(F"{small}{big}{link_predicate}")
                            triple_value = Rsc.validation_ttl(key)
                            # buffer.write(F"{space * 2}{VoidPlus.has_validation_ttl:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                        # APPENDING THE CLUSTER ID AS A RESOURCE
                        elif predicate == VoidPlus.cluster_ID_ttl:
                            cluster_id = int(row[index])
                            triple_value = Rsc.cluster_ttl(cluster_id)
                            # clusters[cluster_id]['item'].extend([src_data, trg_data])

                        # APPENDING ANYTHING ELSE
                        else:
                            triple_value = Literal(round(float(row[index]), 5)).n3(MANAGER) \
                                if Grl.isDecimalLike(row[index]) \
                                else Literal(row[index]).n3(MANAGER)

                        buffer.write(F"{space * 2}{predicate:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                        # buffer.write(F"{space * 2}{predicate:{Vars.PRED_SIZE}}"
                        #              F"{validate.get_resource[row[index]] if not Grl.isDecimalLike(row[index]) else round(float(row[index]), 5)} {end}\n")

                    yield buffer.getvalue()
                    clearBuffer(buffer)

            else:

                # THE CSV HEADER
                # Star at position
                for column in range(2, len(row)):

                    if row[column] in CSV_HEADERS:
                        vars_dic[CSV_HEADERS[row[column]]] = column
                        vars_size += 1

        # except Exception as err:
        #     errors += F">>>> [ERROR FROM AnnotatedLinkset_Generic/rdfStarLinkGenerator] {row}, {err}"


def standardLinkGenerator_fromCSV(link_predicate: str, result_batch, offset=0):

    """
    :param offset           : an integer to increment the counting of tghe links
    :param link_predicate   : a turtle representation of a URI (e.i: owl:sameAs).
    :param result_batch     : an iterable object with link results.
    :param clusters         : a dictionary proving the size of the clusters links.
    :return                 : Yields a string as set of triples.
    """
    errors = ""
    vars_size = 0
    buffer = Buffer()
    vars_dic = defaultdict(int)
    # print(clusters)
    for count, row in enumerate(result_batch):

        try:

            # THE FIRST LINE IS ASSUMED TO BE THE HEADER
            if count > 0 and len(row) > 1:

                # GET THE SOURCE AND TARGET URIS
                src_data, trg_data = row[0], row[1]

                # GENERATION OF THE LINK
                if src_data and trg_data:

                    # The RDFStar subject
                    buffer.write(F"\n{space}### LINK Nbr: {count + offset}\n"
                                 F"{space}<{src_data}>    {Rsc.ga_resource_ttl(link_predicate)}    <{trg_data}> .\n")

                    # STANDARD REIFICATION
                    link = F"{space}{src_data}    {Rsc.ga_resource_ttl(link_predicate)}    {trg_data} .\n"
                    code = Rsc.ga_resource_ttl(F"Reification-{Grl.deterministicHash(link)}")
                    buffer.write(F"\n{space}### STANDARD REIFICATION Nbr: {count}" 
                                 F"\n{space}{code}\n" 
                                 F"{space}{preVal('a', 'rdf:Statement')}" 
                                 F"{space}{preVal('rdf:predicate', link_predicate)}" 
                                 F"{space}{preVal('rdf:subject', F'<{src_data}>')}" 
                                 F"{space}{preVal('rdf:object', F'<{trg_data}>')}")

                    # ANNOTATION OF THE LINK USING THE REIFIED CODE
                    for counter, (predicate, index) in enumerate(vars_dic.items()):
                        end = ".\n" if counter == vars_size - 1 else ";"

                        # APPENDING THE CLUSTER SIZE
                        # if clusters and predicate == VoidPlus.cluster_ID_ttl and int(row[index]) in clusters:
                        #     buffer.write(F"{space * 2}{VoidPlus.cluster_size_ttl:{Vars.PRED_SIZE}}"
                        #                  F"{Literal(clusters[int(row[index])]['size']).n3(MANAGER)} ;\n")

                        # APPENDING THE VALIDATION FLAG
                        # if predicate == VoidPlus.has_validation_flag_ttl:
                        #     triple_value = validate.get_resource[row[index]]

                        # APPENDING THE VALIDATION FLAG RESOURCE
                        if predicate == VoidPlus.has_validation_ttl:
                            small = src_data if src_data < trg_data else trg_data
                            big = trg_data if small == src_data else src_data
                            key = Grl.deterministicHash(F"{small}{big}{link_predicate}")
                            triple_value = Rsc.validation_ttl(key)
                            # buffer.write(F"{space * 2}{VoidPlus.has_validation_ttl:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                        # APPENDING THE CLUSTER ID AS A RESOURCE
                        elif predicate == VoidPlus.cluster_ID_ttl:
                            cluster_id = int(row[index])
                            triple_value = Rsc.cluster_ttl(cluster_id)
                            # clusters[cluster_id]['item'].extend([src_data, trg_data])

                        # APPENDING ANYTHING ELSE
                        else:
                            triple_value = Literal(round(float(row[index]), 5)).n3(MANAGER) \
                                if Grl.isDecimalLike(row[index]) \
                                else Literal(row[index]).n3(MANAGER)

                        buffer.write(F"{space * 2}{predicate:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                    yield buffer.getvalue()
                    clearBuffer(buffer)

            else:

                # THE CSV HEADER
                # Star at position
                # MAPPING THE CSV HEADERS
                row_header = row
                # print(header, len(header))

                for column in range(2, len(row_header)):

                    if row[column] in CSV_HEADERS:
                        vars_dic[CSV_HEADERS[row_header[column]]] = column
                        # print('--->', CSV_HEADERS[header[column]], header[column], column)
                        vars_size += 1

        except Exception as err:
            errors += F">>>> [ERROR FROM AnnotatedLinkset_Generic/standardLinkGenerator] \n\t{row} \n\t{err}"
            print(errors)


def rdfStarLinkGenerator(mappings: dict, link_predicate: str, result_batch, offset=0):

    errors = ""
    buffer = Buffer()

    def ns_modification(uri):

        for ns in mappings:
            if uri.startswith(ns):
                uri = uri.replace(ns, F"{mappings[ns]}:")
                break

        if uri.__contains__("://"):
            uri = F"<{uri}>"

        return uri

    for count, link in enumerate(result_batch):

        try:

            # GET THE SOURCE AND TARGET URIS
            src_data, trg_data = ns_modification(link['source']), ns_modification(link['target'])

            # GENERATION OF THE LINK
            if src_data and trg_data:

                # The RDFStar subject
                buffer.write(F"{space}### LINK Nbr: {count + offset}\n"
                             F"{space}<<{src_data}    {link_predicate}    {trg_data}>>\n")

                # ANNOTATION OF THE LINK
                # ll_val:has-link-validation               "not_validated" .
                for counter, (feature, value) in enumerate(link.items()):
                    end = ".\n" if counter == len(link) - 1 else ";"

                    current_property = JSON_HEADERS.get(feature, None)

                    if current_property:

                        # APPENDING THE VALIDATION FLAG RESOURCE
                        if current_property == VoidPlus.has_validation_ttl:
                            small = link['source'] if link['source'] < link['target'] else link['target']
                            big = link['target'] if small == link['source'] else link['source']
                            key = Grl.deterministicHash(F"{small}{big}{link_predicate}")
                            triple_value = Rsc.validation_ttl(key) if key is not None else key

                        # APPENDING THE CLUSTER ID AS A RESOURCE
                        elif current_property == VoidPlus.cluster_ID_ttl:
                            triple_value = Rsc.cluster_ttl(int(value)) if value is not None else value

                        # APPENDING ANYTHING ELSE
                        else:
                            if value is not None:
                                triple_value = Literal(round(float(value), 5)).n3(MANAGER) \
                                    if Grl.isDecimalLike(value) \
                                    else Literal(value).n3(MANAGER)
                            else:
                                triple_value = value

                        if triple_value is not None:
                            buffer.write(F"{space * 2}{current_property:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                yield buffer.getvalue()
                clearBuffer(buffer)

        except Exception as err:
            errors += F">>>> [ERROR FROM AnnotatedLinkset_Generic/rdfStarLinkGenerator] {link}, {err}"


def standardLinkGenerator(mappings: dict, link_predicate: str, result_batch, offset=0):

    """
    :param mappings         : dictionary of namespaces as keys and prefixes ad values.
    :param offset           : an integer to increment the counting of tghe links
    :param link_predicate   : a turtle representation of a URI (e.i: owl:sameAs).
    :param result_batch     : an iterable object with link results.
    :param clusters         : a dictionary proving the size of the clusters links.
    :return                 : Yields a string as set of triples.
    """

    buffer = Buffer()
    errors = ""

    def ns_modification(uri):

        for ns in mappings:
            if uri.startswith(ns):
                uri = uri.replace(ns, F"{mappings[ns]}:")
                break

        if uri.__contains__("://"):
            uri = F"<{uri}>"

        return uri

    for count, link in enumerate(result_batch):

        if True:

            # GET THE SOURCE AND TARGET URIS
            # src_data, trg_data = link['source'], link['target']
            src_data, trg_data = ns_modification(link['source']), ns_modification(link['target'])

            # GENERATION OF THE LINK
            if src_data and trg_data:

                # The RDFStar subject
                buffer.write(F"\n{space}### LINK Nbr: {count + offset}\n"
                             F"{space}{src_data}    {Rsc.ga_resource_ttl(link_predicate)}    {trg_data} .\n")

                # STANDARD REIFICATION
                reification = F"{space}{src_data}    {Rsc.ga_resource_ttl(link_predicate)}    {trg_data} .\n"
                code = Rsc.ga_resource_ttl(F"Reification-{Grl.deterministicHash(reification)}")
                buffer.write(F"\n{space}### STANDARD REIFICATION Nbr: {count}" 
                             F"\n{space}{code}\n" 
                             F"{space}{preVal('a', 'rdf:Statement')}" 
                             F"{space}{preVal('rdf:predicate', link_predicate)}" 
                             F"{space}{preVal('rdf:subject', F'{src_data}')}" 
                             F"{space}{preVal('rdf:object', F'{trg_data}')}")

                # ANNOTATION OF THE LINK USING THE REIFIED CODE
                for counter, (feature, value) in enumerate(link.items()):

                    end = ".\n" if counter == len(link) - 1 else ";"

                    cur_predicate = JSON_HEADERS.get(feature, None)

                    if cur_predicate:

                        # APPENDING THE VALIDATION FLAG RESOURCE
                        if cur_predicate == VoidPlus.has_validation_ttl:
                            small = link['source'] if link['source'] < link['target'] else link['target']
                            big = link['target'] if small == link['source'] else link['source']
                            # print(F"{small} {big} {link_predicate}")
                            key = Grl.deterministicHash(F"{small}{big}{link_predicate}")
                            triple_value = Rsc.validation_ttl(key) if key is not None else key

                        # APPENDING THE CLUSTER ID AS A RESOURCE
                        elif cur_predicate == VoidPlus.cluster_ID_ttl:
                            triple_value = Rsc.cluster_ttl(int(value)) if value is not None else value

                        # APPENDING ANYTHING ELSE
                        else:
                            if value is not None:
                                triple_value = Literal(round(float(value), 5)).n3(MANAGER) \
                                    if Grl.isDecimalLike(value) \
                                    else Literal(value).n3(MANAGER)
                            else:
                                triple_value = None

                        if triple_value is not None:
                            buffer.write(F"{space * 2}{cur_predicate:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                yield buffer.getvalue()
                clearBuffer(buffer)

        # except Exception as err:
        #     errors += F">>>> [ERROR FROM AnnotatedLinkset_Generic/standardLinkGenerator] \n\t{link} \n\t{err}"
            # print(errors)


def standardLinkGenerator2(link_predicate: str, result_batch, namespace, clusters=None, offset=0):

    """
    :param offset           : an integer to increment the counting of tghe links
    :param link_predicate   : a turtle representation of a URI (e.i: owl:sameAs).
    :param namespace        : a dictionary for namespace
    :param result_batch     : an iterable object with link results.
    :param clusters         : a dictionary proving the size of the clusters links.
    :return                 : Yields a string as set of triples.
    """
    errors = ""
    vars_size = 0
    buffer = Buffer()
    vars_dic = defaultdict(int)

    for count, row in enumerate(result_batch):

        try:

            # THE FIRST LINE IS ASSUMED TO BE THE HEADER
            if count > 0 and len(row) > 1:

                # GET THE SOURCE AND TARGET URIS
                src_data, trg_data, predicate = uri2ttl(row[0], namespace)["short"], \
                                                uri2ttl(row[1], namespace)["short"], \
                                                uri2ttl(link_predicate, namespace)["short"]
                print(src_data)

                # GENERATION OF THE LINK
                if src_data and trg_data:

                    # The RDFStar subject
                    buffer.write(F"\n{space}### LINK Nbr: {count + offset}\n"
                                 F"{space}{src_data}    {Rsc.ga_resource_ttl(predicate)}    {trg_data} .\n")

                    # STANDARD REIFICATION
                    link = F"{space}{src_data}    {Rsc.ga_resource_ttl(predicate)}    {trg_data} .\n"
                    code = Rsc.ga_resource_ttl(F"Reification-{Grl.deterministicHash(link)}")
                    buffer.write(F"\n{space}### STANDARD REIFICATION Nbr: {count}" 
                                 F"\n{space}{code}\n" 
                                 F"{space}{preVal('a', 'rdf:Statement')}" 
                                 F"{space}{preVal('rdf:predicate', predicate)}" 
                                 F"{space}{preVal('rdf:subject', F'{src_data}')}" 
                                 F"{space}{preVal('rdf:object', F'{trg_data}')}")

                    # ANNOTATION OF THE LINK USING THE REIFIED CODE
                    for counter, (predicate, index) in enumerate(vars_dic.items()):
                        end = ".\n" if counter == vars_size - 1 else ";"

                        # APPENDING THE CLUSTER SIZE
                        if clusters and predicate == VoidPlus.cluster_ID_ttl and row[index] in clusters:
                            buffer.write(F"{space * 2}{VoidPlus.cluster_size_ttl:{Vars.PRED_SIZE}}"
                                         F"{Literal(clusters[row[index]]).n3(MANAGER)} ;\n")

                        # APPENDING THE VALIDATION FLAG
                        if predicate == VoidPlus.has_validation_status_ttl:
                            triple_value = validate.get_resource[row[index]]

                        # APPENDING DING ANYTHING ELSE
                        else:
                            triple_value = Literal(round(float(row[index]), 5)).n3(MANAGER) \
                                if Grl.isDecimalLike(row[index]) \
                                else Literal(row[index]).n3(MANAGER)

                        buffer.write(F"{space * 2}{predicate:{Vars.PRED_SIZE}}{triple_value} {end}\n")

                    yield buffer.getvalue()
                    clearBuffer(buffer)

            else:

                # THE CSV HEADER
                # Star at position
                # MAPPING THE CSV HEADERS
                for column in range(2, len(row)):
                    header = row
                    if row[column] in CSV_HEADERS:
                        vars_dic[CSV_HEADERS[row[column]]] = column
                        vars_size += 1

        except Exception as err:
            errors += F">>>> [ERROR FROM csv_2_linkset] {row}, {err}"
            print(errors)


def clusterGraphGenerator(clusters, stats, auto_prefixes, linksetGraph, linkset_id):

    node_count = 0
    validated = 0
    clusterset_graph = F"{Rsc.clusterset_ttl(Grl.deterministicHash(clusters))}-{linkset_id}"

    if clusters:

        # ADDING THE CLUSTER NAMESPACE
        # auto_prefixes[Rsc.clusterset] = "clusterset"

        writer = Buffer()
        predicate_map = {
            "extended": VoidPlus.extended_ttl,
            "id": VoidPlus.id_ttl,
            "links": VoidPlus.links_ttl,
            "reconciled": VoidPlus.reconciled_ttl,
            "size": VoidPlus.size_ttl,
            "accepted": VoidPlus.accepted_ttl,
            "rejected": VoidPlus.rejected_ttl,
            "not_sure": VoidPlus.uncertain_ttl,
            "mixed": VoidPlus.contradictions_ttl,
            "not_validated": VoidPlus.unchecked_ttl
        }

    # APPENDING ALL NAMESPACES
    writer.write(
        linksetNamespaces(
            auto_prefixes, isClustered=clusters and len(clusters) > 0,
            isValidated=(Vars.notValidated in stats and stats[Vars.notValidated] < stats[Vars.triples]) is True
        ))

    # THE CLUSTER METADATA
    writer.write(F'{header("RESOURCE PARTITIONING METADATA")}\n\n')
    writer.write(F"{clusterset_graph}\n")
    writer.write(preVal('a', VoidPlus.Clusterset_ttl))
    writer.write(preVal(VoidPlus.clusters_ttl, Literal(len(clusters)).n3(MANAGER)))
    writer.write(preVal(Sns.VoID.entities_ttl, "###NodeCounts"))
    writer.write(preVal(VoidPlus.validations_ttl, "###VALIDATED"))

    writer.write(preVal(VoidPlus.largestNodeCount_ttl, Rsc.literal_resource(stats['largest_size'])))
    writer.write(preVal(VoidPlus.largestLinkCount_ttl, Rsc.literal_resource(stats['largest_count'])))

    writer.write(preVal(VoidPlus.hasTarget_ttl, linksetGraph))
    writer.write(preVal(VoidPlus.method_ttl, Algorithm.simple_clustering_ttl))
    writer.write(preVal(Sns.DCterms.created_ttl, Grl.getXSDTimestamp(), end=True))

    # DESCRIPTION OF THE CLUSTERING ALGORITHM
    writer.write(F'\n\n{Algorithm.simple_clustering_ttl}\n')
    writer.write(preVal('a', VoidPlus.ClusteringAlgorithm_ttl))
    writer.write(preVal(Sns.DCterms.description_ttl, Literal(Algorithm.simple_clustering_short_description).n3(MANAGER)))
    writer.write(preVal(Sns.RDFS.seeAlso_ttl, Rsc.ga_resource_ttl("https://doi.org/10.3233/SW-200410"), end=True))

    # THE PARTITION OF CO-REFERENT MATCHED RESOURCES
    writer.write(F'{header("ANNOTATED CO-REFERENT RESOURCES")}\n\n')
    writer.write(F"{clusterset_graph}\n{{\n")
    for cid, cluster_data in clusters.items():

        temp = Buffer()

        # A CLUSTER RESOURCE
        writer.write(F"\n\t{Rsc.cluster_ttl(cid)}\n")
        writer.write(preVal('a', VoidPlus.Cluster_ttl, position=2))

        for feature, value in cluster_data.items():

            # CLUSTERED RESOURCES
            if feature == 'nodes':
                if value:
                    nodes = set(value)
                    node_count += len(nodes)
                    temp.write(
                        preVal(
                            VoidPlus.hasItem_ttl,
                            F" ,\n{space*2}{' ' * Vars.PRED_SIZE}".join(Rsc.ga_resource_ttl(elt) for elt in nodes),
                            position=2
                        )
                    )
            # VALIDATION FLAGS
            elif feature == "links":
                if value and value['not_validated'] == 0:
                    validated += 1
                for flag, integer in value.items():
                    temp.write(
                        preVal(
                            predicate_map[flag],
                            Literal(integer).n3(MANAGER),
                            position=2
                        )
                    )

            elif feature in ["values"]:
                pass

            # ABOUT THE CLUSTER
            else:
                temp.write(preVal(predicate_map[feature], Literal(value).n3(MANAGER), position=2))

        writer.write(F"{temp.getvalue()[:-2]}.\n")

    # print(triples.getvalue())
    result = writer.getvalue().replace('###NodeCounts', Literal(node_count).n3(MANAGER))
    return F"{result.replace('###VALIDATED', Literal(validated).n3(MANAGER))}}}"


def validationGraphGenerator(validationset, linksetStats, auto_prefixes, setGraph, set_id, isLinkset: bool):

    # THE LAST STATUS MUST ALWAYS HAVE A VALUE DO THAT IT DETERMINES THE LAST TRIPLE
    predicate_map = {
        "Motivation": VoidPlus.motivation_ttl,
        "Status": VoidPlus.has_validation_status_ttl
    }

    if isLinkset is False:
        auto_prefixes[Rsc.lens] = "lens"

    if validationset:

        validationset_graph = F"{Rsc.validationset_ttl(Grl.deterministicHash(validationset))}-{set_id}"
        writer = Buffer()

        # ADDING THE CLUSTER NAMESPACE
        # auto_prefixes[Rsc.validationset] = "validationset"

        # APPENDING ALL NAMESPACES
        writer.write(
            linksetNamespaces(
                auto_prefixes,
                # isValidated=validationset and len(validationset['items']) > 0,
                isValidated=True,
                isClustered=Vars.clusters in linksetStats and linksetStats[Vars.clusters] > 0
            ))

        # VALIDATION METADATA
        writer.write(F'{header("LINK VALIDATION METADATA")}\n\n')
        writer.write(F"{validationset_graph}\n")
        writer.write(preVal('a', VoidPlus.Validationset_ttl))
        writer.write(preVal(VoidPlus.hasTarget_ttl, setGraph))
        if "creator" in validationset and len(validationset["creator"].strip()) > 0:
            writer.write(preVal(Sns.DCterms.creator_ttl, Literal(validationset["creator"]).n3()))
        if "publisher" in validationset and len(validationset["publisher"].strip()) > 0:
            writer.write(preVal(Sns.DCterms.publisher_ttl, Literal(validationset["publisher"]).n3()))
        writer.write(preVal(Sns.DCterms.created_ttl, Grl.getXSDTimestamp()))

        # VALIDATION STATS
        # THE TOTAL AMOUNT OF LINKS ACCEPTED
        writer.write(F"\n{space}### VOID+ VALIDATION STATS\n")
        if Vars.accepted in linksetStats and linksetStats[Vars.accepted] > -1:
            writer.write(preVal(VoidPlus.accepted_ttl, Rsc.literal_resource(linksetStats[Vars.accepted])))

        # THE TOTAL AMOUNT OF LINKS REJECTED
        if Vars.rejected in linksetStats and linksetStats[Vars.rejected] > -1:
            writer.write(preVal(VoidPlus.rejected_ttl, Rsc.literal_resource(linksetStats[Vars.rejected])))

        # THE TOTAL AMOUNT OF LINKS WITH AN UNCERTAIN VALIDATION FLAG
        if Vars.not_sure in linksetStats and linksetStats[Vars.not_sure] > -1:
            writer.write(preVal(VoidPlus.uncertain_ttl, Rsc.literal_resource(linksetStats[Vars.not_sure])))

        # THE TOTAL AMOUNT OF LINKS NOT VALIDATED
        if Vars.notValidated in linksetStats and linksetStats[Vars.notValidated] > -1:
            writer.write(
                preVal(VoidPlus.unchecked_ttl, Rsc.literal_resource(linksetStats[Vars.notValidated])))

        writer.write("\n")
        writer.write(preVal(Sns.DCterms.description_ttl, Rsc.literal_resource(validate.generic_desc), end=True))

        # VALIDATION TERMS
        writer.write(validate.terminology())

        # VALIDATIONSET
        writer.write(F'{header("VALIDATIONSET")}\n\n')
        writer.write(F"{validationset_graph}\n{{")

        # VALIDATIONS
        for key, validation in validationset['items'].items():
            print(validation)
            writer.write(F'\n\t{Rsc.validation_ttl(key)}\n')
            writer.write(preVal('a', VoidPlus.Validation_ttl, position=2))

            for index, (val_header, value) in enumerate(predicate_map.items()):

                end = True if index == len(predicate_map) - 1 else False
                curr_feature = predicate_map.get(val_header, None)

                if curr_feature:

                    #  aACCEPTED | REJECTED | NOT-VALIDATED : UNSURE | MIXED
                    if curr_feature == VoidPlus.has_validation_status_ttl:
                        writer.write(preVal(VoidPlus.has_validation_status_ttl, validate.get_resource[validation[val_header]], end=end, position=2))

                    elif validation[val_header]:
                        writer.write(preVal(curr_feature, Literal(validation[val_header]).n3(MANAGER), end=end, position=2))

        writer.write("}")
        # print(writer.getvalue())
        return writer.getvalue()


def toLinkset(specs: dict, save_in: str, linkset_result, rdfStarReification: True, prefixes=None):

    """
    --------------------------------------------------
    THIS FUNCTION PROVIDES METADATA IN A TURTLE FORMAT
    --------------------------------------------------

    :param linkset_result     : Linkset file/result to convert to turtle.
    :param save_in            : The folder in which tio save turtle file.
    :param rdfStarReification : Annotation follows the SDFStat protocol if set to YES otherwise it follows the original
                                standard
    :param prefixes           : A disctionary of namespaces followed by the prefix

    :param specs              :

        linksetStats
            triples           : The number of triples
            entities          : The total number of entities that are described in the dataset.
            distinctSub       : The number of distinct entities at the subject position
            distinctObj       : The number of distinct entities at the object position
            clusters          : The number of clusters
            validations       : The number of link validated
            remains           : The number of links not validated

        linksetSpecs
            id                : (str)     The name of the linkset
            linkType          : (uri)     The predicate uri (owl:sameAs, skos:exactMatch...) used to describe the linkset.
            description       : {str}     The user provided matching goal of the method.
            sources           : ([str])   A list of identifiers of entity-type selections to use as source
            targets           : ([str])   A list of identifiers of entity-type selections to use as targets
            methods           : (dict)    The matching configuration for finding links. It requires at least one condition.
            properties        : ([dict])  A list of property paths to use for obtaining data while reviewing the linkset; optional field
            clusters          : {dict}    A dictionary indicating the size (value of the dictionary) of each cluster (key of the dictionRY)

    # The matching configuration is composed of one or more logic boxes
    "conditions": [
    {
        // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR')
        "type": "AND",

        // The type of matching to apply; see table below for allowed values
        "method_name": "=",

        // Some types of matching methods require extra configuration
        "method_value": {},

        // The source properties to use during matching
        "sources":
        [
            {
                // The identifier of the entity-type selection to use
                "entity_type_selection": 1,

                // The property path to which this condition applies
                 "property": ["schema_birthDate"],

                 // The transformers to apply to transform the value before matching; see table below for allowed values
                 "transformers":
                 [
                    {
                        "name": "PARSE_DATE",
                        "parameters": {
                        "format": "YYYY-MM-DD"
                     }
                ]
            }
        ],

        // The target properties to use during matching
        "targets":
        [
            {
                 "entity_type_selection": 1,
                 "property": ["schema_birthDate"],
                 "transformers": []
            }
        ],
    }]

    :return:
    """

    line, center = 70, 70
    linkset_specs = specs[Vars.linksetSpecs]
    job_id = linkset_specs[Vars.job_id]
    link_type = linkset_specs[Vars.linkType]
    auto_prefixes = defaultdict(str) if prefixes is None else prefixes
    start, resource, length = time(), Rsc(), 50
    name = Grl.prep4Iri(linkset_specs[Vars.id])

    # USER DEFINED/SUGGESTED PREFIXES
    mappings = {ns: prefix for prefix, ns in specs['linksetStats']['dynamic_uri_prefix_mappings'].items()}
    auto_prefixes.update(mappings)

    # my_ttl = join(save_in, F"DocumentedLinks-job_{job_id}-id_{name}.trig")
    my_ttl = join(save_in, F"DL_{job_id}_{name}.trig")

    # ****************************************************************
    # WRITING OF THE LINKSET
    # ****************************************************************

    comment = specs['linksetSpecs']['label']
    if len(comment) > 65:
        comment = F"{comment[:64]}..."
    print(F"""\n\n{'':>16}{'-' * line:^{center}}\n{'|':>16}{F"LINKSET DESCRIPTION":^{center}}|\n{'|':>16}{F"{comment}":^{center}}|\n{'':>16}{'-' * line:^{center}}\n
    {F'1. Creating Linkset {name}':{length}} {str(timedelta(seconds=time() - start))}""")

    # Create the linkset file
    with open(my_ttl, "w") as writer:

        # Dissect the link-type for prefix - namespace - name and turtle
        # For http://www.w3.org/2002/07/owl#sameAs, the uri2ttl function
        # returns ('owl', 'http://www.w3.org/2002/07/owl#', 'sameAs', 'owl:sameAs')
        # predicate_data = uri2ttl(reconstructTurtle(link_type, auto_prefixes=auto_prefixes), auto_prefixes=auto_prefixes)
        auto_prefixes[link_type['namespace']] = link_type['prefix']

        # Removing shared prefixes
        print("\t\t- Removing the following namespaces from the automatically generated namespaces")
        for key in SHARED:
            if key in auto_prefixes:
                print("\t\t\t.", key)
                del auto_prefixes[key]

        # GENERATING THE METADATA
        metadata = getMetadata(specs=specs, triples=True, prefixes=auto_prefixes)

        # WRITING THE NAMESPACES
        writer.write(
            linksetNamespaces(
                auto_prefixes,
                isValidated=specs['validations'] and len(specs['validations']) > 0,
                isClustered=Vars.clusters in specs[Vars.linksetStats] and specs[Vars.linksetStats][Vars.clusters] > 0))

        # WRITING THE METADATA
        writer.write(metadata)

        # # VALIDATION TERMS
        # writer.write(validate.terminology())

        # START OF THE LINKSET NAME GRAPH
        linkset = resource.linkset_ttl(F'{job_id}-{name}')
        writer.write(F"\n\n{'#' * 110}"
                     F"\n#{'ANNOTATED LINKSET':^108}#"
                     F"\n{'#' * 110}\n\n\n{linkset}"
                     F"\n{{\n")

        # CONVERTING THE MATCHING RESULT TO RDF AND STORING IT TO FILE
        for item in \
                rdfStarLinkGenerator(
                    mappings=mappings, link_predicate=link_type['short'], result_batch=linkset_result, offset=0) \
                if rdfStarReification else \
                standardLinkGenerator(
                    mappings=mappings, link_predicate=link_type['short'], result_batch=linkset_result, offset=0):

            # WRITE A YIELDED LINK
            writer.write(item)
            # print(item)

        # END OF THE NAME GRAPH
        writer.write("}")

    print(F"""{space}{'2. Process Terminated':{length}} {str(timedelta(seconds=time() - start))}
    3. {'File size':47} {Grl.fileSize(my_ttl)}
    4. Description\n{space * 2}{linkset_specs['label']}
    """)

    # --------------------------------------------------------------#
    #  CREATE THE VALIDATION GRAPH IF THE LINKS HAVE BEEN CLUSTERED #
    # --------------------------------------------------------------#
    validation_graphs = []
    if specs['validations'] and len(specs['validations']) > 0:
        for i, validationset in enumerate(specs['validations']):
            validation_graph = my_ttl.replace('.trig', F'_validations-{i+1}.trig')
            validation_graphs.append(validation_graph)
            with open(validation_graph, "w") as writer:
                writer.write(
                    validationGraphGenerator(
                        validationset,
                        specs['linksetStats'],
                        auto_prefixes,
                        setGraph=linkset,
                        set_id=name, isLinkset=True)
                )

    # --------------------------------------------------------------#
    #   CREATE THE CLUSTER GRAPH IF THE LINKS HAVE BEEN CLUSTERED   #
    # --------------------------------------------------------------#
    cluster_graph = None
    if specs['linksetSpecs']['clusters']:
        cluster_graph = my_ttl.replace('.trig', '_clusters.trig')
        with open(cluster_graph, "w") as writer:
            # WRITE A YIELDED CLUSTER
            writer.write(
                clusterGraphGenerator(
                    specs['linksetSpecs']['clusters'],
                    specs['linksetStats'],
                    auto_prefixes,
                    linkset, linkset_id=name)
            )

    return my_ttl, cluster_graph, validation_graphs


def toLens(specs: dict, save_in: str, linkset_result, rdfStarReification: True, prefixes=None):

    """
    --------------------------------------------------
    THIS FUNCTION PROVIDES METADATA IN A TURTLE FORMAT
    --------------------------------------------------

    :param linkset_result     : Linkset file/result to convert to turtle.
    :param save_in            : The folder in which tio save turtle file.
    :param rdfStarReification : Annotation follows the SDFStat protocol if set to YES otherwise it follows the original
                                standard
    :param prefixes           : A disctionary of namespaces followed by the prefix

    :param specs              :

        linksetStats
            triples           : The number of triples
            entities          : The total number of entities that are described in the dataset.
            distinctSub       : The number of distinct entities at the subject position
            distinctObj       : The number of distinct entities at the object position
            clusters          : The number of clusters
            validations       : The number of link validated
            remains           : The number of links not validated

        linksetSpecs
            id                : (str)     The name of the linkset
            linkType          : (uri)     The predicate uri (owl:sameAs, skos:exactMatch...) used to describe the linkset.
            description       : {str}     The user provided matching goal of the method.
            sources           : ([str])   A list of identifiers of entity-type selections to use as source
            targets           : ([str])   A list of identifiers of entity-type selections to use as targets
            methods           : (dict)    The matching configuration for finding links. It requires at least one condition.
            properties        : ([dict])  A list of property paths to use for obtaining data while reviewing the linkset; optional field
            clusters          : {dict}    A dictionary indicating the size (value of the dictionary) of each cluster (key of the dictionRY)

    # The matching configuration is composed of one or more logic boxes
    "conditions": [
    {
        // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR')
        "type": "AND",

        // The type of matching to apply; see table below for allowed values
        "method_name": "=",

        // Some types of matching methods require extra configuration
        "method_value": {},

        // The source properties to use during matching
        "sources":
        [
            {
                // The identifier of the entity-type selection to use
                "entity_type_selection": 1,

                // The property path to which this condition applies
                 "property": ["schema_birthDate"],

                 // The transformers to apply to transform the value before matching; see table below for allowed values
                 "transformers":
                 [
                    {
                        "name": "PARSE_DATE",
                        "parameters": {
                        "format": "YYYY-MM-DD"
                     }
                ]
            }
        ],

        // The target properties to use during matching
        "targets":
        [
            {
                 "entity_type_selection": 1,
                 "property": ["schema_birthDate"],
                 "transformers": []
            }
        ],
    }]

    :return:
    """

    line, center = 70, 70
    job_id = specs['lensSpecs'][Vars.job_id]
    link_type = specs['lensSpecs'][Vars.linkType]
    auto_prefixes = defaultdict(str) if prefixes is None else prefixes
    start, resource, length = time(), Rsc(), 90
    name = Grl.prep4Iri(specs['lensSpecs'][Vars.id])

    # my_ttl = join(save_in, F"DocumentedLinks-job_{job_id}-id_{name}.trig")
    my_ttl = join(save_in, F"DLens_{job_id}_{name}.trig")

    # USER DEFINED/SUGGESTED PREFIXES
    mappings = {ns: prefix for prefix, ns in specs['lensStats']['dynamic_uri_prefix_mappings'].items()}
    auto_prefixes.update(mappings)

    # Removing shared prefixes
    for key in SHARED:
        if key in auto_prefixes:
            del auto_prefixes[key]

    # ****************************************************************
    # WRITING OF THE LINKSET
    # ****************************************************************

    comment = specs['lensSpecs']['label']
    if len(comment) > 65:
        comment = F"{comment[:64]}..."
    print(F"""\n\n{'':>16}{'-' * line:^{center}}\n{'|':>16}{F"LENS DESCRIPTION":^{center}}|\n{'|':>16}{F"{comment}":^{center}}|\n{'':>16}{'-' * line:^{center}}\n
    {F'1. Creating Lens {name} ':.<{length}} {str(timedelta(seconds=time() - start))}""")

    # Create the linkset file
    with open(my_ttl, "w") as writer:

        print(F"\t{F'2. The file:{my_ttl} is open. ':.<{length}} {str(timedelta(seconds=time() - start))}")

        # Dissect the link-type for prefix - namespace - name and turtle
        # For http://www.w3.org/2002/07/owl#sameAs, the uri2ttl function
        # returns ('owl', 'http://www.w3.org/2002/07/owl#', 'sameAs', 'owl:sameAs')
        # predicate_data = uri2ttl(reconstructTurtle(link_type, auto_prefixes=auto_prefixes), auto_prefixes=auto_prefixes)
        auto_prefixes[link_type['namespace']] = link_type['prefix']

        print(
            F"\t{'3. The metadata is being collected ':.<{length}} {str(timedelta(seconds=time() - start))}")
        metadata = getLensMetadata(specs=specs, prefixes=auto_prefixes,
                                   isValidated=specs['validations'] is not None,
                                   isClustered=specs['clusters'] is not None)

        # WRITING THE METADATA
        writer.write(metadata)
        print(F"\t{'4. The metadata is collected and written to file ':.<{length}} {str(timedelta(seconds=time() - start))}")

        # # VALIDATION TERMS
        # writer.write(validate.terminology())

        # START OF THE LINKSET NAME GRAPH
        lens_rsc = resource.lens_ttl(F'{job_id}-{name}')
        writer.write(subHeader('ANNOTATED LENS', linesBefore=0))
        writer.write(F"\n{lens_rsc}\n{{\n")

        # CONVERTING THE MATCHING RESULT TO RDF AND STORING IT TO FILE
        for item in \
                rdfStarLinkGenerator(
                    mappings=mappings, link_predicate=link_type['short'],
                    result_batch=linkset_result, offset=0) \
                if rdfStarReification else \
                standardLinkGenerator(
                    mappings=mappings, link_predicate=link_type['short'],
                    result_batch=linkset_result, offset=0):

            # WRITE A YIELDED LINK
            writer.write(item)

        # END OF THE NAME GRAPH
        writer.write("}")

    print(F"""{space}{'5. Process Terminated ':.<{length}} {str(timedelta(seconds=time() - start))}
    {'6. File size ':.<{length}} {Grl.fileSize(my_ttl)}
    7. Description\n{space * 2}{specs['lensSpecs']['label']}
    """)

    # --------------------------------------------------------------#
    #  CREATE THE VALIDATION GRAPH IF THE LINKS HAVE BEEN CLUSTERED #
    # --------------------------------------------------------------#
    validation_graphs = []
    if specs['validations'] and len(specs['validations']) > 0:
        for i, validationset in enumerate(specs['validations']):
            validation_graph = my_ttl.replace('.trig', F'_validations-{i+1}.trig')
            validation_graphs.append(validation_graph)
            with open(validation_graph, "w") as writer:
                writer.write(
                    validationGraphGenerator(
                        validationset,
                        specs['lensStats'],
                        auto_prefixes,
                        setGraph=lens_rsc,
                        set_id=name, isLinkset=False)
                )

    # --------------------------------------------------------------#
    #   CREATE THE CLUSTER GRAPH IF THE LINKS HAVE BEEN CLUSTERED   #
    # --------------------------------------------------------------#
    cluster_graph = None
    if specs['clusters']:
        cluster_graph = my_ttl.replace('.trig', '_clusters.trig')
        with open(cluster_graph, "w") as writer:
            # WRITE A YIELDED CLUSTER
            writer.write(
                clusterGraphGenerator(
                    specs['clusters'],
                    specs['lensStats'],
                    auto_prefixes,
                    lens_rsc, linkset_id=name)
            )

    return my_ttl, cluster_graph, validation_graphs

