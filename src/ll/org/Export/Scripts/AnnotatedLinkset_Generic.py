# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   CREATION OF AN ANNOTATED LINKSET USING STANDARD REIFICATION FORMAT OR RDFSTAR                         #
#                                                                                                         #
# #########################################################################################################


from rdflib import URIRef, Literal
from os.path import join
import ll.org.Export.Scripts.Variables as Vars
from collections import defaultdict
import ll.org.Export.Scripts.General as Grl
from ll.org.Export.Scripts.Specs2Metadata import \
    uri2ttl, reconstructTurtle, preVal, linksetNamespaces, \
    unboxingLinksetSpecs as getMetadata,  clearBuffer

from ll.org.Export.Scripts.VoidPlus import VoidPlus
from ll.org.Export.Scripts.Resources import Resource as Rsc
from datetime import timedelta
from time import time
from io import StringIO as Buffer
from ll.org.Export.Scripts.Validation import Validate
from rdflib import Graph
MANAGER = Graph().namespace_manager

validate = Validate()

# FORMATTING SPACE
space = "    "

# MAPPING OF LINKSET HEADERS
CSV_HEADERS = {
    "Valid": VoidPlus.link_validation_tt,
    "Max Strength": VoidPlus.strength_ttl,
    "Strength": VoidPlus.strength_ttl,
    "Cluster ID": VoidPlus.cluster_ID_ttl
}

# Shared prefixes to remove from the set of automated prefixes
SHARED = [
    'http://www.w3.org/2000/01/rdf-schema#', 'http://www.w3.org/2000/01/rdf-schema#', 'http://www.w3.org/2002/07/owl#',
    'http://rdfs.org/ns/void#', 'http://purl.org/dc/terms/', 'http://www.w3.org/ns/formats/',
    'http://purl.org/ontology/similarity/', 'http://creativecommons.org/ns#', 'http://www.w3.org/2001/XMLSchema#']


def rdfStarLinkGenerator(link_predicate: str, result_batch, clusters=None, offset=0):

    errors = ""
    vars_size = 0
    buffer = Buffer()
    vars_dic = defaultdict(int)

    for count, row in enumerate(result_batch):

        try:

            # THE FIRST LINE IS ASSUMED TO BE THE HEADER
            if count > 0:

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
                        if clusters and predicate == VoidPlus.cluster_ID_ttl and row[index] in clusters:
                            buffer.write(F"{space * 2}{VoidPlus.cluster_size_ttl:{Vars.PRED_SIZE}}"
                                         F"{Literal(clusters[row[index]]).n3(MANAGER)} ;\n")

                        # APPENDING THE VALIDATION FLAG
                        if predicate == VoidPlus.link_validation_tt:
                            triple_value = validate.get_resource[row[index]]

                        # APPENDING DING ANYTHING ELSE
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

        except Exception as err:
            errors += F">>>> [ERROR FROM csv_2_linkset] {row}, {err}"


def standardLinkGenerator(link_predicate: str, result_batch, clusters=None, offset=0):

    """
    :param offset           : an integer to increment the counting of tghe links
    :param link_predicate   : a turtle representation of a URI (e.i: owl:sameAs).
    :param result_batch     : an iterable object with link results.
    :return                 : Yields a string as set of triples.
    """
    errors = ""
    vars_size = 0
    buffer = Buffer()
    vars_dic = defaultdict(int)
    header = None

    for count, row in enumerate(result_batch):

        if True:

            # THE FIRST LINE IS ASSUMED TO BE THE HEADER
            if count > 0:

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
                        if clusters and predicate == VoidPlus.cluster_ID_ttl:
                            buffer.write(F"{space * 2}{VoidPlus.cluster_size_ttl:{Vars.PRED_SIZE}}"
                                         F"{Literal(clusters[row[index]]).n3(MANAGER)} ;\n")

                        # APPENDING THE VALIDATION FLAG
                        if predicate == VoidPlus.link_validation_tt:
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

        # except Exception as err:
        #     errors += F">>>> [ERROR FROM csv_2_linkset] {row}, {err}"
        #     print(errors)


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

    linkset_specs = specs[Vars.linksetSpecs]
    job_id = linkset_specs[Vars.job_id]
    link_type = linkset_specs[Vars.linkType]
    auto_prefixes = defaultdict(str) if prefixes is None else prefixes
    start, resource, length = time(), Rsc(), 50
    name = Grl.prep4Iri(linkset_specs[Vars.id])

    # my_ttl = join(save_in, F"DocumentedLinks-job_{job_id}-id_{name}.trig")
    my_ttl = join(save_in, F"DL_{job_id}_{name}.trig")

    # Removing shared prefixes
    for key in SHARED:
        if key in auto_prefixes:
            del auto_prefixes[key]

    # ****************************************************************
    # WRITING OF THE LINKSET
    # ****************************************************************

    print(F"""\n{'-' * 70}\n{F"LINKSET DESCRIPTION":^70}\n{F"{specs['linksetSpecs']['label']}":^{70}}\n{'-' * 70}\n
    {F'1. Creating Linkset {name}':{length}} {str(timedelta(seconds=time() - start))}""")

    # Create the linkset file
    with open(my_ttl, "w") as writer:

        # Dissect the link-type for prefix - namespace - name and turtle
        # For http://www.w3.org/2002/07/owl#sameAs, the uri2ttl function
        # returns ('owl', 'http://www.w3.org/2002/07/owl#', 'sameAs', 'owl:sameAs')
        predicate_data = uri2ttl(reconstructTurtle(link_type, auto_prefixes=auto_prefixes), auto_prefixes=auto_prefixes)

        metadata = getMetadata(specs=specs, triples=True, prefixes=auto_prefixes)

        # WRITING THE NAMESPACES
        writer.write(linksetNamespaces(auto_prefixes))

        # WRITING THE METADATA
        writer.write(metadata)

        # VALIDATION TERMS
        writer.write(validate.terminology())

        # START OF THE LINKSET NAME GRAPH
        writer.write(F"\n\n{'#' * 110}"
                     F"\n#{'ANNOTATED LINKSET':^108}#"
                     F"\n{'#' * 110}\n\n\n{resource.linkset_ttl(name)}"
                     F"\n{{\n")

        # CONVERTING THE MATCHING RESULT TO RDF AND STORING IT TO FILE
        for item in rdfStarLinkGenerator(
                link_predicate=predicate_data[3], result_batch=linkset_result, clusters=specs['linksetSpecs']['clusters'], offset=0) \
                if rdfStarReification else \
                standardLinkGenerator(link_predicate=predicate_data[3], result_batch=linkset_result, offset=0):

            # WRITE A YIELDED LINK
            writer.write(item)
            # print(item)

        # END OF THE NAME GRAPH
        writer.write("}")

    print(F"""{space}{'2. Process Terminated':{length}} {str(timedelta(seconds=time() - start))}
    3. {'File size':47} {Grl.fileSize(my_ttl)}
    4. Description\n{space * 2}{linkset_specs['label']}
    """)

    return my_ttl


# \{'is_percentage': True, 'threshold': 2, 'unique_is_percentage': True, 'unique_threshold': 5}
# {'is_percentage': False, 'threshold': 2, 'unique_is_percentage': False, 'unique_threshold': 5}
