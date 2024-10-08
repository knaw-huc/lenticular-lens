# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   CREATION OF AN ANNOTATED LINKSET USING STANDARD REIFICATION FORMAT OR RDFSTAR                         #
#                                                                                                         #
# #########################################################################################################

from os.path import join
import lenticularlens.org.Export.Scripts.Variables as Vars
from collections import defaultdict
import lenticularlens.org.Export.Scripts.General as Grl
from csv import reader as csv_reader
from lenticularlens.org.Export.Scripts.Specs2Metadata import uri2ttl, reconstructTurtle, preVal, unboxingLinksetSpecs, linksetNamespaces
from lenticularlens.org.Export.Scripts.VoidPlus import VoidPlus
from rdflib import URIRef, Literal
from lenticularlens.org.Export.Scripts.Resources import Resource as Rsc
from datetime import timedelta
from time import time
from os import remove as remove_file

CSV_HEADERS = {
    "Valid": VoidPlus.has_validation_status_ttl,
    "Strength": VoidPlus.strength_ttl,
    "Cluster ID": VoidPlus.cluster_ID_ttl
}


# CONVERTS A CSV LINKSET IN TO RDFStar ANNOTATED TRIPLES
def csv2RDFStarLinkset(csv_linkset_file: str, link_type: str, auto_prefixes: dict):

    errors = ""
    ttl_file = F"{csv_linkset_file}.ttl"
    vars_dic = defaultdict(int)
    vars_size = 0

    # WRITING THE TURTLE FILE
    with open(ttl_file, "w") as writer:

        # Reading the old csv file
        with open(csv_linkset_file, "r") as csv_file:

            # Dissect the link-type for prefix - namespace - name and turtle
            predicate_data = uri2ttl(
                reconstructTurtle(link_type, auto_prefixes=auto_prefixes), auto_prefixes=auto_prefixes)

            for count, row in enumerate(csv_reader(csv_file)):

                try:

                    # THE FIRST LINE IS ASSUMED TO BE THE HEADER
                    if count > 0:

                        # GET THE SOURCE AND TARGET URIS
                        src_data, trg_data = uri2ttl(
                            uri=row[0], auto_prefixes=auto_prefixes), uri2ttl(row[1], auto_prefixes)

                        # GENERATION OF THE LINK
                        if src_data and trg_data and src_data[3] is not None and trg_data[3] is not None:

                            # The RDFStar subject
                            writer.write(F"\t### LINK Nbr: {count}\n")
                            writer.write(F"\t<<{src_data[3]}    {predicate_data[3]}    {trg_data[3]}>>\n"
                                         if len(vars_dic) > 0
                                         else F"\t{src_data[3]}    {predicate_data[3]}    {trg_data[3]} .\n")

                            # ANNOTATION OF THE LINK
                            # ll_val:has-link-validation               "not_validated" .
                            for counter, (predicate, index) in enumerate(vars_dic.items()):
                                end = ".\n" if counter == vars_size - 1 else ";"
                                writer.write(F"\t\t{predicate:{Vars.PRED_SIZE}}"
                                             F"{Literal(row[index]).n3() if not Grl.isDecimalLike(row[index]) else round(float(row[index]), 5)} {end}\n")

                    else:

                        # THE CSV HEADER
                        # Star at position
                        for column in range(2, len(row)):

                            if row[column] in CSV_HEADERS:
                                vars_dic[CSV_HEADERS[row[column]]] = column
                                vars_size += 1

                except Exception as err:
                    errors += F">>>> [ERROR FROM csv_2_linkset] {row}, {err}"

    return ttl_file


# CONVERTS A CSV LINKSET IN TO THE STANDARD ANNOTATED TRIPLES
def csv2Linkset(csv_linkset_file: str, link_type: str, auto_prefixes: dict):
    errors = ""
    ttl_file = F"{csv_linkset_file}.ttl"

    # LOAD PARAMETERS THAT ARE NOT THE SOURCE - TARGET - OR PROPERTY
    vars_dic = defaultdict(int)
    vars_size = 0

    # WRITING THE TURTLE FILE
    with open(ttl_file, "w") as writer:

        # Reading the old csv file
        with open(csv_linkset_file, "r") as csv_file:

            # Dissect the link-type for prefix - namespace - name and turtle
            predicate_data = uri2ttl(reconstructTurtle(link_type, auto_prefixes=auto_prefixes), auto_prefixes=auto_prefixes)

            for count, row in enumerate(csv_reader(csv_file)):

                if True:

                    # THE FIRST LINE IS ASSUMED TO BE THE HEADER
                    if count > 0:

                        # GET THE SOURCE AND TARGET URIS
                        src_data, trg_data = uri2ttl(uri=row[0], auto_prefixes=auto_prefixes), uri2ttl(row[1], auto_prefixes)

                        # GENERATION OF THE LINK
                        if src_data and trg_data and src_data[3] is not None and trg_data[3] is not None:

                            # The RDFStar subject
                            writer.write(F"\n\t### LINK Nbr: {count}\n")
                            link = F"\t{src_data[3]}    {predicate_data[3]}    {trg_data[3]} .\n"
                            writer.write(F"\t{src_data[3]}    {predicate_data[3]}    {trg_data[3]} .\n")

                            # STANDARD REIFICATION
                            code = Rsc.ga_resource_ttl(F"Reification-{Grl.deterministicHash(link)}")
                            writer.write(F"\n\t### STANDARD REIFICATION Nbr: {count}")
                            writer.write(F"\n\t{code}\n")
                            writer.write(F"\t{preVal('a', 'rdf:Statement')}")
                            writer.write(F"\t{preVal('rdf:predicate', predicate_data[3])}")
                            writer.write(F"\t{preVal('rdf:subject', src_data[3])}")
                            writer.write(F"\t{preVal('rdf:object', trg_data[3])}")

                            # ANNOTATION OF THE LINK USING THE REIFGIED CODE
                            for counter, (predicate, index) in enumerate(vars_dic.items()):
                                end = ".\n" if counter == vars_size - 1 else ";"
                                writer.write(F"\t\t{predicate:{Vars.PRED_SIZE}}"
                                             F" {Literal(row[index]).n3() if not Grl.isDecimalLike(row[index]) else round(float(row[index]), 5)} {end}\n")

                    # THE MAPPING OF GHE CSV HEADERS TO VOIDPLUS RDF PREDICATES
                    else:

                        # THE CSV HEADER
                        # Star at position
                        for column in range(2, len(row)):

                            if row[column] in CSV_HEADERS:
                                vars_dic[CSV_HEADERS[row[column]]] = column
                                vars_size += 1

                # except Exception as err:
                #     errors += F">>>> [ERROR FROM csv_2_linkset] {row}, {err}"

    return ttl_file


def linkset(specs: dict, save_in: str, csv_linkset_file: str, rdfStarReification: True, prefixes=None):

    """
    --------------------------------------------------
    THIS FUNCTION PROVIDES METADATA IN A TURTLE FORMAT
    --------------------------------------------------

    :param csv_linkset_file   : The CSV linkset file to convert to turtle.
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
    name = Grl.prep4Iri(linkset_specs[Vars.id])
    auto_prefixes = defaultdict(str) if prefixes is None else prefixes
    start, resource, length = time(), Rsc(), 50
    my_ttl = join(save_in, F"DocumentedLinks-job_{job_id}-id_{name}.trig")

    # Shared prefixes to remove from the set of automated prefixes
    shared = [
        'http://www.w3.org/2000/01/rdf-schema#', 'http://www.w3.org/2000/01/rdf-schema#',
        'http://www.w3.org/2002/07/owl#', 'http://rdfs.org/ns/void#', 'http://purl.org/dc/terms/',
        'http://www.w3.org/ns/formats/', 'http://purl.org/ontology/similarity/', 'http://creativecommons.org/ns#',
        'http://www.w3.org/2001/XMLSchema#'
    ]

    # Removing shared prefixes
    for key in shared:
        if key in auto_prefixes:
            del auto_prefixes[key]

    print(F"\nLINKSET AT POSITION [{specs['linksetSpecs']['id']}] CREATION {Grl.fileSize(csv_linkset_file)}\n{'-' * 70}")
    print(F"\t{F'1. Creating Linkset {name}':{length}} {str(timedelta(seconds=time() - start))}")
    print(F"\t\tDescription : {linkset_specs['label']}")

    linkset_header = F"""\n\n{'#' * 110}\n#{'ANNOTATED LINKSET':^108}#\n{'#' * 110}\n\n\n{resource.linkset_ttl(name)}\n{{\n"""

    # ****************************************************************
    # GET THE METHODS HASH AND THE METHODS' ANNOTATIONS
    # ****************************************************************
    methods = unboxingLinksetSpecs(specs=specs, triples=True)

    # Create the linkset
    with open(my_ttl, "w") as writer:

        print(F"\t{'2. Generating the temporarily csv conversion':{length}} {str(timedelta(seconds=time() - start))}")

        temp = csv2RDFStarLinkset(csv_linkset_file, link_type, auto_prefixes=auto_prefixes) \
            if rdfStarReification else csv2Linkset(csv_linkset_file, link_type, auto_prefixes=auto_prefixes)

        writer.write(linksetNamespaces(auto_prefixes))
        writer.write(methods)
        writer.write(linkset_header)

        print(F"\t{'3. Copying the temporarily csv conversion':{length}} {str(timedelta(seconds=time() - start))}")
        with open(temp, "r") as converted_ttl:
            for line in converted_ttl:
                writer.write(line)
            writer.write("}")

        print(F"\t{'3. Removing the temporarily csv conversion':{length}} {str(timedelta(seconds=time() - start))}")
        # Delete the temporarily converted linkset
        remove_file(temp)

    # return F"{prefixes} {generic_meta}  {linkset}}}", errors
    return my_ttl
