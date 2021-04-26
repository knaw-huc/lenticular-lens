# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   DOCUMENTATION OF THE WHO - WHAT AND HOW OF A LINKSET BASED ON THE USERS'S SPECIFICATION               #
#                                                                                                         #
# #########################################################################################################

import requests
import ll.org.Export.Scripts.Variables as Vars
import ll.org.Export.Scripts.General as Grl
from ll.org.Export.Scripts import FuzzyNorms
from collections import defaultdict, deque
from io import StringIO as Buffer
from rdflib import URIRef, Literal
from ll.org.Export.Scripts.Algotithms import Algorithm
from ll.org.Export.Scripts.Resources import Resource as Rsc
from ll.org.Export.Scripts.VoidPlus import VoidPlus
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from string import digits
from anytree import Node, RenderTree, DoubleStyle, PostOrderIter
from rdflib import Graph
import ll.org.Export.Scripts.CountryCode as Country


RSC_SELECTION = {}
SAME_AS = Sns.OWL.sameAs_ttl
MANAGER = Graph().namespace_manager
DEFAULT_LICENCE = Sns.DCterms.license_ttl
GET_LOGIC_OPERATOR = lambda operator: FuzzyNorms.LogicOperations.operator_format[operator.lower()]
CSV_HEADERS = {
    "Valid": VoidPlus.link_validation_tt,
    "Max Strength": VoidPlus.strength_ttl,
    "Cluster ID": VoidPlus.cluster_ID_ttl
}
NORMSs = [

    'AND', 'OR',

    'AND [Minimum t-norm (⊤min)]', 'AND [Hamacher Product (⊤H0)]', 'AND [Product t-norm (⊤prod)]',
    'AND [Nilpotent Minimum (⊤nM)]', 'AND [Łukasiewicz t-norm (⊤Luk)]', 'AND [Drastic t-norm (⊤D)]',

    'OR [Maximum s-norm (⊥max)]', 'OR [Probabilistic Sum (⊥sum)]', 'OR [Bounded Sum (⊥Luk)]',
    'OR [Drastic s-norm (⊥D)]', 'OR [Nilpotent Maximum (⊥nM)]', 'OR [Einstein Sum (⊥D)]']
space = "    "
language_code = Sns.ISO()



# CLEARS THE StringIO GIVEN OBJECT
def clearBuffer(buffer):

    buffer.seek(0)
    buffer.truncate(0)


# CLEARS THE StringIO GIVEN OBJECT AND WRITES TO IT THE PROVIDED STRING
def resetBuffer(buffer, text):

    buffer.seek(0)
    buffer.truncate(0)
    buffer.write(text)


def getExpressionAndTree(root):

    """
    :param root : the root of the tree
    :return     : Tuple of strings (fomula expression, formula tree)
    """

    # List of operations in post order for generating the formula expression
    post_order = [node.name for node in PostOrderIter(root)]

    if len(root.children) == 1:
        root = root.children[0]
        root.parent = None

    return (expression_generator(post_order)[0],
            F'\n{space}'.join([F"{space}%s%s" % (pre, node.name)
                               for i, (pre, fill, node) in enumerate(RenderTree(root, style=DoubleStyle))]))


def expression_generator(postOrder):

    temporary = []
    new = []

    for item in postOrder:

        # NOT AN OPERATOR
        if item.strip() and item.strip().startswith("AND") is False and item.strip().startswith("OR") is False:
            temporary.append(item)

        else:

            if len(temporary) > 1:

                new.append(F'( {F" {item.upper()} ".join(temporary)} )')
                temporary.clear()

            elif len(temporary) == 1:

                new = [F'( {F" {item.upper()} ".join(new + temporary)} )']
                temporary.clear()

            else:
                new.append(item)

    if len(new) > 1:
        new = expression_generator(new)

    return new if new else postOrder


# RETURN (1) <PREDICATE> <PREDICATE-VALUE> IF A SINGLE PROPERTY IS PROVIDED AND A (2) PREFIX:NAME
# RETURN (1) AN RDF SEQUENCE AND (2) PREFIX:NAME IF A PROPERTY PATH IS PROVIDED
def rdfSequence(sequence: list, auto=True, only=False):

    if len(sequence) == 0:
        return None, None

    if len(sequence) == 1 and auto is True:
        # SEQUENCE TYPE
        triples = preVal('a', VoidPlus.PropertyPartition_ttl)
        # triples = preVal(Sns.VoID.property_tt, Rsc.uri_resource(sequence[0]), line=True)
        triples += preVal(Sns.VoID.property_ttl, Rsc.ga_resource_ttl(sequence[0] if sequence[0] else '...........'), line=True)
        code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(triples)}")
        triples = F"{code}\n{triples}"

    else:

        # SEQUENCE TYPE
        triples = ""
        if only is False:
            triples = preVal('a', VoidPlus.PropertyPartition_ttl)
            triples += F"{space}{Sns.VoID.property_ttl}\n"

        # THE RDF SEQUENCE
        seq = F"{space * 2}{preVal('a', Sns.RDFS.sequence_ttl)}"
        for index, item in enumerate(sequence):

            pred = F"rdf:_{index+1}"
            end = "" if index == len(sequence) - 1 else ";"
            seq += F"{space * 3}{pred:{Vars.PRED_SIZE}}{Rsc.ga_resource_ttl(item if item else '... NONE VALUE PROBLEM...')} {end}\n"

        # THE SEQUENCE CODE
        triples += F"{space * 2}[\n{seq} {space * 2}]"
        code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(triples)}")

        # THE FINAL SEQUENCE
        triples = F"{code}\n{triples} ;" if only is False else F"\n{triples} "

    return triples, code


def rdfSAlgorithmSequence(sequence: list, auto=True):

    if len(sequence) == 0:
        return None, None

    if len(sequence) == 1 and auto is True:
        # SEQUENCE TYPE
        triples = preVal('a', VoidPlus.algoSequence_ttl)
        # triples = preVal(Sns.VoID.property_tt, Rsc.uri_resource(sequence[0]), line=True)
        triples += preVal(Sns.VoID.property_ttl, Rsc.ga_resource_ttl(sequence[0] if sequence[0] else '...........'), line=True)
        code = Rsc.ga_resource_ttl(F"AlgorithmSequence-{Grl.deterministicHash(triples)}")
        triples = F"{code}\n{triples}"

    else:

        # SEQUENCE TYPE
        triples = ''

        # THE RDF SEQUENCE
        seq = F"{preVal('a', Sns.RDFS.sequence_ttl)}"
        for index, item in enumerate(sequence):
            pred = F"\n{space}rdf:_{index+1}"
            end = "" if index == len(sequence) - 1 else ";"
            seq += F"{space}{pred:{Vars.PRED_SIZE}}{Rsc.ga_resource_ttl(item if item else '...........')} {end}\n"

        # THE SEQUENCE CODE
        triples += F"{space}\n{seq}"
        code = Rsc.ga_resource_ttl(F"AlgorithmSequence-{Grl.deterministicHash(triples)}")

        # THE FINAL SEQUENCE
        triples = F"{code}\n{triples} ;"

    return triples, code


# Given a URI such as http://www.w3.org/2004/02/skos/core#exactMatch
# reconstruct it in turtle format as skos:exactMatch,
# THIS FUNCTION ALSO UPDATES THE VARIABLE auto_prefixes
# WHICH SAVES ALL PREFIXES AUTOMATICALLY GENERATED
def uri2ttl(uri, auto_prefixes):

    if Grl.isNtFormat(uri):
        uri = Grl.undoNtFormat(uri)

    try:

        # Get the local name of the URI
        rsc_name = Grl.getUriLocalNamePlus(uri=uri, sep="_")

        # Get the local name
        rsc_namespace = uri.replace(rsc_name, "")

        # Get the prefix that can be used for the URI if it exists in the global prefix dictionary
        if rsc_namespace in auto_prefixes:
            rsc_prefix = auto_prefixes[rsc_namespace]

        else:

            # Check if the namespace is registered in LOV's dataset
            result = Grl.queryEndpoint(query=getLovPrefixes(rsc_namespace), endpoint=Vars.LOV)

            if result and result["results"]["bindings"]:
                rsc_prefix = result["results"]["bindings"][0]['output']["value"]

            else:
                # As the namespace is not in the global prefix dictionary and LOV let us automate it
                prefix = Grl.getUriLocalNamePlus(uri=rsc_namespace, sep="_")
                code = Grl.hasher(rsc_namespace.replace(prefix, ""))

                if prefix[0] in digits:
                    prefix = F"N{prefix}"
                rsc_prefix = F"""{prefix.replace('-', '_')}_{code[:5]}"""

            # Update the global prefix dictionary
            auto_prefixes[rsc_namespace] = rsc_prefix

        # Compose the source and target of the URI
        turtle = F"{rsc_prefix}:{rsc_name}" if rsc_prefix is not None and not Grl.isNumber(rsc_prefix) else URIRef(
            uri).n3(MANAGER)

        return rsc_prefix, rsc_namespace, rsc_name, turtle

    except Exception as err:
        print(F">>> [ERROR FROM uri_2_turtle] URI: \n{space}{uri:30}\n{space}{err}\n")


# Given a turtle format such as owl:sameAs or skos:exactMatch,
# reconstruct it as http://www.w3.org/2004/02/skos/core#exactMatch and
# http://www.w3.org/2002/07/owl#
def reconstructTurtle(turtle, auto_prefixes):

    if not turtle.__contains__("://"):
        # splits => skos:exact
        splits = turtle.split(':')

        query = F"""
            PREFIX vann:<http://purl.org/vocab/vann/>
            PREFIX voaf:<http://purl.org/vocommons/voaf#>

            ### Vocabularies contained in LOV and their prefix
            SELECT DISTINCT ?output {{
                GRAPH <https://lov.linkeddata.es/dataset/lov>{{
                    ?vocab a voaf:Vocabulary;
                           vann:preferredNamespacePrefix "{splits[0]}" ;
                           vann:preferredNamespaceUri ?output .
            }}}}
        """

        result = Grl.queryEndpoint(query=query, endpoint=Vars.LOV)
        if result and result["results"]["bindings"]:
            rsc_namespace = result["results"]["bindings"][0]['output']["value"]
            auto_prefixes[rsc_namespace] = splits[0]

            return F"{rsc_namespace}{splits[1]}"

        return turtle


# Given a registered namespace such as http://purl.org/dc/terms/,
# return the query for fetching the URI's preferred prefix which is dcterms
def getLovPrefixes(namespace):

    return F"""
    PREFIX vann:<http://purl.org/vocab/vann/>
    PREFIX voaf:<http://purl.org/vocommons/voaf#>

    ### Vocabularies contained in LOV and their prefix
    SELECT DISTINCT ?output {{
        GRAPH <https://lov.linkeddata.es/dataset/lov>{{
            ?vocab a voaf:Vocabulary;
                   vann:preferredNamespacePrefix ?output ;
                   vann:preferredNamespaceUri "{namespace}" .
    }}}}
        """


# RETURNS A PREDICATE VALUE LINE
def preVal(predicate, value, end=False, line=True):

    new_line = '\n' if line is True else ''
    tab = F'{space}' if line is True else ''
    return F"{tab}{predicate:{Vars.PRED_SIZE}}{value} {'.' if end is True else ';'}{new_line}"


# RETURN THE GENERIC NAMESPACES USED IN A LINKSET
def linksetNamespaces(automated: dict):

    names = F"""{'#'*110}\n#{'NAMESPACES':^108}#\n{'#'*110}\n

### PREDEFINED SHARED NAMESPACES    
    {Sns.RDF.prefix}
    {Sns.RDFS.prefix}
    {Sns.OWL.prefix}
    {Sns.VoID.prefix}
    {Sns.DCterms.prefix}
    {Sns.Formats.prefix}
    {Sns.SIM.prefix}
    {Sns.CC.prefix}
    {Sns.XSD.prefix}

### PREDEFINED SPECIFIC NAMESPACES
    {VoidPlus.ontology_prefix}
    {Rsc.resource_prefix}
    {Rsc.linkset_prefix}

### AUTOMATED / EXTRACTED NAMESPACES
    """
    if automated:
        for count, (namespace, prefix) in enumerate(automated.items()):
            names += F"{'    ' if count > 0 else ''}@prefix {prefix:>{Vars.PREF_SIZE}}: {URIRef(namespace).n3(MANAGER)} .\n"

    return names


# THE UNBOXING OF A FILTER LOGIC BOX
def unboxingFilter(logicBox, checker):

    root = None
    predicate_selection = Buffer()
    predicate_sequences = Buffer()

    def filterBox(f_Box):

        if Vars.conditions in f_Box:

            for item in f_Box[Vars.conditions]:

                temp = Buffer()

                # RECURSIVE CALL
                if Vars.conditions in item:
                    filterBox(item)

                # UNBOXING OF THE ACTUAL CONSTRAINT
                else:

                    # sequence = rdfSequence(item[Vars.filterProperty])
                    sequence = rdfSequence(
                        item[Vars.short_properties]
                        if Vars.short_properties in item and len(item[Vars.short_properties]) > 0
                        else item[Vars.long_properties] if Vars.long_properties in item else item[Vars.filterProperty])

                    seq_function = item[Vars.filterType] if Vars.filterType in item else ""
                    seq_value = item[Vars.filterValue] if Vars.filterValue in item else ""
                    seq_format = item[Vars.format] if Vars.format in item else ""

                    new_info = len(seq_function) > 0 or len(seq_value) > 0 or len(seq_format) > 0

                    if new_info is True:

                        # THE FILTER FUNCTION
                        if len(seq_function) > 0:
                            temp.write(
                                preVal(VoidPlus.filterFunction_ttl, Literal(seq_function, lang='en').n3(MANAGER)))

                        # THE FILTER VALUE
                        if len(str(seq_value)) > 0:
                            temp.write(preVal(VoidPlus.filterValue_ttl, Literal(seq_value).n3(MANAGER)))

                        # THE FILTER FORMAT TO APPLY
                        if len(seq_format) > 0:
                            temp.write(preVal(VoidPlus.filterFormat_ttl, Literal(seq_format).n3(MANAGER)))

                    code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(sequence[0] + temp.getvalue())}")
                    sequence = sequence[0].replace(sequence[1], code)

                    # IF THE SEQUENCE IS NOT EMPTY
                    if sequence:

                        # FORMULATION HAS ITEM
                        predicate_selection.write(preVal(VoidPlus.hasItem_ttl, code))

                        if code not in checker:
                            checker[code] = 'in'

                            if new_info is False:
                                predicate_sequences.write(F"\n\n{sequence}")

                            else:
                                predicate_sequences.write(F"\n\n{sequence.rstrip()[:-1]};\n\n")
                                predicate_sequences.write(temp.getvalue())
                                clearBuffer(temp)
                                resetBuffer(predicate_sequences, F"{predicate_sequences.getvalue().rstrip()[:-1]}.\n")

    # RUNNING THE RECURSIVE FUNCTION
    filterBox(logicBox)

    if 'conditions' in logicBox and logicBox['conditions']:
        root = Node(GET_LOGIC_OPERATOR(logicBox['type']))
        filter_formula(logicBox['conditions'], parent=root)

    return predicate_selection.getvalue(), predicate_sequences.getvalue(), root


# THE UNBOXING OF THE ENTITY SELECTION FILTER
#  ### RESOURCE
def unboxingFilterBox(job_id, collection, checker):

    global RSC_SELECTION
    writer = Buffer()
    id = collection[Vars.id]

    label = collection[Vars.label]
    description = collection[Vars.description] if Vars.description in collection else ""
    dataset = collection[Vars.dataset]
    RSC_SELECTION[id] = dataset
    predicate_selections, sequences, root = unboxingFilter(logicBox=collection['filter'], checker=checker)

    # FORMULATION HAS CLASS PARTITION
    class_partition = F"[ {Sns.VoID.voidClass_ttl} {Rsc.ga_resource_ttl(dataset['collection_id'])} ]"
    class_partition_rsc = Rsc.ga_resource_ttl(F"ClassPartition-{Grl.deterministicHash(class_partition)}")

    expression, f_tree = None, None
    if root:
        # ADDING THE CLASS PARTITION TO THE CONDITION
        root.parent = Node("AND")
        Node(class_partition_rsc, parent=root.parent)
        expression, f_tree = getExpressionAndTree(root.parent)

    formulation_code = Rsc.ga_resource_ttl(F"SelectionFormulation-{Grl.deterministicHash(expression)}-{id}")
    check_code = Grl.deterministicHash(F"{expression}{dataset['dataset_id']}{dataset['collection_id']}")

    if check_code not in checker:
        checker[check_code] = 'in'
    else:
        return ""

    # WRITE THE RESOURCE SELECTION ID AND THE TYPE OF THE RESOURCE
    writer.write(F"\n\n### RESOURCE {id}\n")
    writer.write(F"{Rsc.ga_resource_ttl(F'ResourceSelection-{job_id}-{id}')}\n\n")
    writer.write(preVal('a', F"{Sns.VoID.dataset_ttl}, {VoidPlus.EntitySelection_ttl}"))

    # LABEL AND  DESCRIPTION IF THEY EXISTS
    if len(label.strip()) > 0:
        writer.write(preVal(Sns.RDFS.label_ttl, Literal(label).n3(MANAGER)))

    if len(description.strip()) > 0:
        writer.write(preVal(Sns.DCterms.description_ttl, Literal(description).n3(MANAGER)))

    # DATASET AND DATA-TYPE
    writer.write(preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(dataset['dataset_id'])))

    # DATASET NAME
    writer.write(preVal(Sns.DCterms.identifier_ttl, Rsc.literal_resource(dataset['name'])))

    # FORMULATION
    writer.write(preVal(VoidPlus.hasFormulation_ttl, formulation_code, end=True))

    # FORMULATION HAS CLASS PARTITION
    writer.write(F"\n\n### CLASS PARTITION OF RESOURCE {id}\n")
    writer.write(F"{class_partition_rsc}\n")
    writer.write(preVal('a', F"{VoidPlus.ClassPartition_ttl}"))
    writer.write(preVal(Sns.VoID.voidClass_ttl, Rsc.ga_resource_ttl(dataset['short_uri']), end=True))

    writer.write(F"\n\n### FORMULATION OF RESOURCE {id}\n")
    writer.write(F"{formulation_code}\n\n")
    writer.write(preVal('a', F"{VoidPlus.PartitionFormulation_ttl}"))
    writer.write(preVal(VoidPlus.hasItem_ttl, class_partition_rsc, end=True if not predicate_selections else False))

    # PREDICATE SELECTION
    writer.write(predicate_selections)

    # FORMULA EXPRESSION
    if expression:
        writer.write("\n")
        writer.write(preVal(
            VoidPlus.formulaDescription_ttl, Literal(F"{expression}").n3(MANAGER), end=False))
        writer.write("\n")
        writer.write(preVal(VoidPlus.formulaTree_ttl, Literal(F"\n{space}{f_tree}").n3(MANAGER), end=True))

    # FORMULA SEQUENCES
    writer.write(sequences)

    return writer.getvalue()


# Method for printing the linkset specs
def printSpecs(data, tab=1):

    pad = 60

    for i, (key, val) in enumerate(data.items()):

        # DICTIONARY
        if isinstance(val, dict):
            if tab == 1:
                print(F"\n{tab * space} {key} {{{i+1}/{len(data)}}}")
            else:
                print(F"{tab * space}- {key} {{{i+1}/{len(data)}}}")
            printSpecs(val, tab=tab + 1)

        # LIST OBJECT
        elif isinstance(val, (list, set)):
            if tab == 1:
                print(F"\n{tab * space} {key} [{len(val)}]")
            else:
                print(F"{tab * space}- {key} [{len(val)}]")

            for counter, item in enumerate(val):

                if isinstance(item, dict):
                    if tab == 1:
                        print(F"\n{tab * space}{space}- {key} [{counter + 1}/{len(val)}] {{{len(item)}}}")
                    else:
                        print(F"{tab * space}{space}- {key} [{counter + 1}/{len(val)}] {{{len(item)}}}")
                    printSpecs(item, tab=tab + 2)
                else:
                    print(F"{tab * space}{space}  {counter+1}. {item}")
        else:
            print(F"{tab * space}- {key:{pad - (tab - 1) * 4}}: {val}")


# CODE TO GENERATE THE FORMULA EXPRESSION OF THE FILTER LOGIC BOX OF THE SELECTED ENTITY
def filter_formula(filter_list, parent=None):

    # List of conditions
    for condition in filter_list:
        temp = Buffer()

        # New nested list of conditions
        if 'conditions' in condition:
            node = Node(GET_LOGIC_OPERATOR(condition['type']), parent=parent)
            filter_formula(condition['conditions'], parent=node)

        else:
            # Sequence for generating the resource hash code
            sequence = rdfSequence(
                condition[Vars.short_properties]
                if Vars.short_properties in condition and len(condition[Vars.short_properties]) > 0
                else condition[Vars.long_properties]
                if Vars.long_properties in condition else condition[Vars.filterProperty])

            # print(item[Vars.filterProperty], sequence[1])
            seq_function = condition[Vars.filterType] if Vars.filterType in condition else ""
            seq_value = condition[Vars.filterValue] if Vars.filterValue in condition else ""
            seq_format = condition[Vars.format] if Vars.format in condition else ""

            new_info = len(seq_function) > 0 or len(seq_value) > 0 or len(seq_format) > 0

            if new_info is True:

                # THE FILTER FUNCTION
                if len(seq_function) > 0:
                    temp.write(
                        preVal(VoidPlus.filterFunction_ttl, Literal(seq_function, lang='en').n3(MANAGER)))

                # THE FILTER VALUE
                if len(str(seq_value)) > 0:
                    temp.write(preVal(VoidPlus.filterValue_ttl, Literal(seq_value).n3(MANAGER)))

                # THE FILTER FORMAT TO APPLY
                if len(seq_format) > 0:
                    temp.write(preVal(VoidPlus.filterFormat_ttl, Literal(seq_format).n3(MANAGER)))

            code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(sequence[0] + temp.getvalue())}")

            Node(code, parent=parent)


# CODE TO GENERATE THE FORMULA EXPRESSION OF THE METHOD'S LOGIC BOX
def method_formula(filter_list, parent=None):

    # List of conditions
    for condition in filter_list:

        # New nested list of conditions
        if 'conditions' in condition:
            # recursive call
            t_value = condition['threshold'] if 'threshold' in condition else 0
            cur_threshold = "" if t_value == 0 else (F"[with sim ≥ {t_value}]" if t_value < 1 else F"= {t_value}")
            method_formula(
                condition['conditions'], parent=Node(
                    F"{GET_LOGIC_OPERATOR(condition['type'])} {cur_threshold}", parent=parent))

        else:

            ttl_algorithm = condition['method']['name'].split(":")

            # THE ALGORITHM CONDITION URI
            seq_code = F"{ttl_algorithm[1]}-{Grl.deterministicHash(condition)}" \
                if len(ttl_algorithm) > 1 else F"{condition['method']['name']}-{Grl.deterministicHash(condition)}"

            code = Rsc.ga_resource_ttl(F"{seq_code}")
            Node(code, parent=parent)


# THE UNBOXING OF THE LINKSET SPECIFICATIONS
def unboxingLinksetSpecs(specs: dict, prefixes: dict, triples: bool = True):

    formula_parts = set()
    linkset_buffer = Buffer()
    checker = defaultdict(str)
    job_code = specs[Vars.linksetSpecs][Vars.job_id]
    linkset_id = specs[Vars.linksetSpecs][Vars.id]

    def header(x, lines=2):
        liner = "\n"
        return F"{liner * lines}{'#'*80:^110}\n{' '*15}#{x:^78}#\n{'#'*80:^110}{liner * (lines-1)}"

    formula_uri_place_holder = F"LinksetFormulation-###FORMULA URI###-{linkset_id}"
    methods_descriptions = Buffer()
    methods_descriptions.write(header("METHODS'S DESCRIPTION", lines=2))

    def genericStats(linksetStats: dict):

        stats = Buffer()
        stats.write(F"\n{space}### VOID LINKSET STATS\n")

        if Vars.triples in linksetStats and linksetStats[Vars.triples] and linksetStats[Vars.triples] > -1:
            stats.write(preVal(Sns.VoID.triples_ttl, linksetStats[Vars.triples]))

        if Vars.entities in linksetStats and linksetStats[Vars.entities] and linksetStats[Vars.entities] > -1:
            stats.write(preVal(Sns.VoID.entities_ttl, linksetStats[Vars.entities]))

        if Vars.distinctSub in linksetStats and linksetStats[Vars.distinctSub] and linksetStats[Vars.distinctSub] > -1:
            stats.write(preVal(Sns.VoID.distinctSubjects_ttl, linksetStats[Vars.distinctSub]))

        if Vars.distinctObj in linksetStats and linksetStats[Vars.distinctObj] and linksetStats[Vars.distinctObj] > -1:
            stats.write(preVal(Sns.VoID.distinctObjects_ttl, linksetStats[Vars.distinctObj]))

        stats.write(F"\n{space}### LENTICULAR LENS LINKSET STATS\n")

        if Vars.clusters in linksetStats and linksetStats[Vars.clusters] and linksetStats[Vars.clusters] > -1:
            stats.write(preVal(VoidPlus.cluster_ttl, linksetStats[Vars.clusters]))

        if Vars.validations in linksetStats and linksetStats[Vars.validations] and linksetStats[Vars.validations] > -1:
            stats.write(preVal(VoidPlus.validations_tt, linksetStats[Vars.validations]))

        if Vars.remains in linksetStats and linksetStats[Vars.remains] and linksetStats[Vars.remains] > -1:
            stats.write(preVal(VoidPlus.remains_ttl, linksetStats[Vars.remains]))

        if Vars.contradictions in linksetStats and linksetStats[Vars.contradictions] and linksetStats[Vars.contradictions] > -1:
            stats.write(preVal(VoidPlus.contradictions_tt, linksetStats[Vars.contradictions]))

        stats.write("\n")

        return stats.getvalue()

    # Generic description of a linkset/les
    def genericDes(job_id: str, linksetSpecs: dict):

        g_meta = Buffer()
        g_meta.write(header('GENERIC METADATA', lines=2))

        # 1. The LINKSET'S NAME OR ID
        # linkset_id = linksetSpecs[Vars.id]
        g_meta.write(F"\n\n### JOB ID       : {job_code}\n")
        g_meta.write(F"### LINKSET ID   : {linkset_id}\n")
        g_meta.write(F"linkset:{job_code}-{linkset_id}\n\n")
        # g_meta.write(preVal('a', Sns.VoID.linkset_ttl))
        g_meta.write(preVal('a', VoidPlus.Linkset_ttl))

        # LINKSET FORMAT (TURTLE)
        g_meta.write(preVal(Sns.VoID.feature_ttl, F"{Sns.Formats.turtle_ttl}, {Sns.Formats.triG_ttl}"))

        # NAME ATTRIBUTION
        g_meta.write(preVal(Sns.CC.attributionName_ttl, Literal('LenticularLens', 'en').n3()))

        # LICENCE OF THE LL
        g_meta.write(preVal(Sns.CC.license_ttl, Rsc.uri_resource(Vars.LICENCE)))

        # LINKSET TIMESTAMP
        g_meta.write(preVal(Sns.DCterms.created_ttl, Grl.getXSDTimestamp()))

        if "creator" in linksetSpecs and len(linksetSpecs["creator"].strip()) > 0:
            g_meta.write(preVal(Sns.DCterms.creator_ttl, Literal(linksetSpecs["creator"]).n3()))

        if "publisher" in linksetSpecs and len(linksetSpecs["publisher"].strip()) > 0:
            g_meta.write(preVal(Sns.DCterms.creator_ttl, Literal(linksetSpecs["publisher"]).n3()))

        # LINKSET LINK-TYPE
        g_meta.write(preVal(Sns.VoID.linkPredicate_tt, linksetSpecs[Vars.linkType]))

        # 2. USER'S LABEL
        if len(Literal(linksetSpecs[Vars.label].strip())) > 0:
            g_meta.write(preVal(Sns.RDFS.label_ttl, Literal(linksetSpecs[Vars.label]).n3()))

        # 3. LINKSET DESCRIPTION
        if Vars.description in linksetSpecs and len(Literal(linksetSpecs[Vars.description].strip())) > 0:
            g_meta.write(preVal(
                Sns.DCterms.description_ttl, Literal(linksetSpecs[Vars.description]).n3()))
            g_meta.write("\n")

        # LINKSET STATS
        g_meta.write(genericStats(specs[Vars.linksetStats]))

        # 4. SELECTED ENTITY AT THE SOURCE
        g_meta.write(F"{space}### SOURCE ENTITY TYPE SELECTION(S)\n")
        g_meta.write("".join(preVal(
            VoidPlus.subTarget_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{job_id}-{selection[Vars.id]}"))
                             for selection in linksetSpecs[Vars.sources]))

        g_meta.write(F"\n{space}### TARGET ENTITY TYPE SELECTION(S)\n")
        g_meta.write("".join(preVal(
            VoidPlus.objTarget_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{job_id}-{selection[Vars.id]}"))
                             for selection in linksetSpecs[Vars.targets]))

        # LOGIC FORMULATION
        g_meta.write(F"\n{space}### THE LOGIC FORMULA\n")
        g_meta.write(preVal(VoidPlus.formulation_ttl, Rsc.ga_resource_ttl(formula_uri_place_holder), end=True))

        # return F"{g_meta.getvalue().rstrip()[:-1]}.\n\n"
        return g_meta.getvalue()

    # Documentation of the selected resource by unboxing the collection filter
    def resourceSelection(linksetSpecs):

        entity_constraints = Buffer()
        entity_constraints.write(F"{header('RESOURCE SELECTIONS')}")

        # AT THE SOURCE OR TARGET, THERE CAN EXIST MORE THAN ONE SELECTED RESOURCE
        for logic_box in linksetSpecs[Vars.sources]:

            filter_triples = unboxingFilterBox(job_code, logic_box, checker)
            if filter_triples not in checker:
                checker[filter_triples] = "in"
                entity_constraints.write(filter_triples)

        # Source selected at the target
        if linksetSpecs[Vars.sources] != linksetSpecs[Vars.targets]:
            for logic_box in linksetSpecs[Vars.targets]:
                filter_triples = unboxingFilterBox(job_code, logic_box, checker)
                if filter_triples not in checker:
                    checker[filter_triples] = "in"
                    entity_constraints.write(F"{filter_triples}")

        return F"{entity_constraints.getvalue().rstrip()[:-1]}.\n"

    # ### METHOD SPECIFICATIONS --- ### SOURCE
    # ADDRESSING EACH ALGORITHM IN THE METHOD
    def unboxingAlgorithm(job_id: str, method: dict):

        # print(method['list_matching'])
        algor_writer = Buffer()
        p_sel_writer = Buffer()
        p_sequences_writer = Buffer()
        algor_name = method['method'][Vars.methodName]
        algor_sequence = Buffer()
        algorithm_seq_triple = None
        main_threshold = method['method']['config']['threshold'] if 'threshold' in method['method']['config'] else None

        # ALGORITHM SIMILARITY CONFIGURATION
        sim_config = method['sim_method']
        sim_name = method['sim_method'][Vars.methodName]
        sim_normalized = method['sim_method'][Vars.normalized]

        # DATA ON SET MATCHING
        matching_list = method['list_matching']
        active_matching_list = True if matching_list['threshold'] > 0 else False

        # DATA ON ALGORITHM CONFIGURATION
        method_config = method['method']

        # NAME COMPATIBILITY
        algor_name = Algorithm.exact_ttl if algor_name == "=" else algor_name

        tad_algor = algor_name.split(":")

        # THE ALGORITHM CONDITION URI
        seq_code = F"{tad_algor[1]}-{Grl.deterministicHash(method)}" \
            if len(tad_algor) > 1 else F"{algor_name}-{Grl.deterministicHash(method)}"

        # ALGORITHM DESCRIPTION
        if algor_name not in checker:
            checker[algor_name] = 'i'
            methods_descriptions.write(F"\n\n### ALGORITHM : {algor_name}")
            methods_descriptions.write(F"\n{Rsc.ga_resource_ttl(algor_name)}\n\n")
            methods_descriptions.write(preVal('a', VoidPlus.MatchingAlgorithm_ttl))
            methods_descriptions.write(preVal(Sns.DCterms.description_ttl, Algorithm.illustration(algor_name), end=True))

        algor_writer.write(F"\n\n### METHOD SPECIFICATIONS {algor_name}\n")
        algor_writer.write(F"{Rsc.ga_resource_ttl(seq_code)}\n\n")
        algor_writer.write(preVal('a', VoidPlus.MatchingMethod_ttl))

        # ALGORITHM NAME (hasAlgorithm)
        if sim_name:
            algor_sequence.write(
                F"\n{space * 2}[\n"
                F"{space * 3}### MAIN ALGORITHM\n"
                F"{space * 3}{VoidPlus.method_ttl:{Vars.PRED_SIZE - 8}}{Rsc.ga_resource_ttl(algor_name)} ;\n")
            algor_writer.write(preVal(VoidPlus.methodSequence_ttl, "### ALGORITHM SEQUENCE"))
        else:
            algor_writer.write(preVal(VoidPlus.method_ttl, Rsc.ga_resource_ttl(algor_name)))

        # ALGORITHM OPERATOR
        if Vars.threshold_operator in method:
            algor_writer.write(preVal(VoidPlus.simOperator_ttl, Rsc.ga_resource_ttl(method[Vars.threshold_operator])))

        # #########################################################
        # 1. METHOD CONFIGURATION
        # #########################################################

        # THRESHOLD RANGE OF THE EXACT METHOD
        if algor_name.lower() == "exact":
            algor_writer.write(preVal(VoidPlus.thresholdRange_ttl, Literal(Algorithm.range(algor_name)).n3(MANAGER)))

        # IN CASE OF MULTIPLE PROPERTIES SELECTED FOR A MATCHING ALGORITHM, THE USER CAN ASSIGN AN S-NORM THRESHOLD
        if 'threshold' in method and method['threshold'] > 0 and algor_name.lower() != "exact":
            algor_writer.write(preVal(VoidPlus.combiThreshold_ttl, Literal(method['threshold']).n3(MANAGER)))
            algor_writer.write(preVal(VoidPlus.combiThresholdRange_ttl,
                                      Literal(Algorithm.range('interval')).n3(MANAGER)))

        if method_config and not sim_name:

            # Threshold for Levenshtein Normalised - Jaro - Winkler - Trigram
            # ALGORITHM THRESHOLD RANGE
            if 'threshold' in method_config['config']:
                # Jaro Winkler prefix weight
                if 'prefix_weight' in method_config['config']:
                    algor_writer.write(
                        preVal("voidPlus:jaroWinklerPrefixWeight",
                               Literal(method_config['config'][Vars.prefix_weight]).n3(Graph().namespace_manager)))
                algor_writer.write(preVal(VoidPlus.simThreshold_ttl, Literal(method_config['config'][Vars.threshold]).n3(MANAGER)))
                algor_writer.write(preVal(VoidPlus.thresholdRange_ttl, Literal(Algorithm.range(algor_name)).n3(MANAGER)))

            # Levenshtein distance max size
            if 'max_distance' in method_config['config']:
                algor_writer.write(
                    preVal("voidPlus:maxDistance", Literal(method_config['config'][Vars.max_distance]).n3(MANAGER)))
                algor_writer.write(preVal(VoidPlus.thresholdRange_ttl, Literal(Algorithm.range(algor_name)).n3(MANAGER)))

            if 'size' in method_config['config']:
                algor_writer.write(
                    preVal("voidPlus:soundexSize", Literal(method_config['config'][Vars.soundex_size]).n3(MANAGER)))

            if 'name_type' in method_config['config']:
                algor_writer.write(preVal("voidPlus:BloothooftNameType",
                                          Literal(method_config['config'][Vars.Bloothooft_name_type]).n3(MANAGER)))

            if 'date_part' in method_config['config']:
                unit = Sns.Time.get_uri_ttl(method_config['config']['date_part']) \
                    if method_config['config']['date_part'].lower() != 'year_month' \
                    else F"{Sns.Time.get_uri_ttl('month')}, {Sns.Time.get_uri_ttl('year')}"

                algor_writer.write(preVal(Sns.Time.unitType_ttl, unit))

                prefixes[Sns.Time.time] = "time"

        # THIS IS A SEQUENCE OF ALGORITHMS FOR THIS METHOD
        else:

            if 'threshold' in method_config['config']:

                # Jaro Winkler prefix weight
                if 'prefix_weight' in method_config['config']:
                    algor_sequence.write(
                        F"{space * 3}{'voidPlus:jaroWinklerPrefixWeight':{Vars.PRED_SIZE}}"
                        F"{Literal(method_config['config'][Vars.prefix_weight]).n3(MANAGER)} ;\n")

                algor_sequence.write(
                    F"{space * 3}{VoidPlus.simThreshold_ttl:{Vars.PRED_SIZE}}"
                    F"{Literal(method_config['config'][Vars.threshold]).n3(MANAGER)} ;\n")

                algor_sequence.write(
                    F"{space * 3}{VoidPlus.thresholdRange_ttl:{Vars.PRED_SIZE}}"
                    F"{Literal(Algorithm.range(algor_name)).n3(MANAGER)} ;\n")

            # Levenshtein distance max size
            if 'max_distance' in method_config['config']:
                algor_sequence.write(
                    F"{space * 3}{'voidPlus:maxDistance':{Vars.PRED_SIZE}}"
                    F"{Literal(method_config['config'][Vars.max_distance]).n3(MANAGER)} ;\n")

                algor_sequence.write(
                    F"{space * 3}{VoidPlus.thresholdRange_ttl:{Vars.PRED_SIZE}}"
                    F"{Literal(Algorithm.range(algor_name)).n3(MANAGER)} ;\n")

            if 'size' in method_config['config']:
                algor_sequence.write(
                    preVal(F"{space * 2}{'voidPlus:soundexSize'}",
                           Literal(method_config['config'][Vars.soundex_size]).n3(MANAGER)))

            if 'name_type' in method_config['config']:
                algor_sequence.write(
                    preVal(F"{space * 2}{'voidPlus:BloothooftNameType'}",
                           Literal(method_config['config'][Vars.Bloothooft_name_type]).n3(MANAGER)))

            algor_sequence.write(F"{space * 2}]")

        # #########################################################
        # MATCHING LIST SPECS
        # #########################################################
        appreciation, appreciation_desc = None, None
        is_percentage = matching_list['is_percentage']
        list_threshold = matching_list['threshold']

        if active_matching_list is True:

            appreciation = "RelativeCount" if is_percentage else "AbsoluteCount"
            appreciation_desc = "Establishes a link when the percentage threshold is reached." \
                if is_percentage \
                else "Establishes a link between the source and target when the absolute threshold is reached."

            algor_writer.write(F"\n{space}### SET MATCHING CONFIGURATION\n")
            algor_writer.write(F"\n{space}{'voidPlus:hasListConfiguration':{Vars.PRED_SIZE}}\n{space * 2}[\n")
            algor_writer.write(preVal(F"{space * 2}voidPlus:listThreshold", Literal(list_threshold).n3(MANAGER)))
            algor_writer.write(preVal(F"{space * 2}voidPlus:appreciation", Rsc.ga_resource_ttl(appreciation)))
            # algor_writer.write(preVal(F"{tab * 2}voidPlus:appreciation", Rsc.ga_resource_ttl(appreciation_unique), end=False))
            algor_writer.write(F"{space * 2}] ;\n")

        # #########################################################
        # SIMILARITY ALGORITHM CONFIGURATION
        # #########################################################
        # SEQUENCE OF ALGORITHMS METHOD CONFIGURATION
        if sim_name:

            sequencer = [algor_sequence.getvalue()]
            resetBuffer(algor_sequence, '')
            algor_sequence.write(F"\n{space * 2}[\n{space * 3}### SUB-SIMILARITY ALGORITHM CONFIGURATION\n")

            # ALGORITHM'S NAME
            algor_sequence.write(preVal(F"{space * 2}{VoidPlus.method_ttl}", Rsc.ga_resource_ttl(sim_name)))

            # WHETHER OR NOT THE SUB-MATCHING ALGORITHM IS RUN OVER THE NORMALISED OR THE ACTUAL VALUES
            algor_sequence.write(preVal(F"{space * 2}voidPlus:isAppliedOnEncodedValues", Literal(sim_normalized).n3(MANAGER)))

            # SUB ALGORITHM'S THRESHOLD
            algor_sequence.write(
                preVal(F"{space * 2}{VoidPlus.simThreshold_ttl}",
                       Literal(method['sim_method']['config'][Vars.threshold]).n3(MANAGER)))

            # MAX DISTANCE FOR SPECIFIC ALGORITHMS
            if 'max_distance' in sim_config:

                algor_sequence.write(
                    preVal(F"{space * 2}voidPlus:maxDistance", Literal(sim_config[Vars.max_distance]).n3(MANAGER)))

                algor_sequence.write(
                    preVal(F"{space * 2}{VoidPlus.thresholdRange_ttl}", Literal(Algorithm.range(sim_name)).n3(MANAGER)))

            algor_sequence.write(F"{space * 2}]")

            sequencer.append(algor_sequence.getvalue())
            algorithm_seq_triple = rdfSAlgorithmSequence(sequencer)

        # #########################################################
        #            EXECUTING THE METHOD'S SIGNATURE]            #
        # #########################################################

        def entitySelections(method_cont, subject=True):

            buffer = Buffer()
            sources = method[method_cont]
            property_sel_formulation = Buffer()
            formulation_code = Grl.deterministicHash(sources)

            # LIST OF SOURCE PROPERTIES SELECTIONS
            # THE METHODS SOURCE AND TARGET PARTITIONS
            algor_writer.write(F"\n{space}### {algor_name} SOURCE PREDICATE(S) CONFIGURATION\n"
                               if subject is True else F"\n{space}### {algor_name} TARGET PREDICATE CONFIGURATION(S)\n")

            # HAS SUB/OBJ RESOURCE SELECTION
            predicate_type = VoidPlus.entitySelectionSubj_ttl if subject is True else VoidPlus.entitySelectionObj_ttl
            algor_writer.write(preVal(predicate_type, Rsc.ga_resource_ttl(F"ResourcePartition-{formulation_code}")))

            # FOR COLLECTING SELECTED PROPERTIES FOR A GIVEN RESOURCE SELECTION (ENTITY TYPE)
            group_check = defaultdict(dict)

            # ABOUT THE SELECTED  FROM THE LIST OF CONDITIONS
            for identifier, selection in sources['properties'].items():

                for item in selection:

                    transformer = item['transformers']
                    # stop_word_dictionary = item["stopwords"]["dictionary"]
                    # stop_word_additional = F'{" ".join(item["stopwords"]["additional"])}'

                    ent_sel_id = identifier
                    ent_sel = F"{RSC_SELECTION[int(ent_sel_id)]['collection_id']} {RSC_SELECTION[int(ent_sel_id)]['short_uri']}"
                    rsc_sel_code = F"ResourceSelection-{job_id}-{ent_sel}"

                    # THE SELECTED PROPERTY IS A PROPERTY PATH
                    if len(item[Vars.property]) > 1:

                        # GET THE PROPERTY PATH SEQUENCE AND ITS URI
                        # src_sequence = rdfSequence(item[Vars.property])
                        src_sequence = rdfSequence(item[Vars.short_properties]
                                                   if len(item[Vars.short_properties]) > 0
                                                   else item[Vars.long_properties], only=True)

                        seq_code = Grl.deterministicHash(F"{src_sequence[1]}{transformer}")

                        # WRITING THE SEQUENCE
                        if seq_code not in checker:

                            checker[seq_code] = str(src_sequence[0])

                            p_sequences_writer.write(F"\n\n{src_sequence[0].rstrip()}\n")
                            p_sequences_writer.write(
                                preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(rsc_sel_code), end=True))

                        if ent_sel_id not in group_check:
                            group_check[ent_sel_id] = {
                                'code': seq_code,
                                'predicates': [
                                    {
                                        'property': str(src_sequence[0]),
                                        # 'stop_lang': stop_word_dictionary,
                                        # 'stop_add': stop_word_additional,
                                        'transformer': transformer
                                    }
                                ]
                            }

                        else:
                            group_check[ent_sel_id]['predicates'].append(
                                {
                                    'property': str(src_sequence[0]),
                                    # 'stop_lang': stop_word_dictionary,
                                    # 'stop_add': stop_word_additional,
                                    'transformer': transformer
                                }
                            )

                    # A SINGLE PROPERTY
                    else:

                        # For several properties selected for the same entity selection
                        if ent_sel_id not in group_check:

                            # the has code for creating a URI: entity type selection ID + the property
                            selection_code = Grl.deterministicHash(F"{ent_sel}{item[Vars.property][0]}{transformer}")
                            # For this entity selection, register its uri code and all selected properties
                            group_check[ent_sel_id] = {
                                'code': selection_code,
                                'predicates': [
                                    {
                                        'property': item[Vars.property][0] if 'short_properties' not in item else
                                            item['short_properties'][0],
                                        # 'stop_lang': stop_word_dictionary,
                                        # 'stop_add': stop_word_additional,
                                        'transformer': transformer
                                    }
                                ]
                            }

                        else:
                            # the recall of the code makes sure that the sequence is not recreated
                            group_check[ent_sel_id]['predicates'].append(
                                {
                                    'property': item[Vars.property][0] if 'short_properties' not in item else item[
                                        'short_properties'][0],
                                    # 'stop_lang': stop_word_dictionary,
                                    # 'stop_add': stop_word_additional,
                                    'transformer': transformer
                                }
                            )

            # #############################################
            #     PREDICATES SELECTED FOR A METHOD        #
            # #############################################
            root = Node("OR")
            if 'fuzzy' in method:

                operator = GET_LOGIC_OPERATOR(method['fuzzy']['t_conorm'] if method['fuzzy']['t_conorm'] else "OR")

                fuzzy_threshold = method['fuzzy']['threshold']
                cur_threshold = "" if fuzzy_threshold == 0 or fuzzy_threshold is None else (
                    F"[with sim ≥ {fuzzy_threshold}]" if fuzzy_threshold < 1 else F"[with sim = {fuzzy_threshold}]")

                root = Node(F"{operator}{F' {cur_threshold}'}") \
                    if len(group_check) > 1 or \
                       (len(group_check) == 1 and len(list(group_check.values())[0]['predicates']) > 1) \
                    else Node('')

            if formulation_code not in checker:

                checker[formulation_code] = ''

                # COMMENT FOR SOURCE OR TARGET PROPERTY SELECTION FORMULATION
                property_sel_formulation.write(F"\n\n### {algor_name} {'SOURCE' if subject is True else 'TARGET'}"
                                               F" PROPERTY SELECTION FORMULATION\n")

                # THE PARTITION FORMULATION
                property_sel_formulation.write(F"""{Rsc.ga_resource_ttl(F'PartitionFormulation-{formulation_code}')}\n""")

                # A TYPE OF PROPERTY PARTITION FORMULATION
                property_sel_formulation.write(preVal('a', VoidPlus.PartitionFormulation_ttl))

                # #############################################
                #             RESOURCE PARTITIONS             #
                # #############################################

                # PARTITIONED RESOURCE
                partitioned_uri = F"""{Rsc.ga_resource_ttl(F'ResourcePartition-{formulation_code}')}\n"""

                if partitioned_uri not in checker:

                    checker[partitioned_uri] = ''

                    p_sel_writer.write(F"\n\n### {algor_name} {'SOURCE' if subject is True else 'TARGET'} "
                                       F" MATCHING PARTITION ({'S'if subject is True else 'T'}-{ent_sel_id})\n")
                    p_sel_writer.write(partitioned_uri)
                    p_sel_writer.write(preVal('a', VoidPlus.EntitySelection_ttl))

                    # SEQUENCE / FORMULATION
                    p_sel_writer.write(
                        preVal(VoidPlus.hasFormulation_ttl, Rsc.ga_resource_ttl(F'PartitionFormulation-{formulation_code}'),
                               end=True))

                for n, (ent_sel_id, data) in enumerate(group_check.items()):

                    # THE DETAIL OF THE SELECTED PROPERTIES
                    for i, predicate in enumerate(data['predicates']):

                        feature = predicate['property']

                        transformers = predicate['transformer']

                        part_code = F'PropertyPartition-{Grl.deterministicHash(F"{ent_sel}{feature}{transformers}")}'

                        # PROPERTY PARTITION FORMULATION HAS ITEM
                        property_sel_formulation.write(preVal(VoidPlus.hasItem_ttl, Rsc.ga_resource_ttl(part_code)))

                        # APPENDING TO TGHE ROOT TYREE
                        Node(Rsc.ga_resource_ttl(part_code), parent=root)

                        if part_code not in checker:

                            checker[part_code] = 'in'

                            buffer.write(F"### {algor_name} DETAIL ON {'SOURCE' if subject is True else 'TARGET'} "
                                         F"PROPERTY SELECTION ({'S'if subject is True else 'T'}-{ent_sel_id}-{i+1})\n")

                            # THE PARTITIONED RESOURCE
                            buffer.write(F"{Rsc.ga_resource_ttl(part_code)}\n")

                            # THE PROPERTY PARTITION TYPE IS ALREADY IN THE SEQUENCE ==-> CONDITIONAL
                            buffer.write(
                                preVal('a', VoidPlus.PropertyPartition_ttl)
                                if 'VoidPlus:PropertyPartition' not in feature else '')

                            buffer.write(
                                preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{ent_sel_id}")))

                            stopwords_buffer = Buffer()
                            if transformers:
                                for transform in transformers:

                                    # A TRANSFORMER FUNCTION
                                    if transform['name'].lower() != "stopwords":
                                        buffer.write(
                                            preVal("voidPlus:hasTransformationFunction",
                                                   Literal(transform['name'], lang='en').n3(MANAGER), end=False))

                                        if transform['parameters']:
                                            buffer.write(preVal("voidPlus:hasTransformationParameters",
                                                                Literal(transform['parameters']).n3(MANAGER), end=False))

                                    # LIST OF STOPWORDS
                                    else:

                                        # FETCH THE LIST OF STOPWORDS
                                        link = F"https://recon.diginfra.net/stopwords/{transform['parameters']['dictionary']}"
                                        try:
                                            stopwords = requests.get(link).json()
                                        except Exception as err:
                                            stopwords = None

                                        if stopwords:

                                            new = "\n\t\t"
                                            language = transform['parameters']['dictionary'].lower().split('_')[0]
                                            stopwords_code = Grl.deterministicHash(stopwords)
                                            resource = Rsc.ga_resource_ttl(F"{language[0].upper()}{language[1:]}-StopwordsList-{stopwords_code}")

                                            # REFORMAT THE STOPWORDS
                                            stopwords = F", ".join(F"{new if i%10 == 0 else ''}{Literal(word).n3(MANAGER)}" for i, word in enumerate(stopwords))
                                            buffer.write(preVal("voidPlus:stopWords", resource, end=False))

                                            if stopwords_code not in checker:

                                                checker[stopwords_code] = 'in'
                                                stopwords_buffer.write(F"\n\n### STOPWORDS IN {transform['parameters']['dictionary'].upper()}\n")
                                                stopwords_buffer.write(F"{resource}\n")

                                                # ADD ISO-1 CODE RESOURCE
                                                iso369 = language_code.get_iso369_1_ttl_uri(
                                                    Country.iso_639_1[language] if language in Country.iso_639_1 else language)

                                                prefixes[Sns.ISO.iso3166_1] = Sns.ISO.prefix_code
                                                stopwords_buffer.write(
                                                    preVal(Sns.DC.language_ttl,
                                                           iso369 if iso369 else Literal(language).n3(), end=False))

                                                stopwords_buffer.write(
                                                    preVal("voidPlus:stopWordsList", stopwords, end=True))

                                                # UPDATE THE USE OF A NEW NAMESPACE
                                                prefixes[Sns.DC.dc] = "dc"

                                        # ADDITIONAL STOPWORDS
                                        if transform['parameters']['additional']:
                                            stopwords_code = Grl.deterministicHash(transform['parameters']['additional'])
                                            resource = Rsc.ga_resource_ttl(F"StopwordsList-{stopwords_code}")
                                            stopwords = F", ".join(
                                                F"{new if i % 10 == 0 else ''}{Literal(word).n3(MANAGER)}" for i, word
                                                in enumerate(transform['parameters']['additional']))
                                            buffer.write(preVal("voidPlus:stopWords", resource, end=False))

                                            if stopwords_code not in checker:
                                                checker[stopwords_code] = 'in'
                                                stopwords_buffer.write(F"\n\n### ADDITIONAL STOPWORDS\n")
                                                stopwords_buffer.write(F"{resource}\n")
                                                stopwords_buffer.write(
                                                    preVal("voidPlus:stopWordsList", stopwords, end=True))

                            # THE PREDICATE
                            buffer.write(preVal(Sns.VoID.property_ttl, feature, end=True))

                            # THE STOPWORDS
                            buffer.write(stopwords_buffer.getvalue())

                            buffer.write("\n\n")

                # #############################################
                #       FORMULA EXPRESSION AND TREE           #
                # #############################################
                f_expression, f_tree = getExpressionAndTree(root)

                property_sel_formulation.write(
                    preVal(VoidPlus.formulaDescription_ttl, Literal(f_expression).n3(MANAGER)))

                property_sel_formulation.write(
                    preVal(VoidPlus.formulaTree_ttl, Literal(F"\n{space}{f_tree}").n3(MANAGER), end=True))

                p_sel_writer.write(property_sel_formulation.getvalue() + "\n\n")
                p_sel_writer.write(buffer.getvalue())

                clearBuffer(buffer)

        entitySelections(Vars.sources, subject=True)
        entitySelections(Vars.targets, subject=False)

        # #########################################################
        #       ADDING INTERMEDIATE TO THE METHODS SIGNATURE      #
        # #########################################################

        def intermediateSelections(method_configuration):

            rsc = {}
            buffer = Buffer()
            property_sel_buffer = Buffer()

            # # FOR COLLECTING SELECTED PROPERTIES FOR A GIVEN RESOURCE SELECTION (ENTITY TYPE)
            # group_check = defaultdict(dict)

            ent_sel_id = method_configuration['config'][Vars.entityTypeSelection]
            ent_type = method_configuration['config'][ent_sel_id]['dataset']['collection_id']
            dataset = method_configuration['config'][ent_sel_id]['dataset']['dataset_id']
            rsc_sel_code = F"ResourceSelection-{job_id}-{ent_sel_id}"

            # ABOUT THE SELECTED PROPERTIES
            for idx, source_target in enumerate(["intermediate_source", "intermediate_target"]):

                # FOR COLLECTING SELECTED PROPERTIES FOR A GIVEN RESOURCE SELECTION (ENTITY TYPE)
                group_check = defaultdict(dict)

                formulation_code = Grl.deterministicHash(
                    F"{dataset}{ent_type}{source_target}")

                rsc['source' if idx == 0 else 'target'] = formulation_code

                short_key = 'short_intermediate_source' if idx == 0 else 'short_intermediate_target'
                long_key = 'long_intermediate_source' if idx == 0 else 'long_intermediate_target'
                properties = method_configuration['config'][source_target]

                for feature in properties:

                    # THE SELECTED PROPERTY IS A PROPERTY PATH
                    if len(feature) > 1:
                        # print(method_configuration)
                        # GET THE PROPERTY PATH SEQUENCE AND ITS URI
                        # src_sequence = rdfSequence(item[Vars.property])
                        src_sequence = rdfSequence(
                            feature if len(method_configuration['config'][short_key]) > 0
                            else method_configuration['config'][long_key], only=True)

                        # WRITING THE SEQUENCE
                        if src_sequence[1] not in checker:
                            p_sequences_writer.write(F"\n\n{src_sequence[0].rstrip()}\n")
                            p_sequences_writer.write(
                                preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(rsc_sel_code), end=True))
                            checker[src_sequence[1]] = str(src_sequence[0])

                        if ent_sel_id not in group_check:
                            group_check[ent_sel_id] = {'code': src_sequence[1], 'predicates': [str(src_sequence[0])]}
                        else:
                            group_check[ent_sel_id]['predicates'].append(str(src_sequence[0]))

                    # A SINGLE PROPERTY
                    else:

                        # For several properties selected for the same entity selection
                        if ent_sel_id not in group_check:

                            # the has code for creating a URI: entity type selection ID + the property
                            selection_code = Grl.deterministicHash(F"{dataset}{ent_type}{feature[0]}")
                            # For this entity selection, register its uri code and all selected properties
                            group_check[ent_sel_id] = {
                                'code': selection_code,
                                'predicates': [feature[0]] if short_key not in method_configuration['config']
                                else [method_configuration['config'][short_key][0]]}

                        else:
                            # the recall of the code makes sure that the sequence is not recreated

                            group_check[ent_sel_id]['predicates'].append(
                                feature[0] if short_key not in method_configuration['config']
                                else method_configuration['config'][short_key][0])

                # #############################################
                #     PREDICATES SELECTED FOR A METHOD        #
                # #############################################

                operator = GET_LOGIC_OPERATOR(method['fuzzy']['t_conorm'] if method['fuzzy']['t_conorm'] else "OR")

                root = Node(F"{operator} ≥{main_threshold}") \
                    if len(group_check) > 1 or \
                       (len(group_check) == 1 and len(list(group_check.values())[0]['predicates']) > 1) \
                    else Node('')

                if formulation_code not in checker:
                    checker[formulation_code] = ''
                    property_sel_buffer.write(F"\n\n### *** {algor_name} DATASET *** {'SOURCE' if idx == 0 else 'TARGET'}"
                                                   F" FORMULATION OF SELECTED PROPERTIES\n")

                    # THE PARTITION FORMULATION
                    property_sel_buffer.write(F"""{Rsc.ga_resource_ttl(F'PartitionFormulation-{formulation_code}')}\n""")
                    property_sel_buffer.write(preVal('a', VoidPlus.PartitionFormulation_ttl))

                    # #############################################
                    #             RESOURCE PARTITIONS             #
                    # #############################################

                    # PORTIONED RESOURCE
                    partitioned_uri = F"""{Rsc.ga_resource_ttl(F'ResourcePartition-{formulation_code}')}\n"""
                    if partitioned_uri not in checker:
                        checker[partitioned_uri] = ''

                        p_sel_writer.write(F"\n### *** {algor_name} DATASET *** {'SOURCE' if idx == 0 else 'TARGET'}"
                                           F" METHOD'S MATCHING PARTITION ({ent_sel_id})\n")
                        p_sel_writer.write(partitioned_uri)
                        p_sel_writer.write(preVal('a', VoidPlus.EntitySelection_ttl))

                        # SEQUENCE / FORMULATION
                        p_sel_writer.write(
                            preVal(VoidPlus.hasFormulation_ttl, Rsc.ga_resource_ttl(F'PartitionFormulation-{formulation_code}'),
                                   end=True))

                    for n, (ent_sel_id, data) in enumerate(group_check.items()):

                        # FORMULATION HAS ITEM AND PROPERTY SELECTION DETAIL
                        for i, predicate in enumerate(data['predicates']):

                            # part_code = F'PropertyPartition-{Grl.deterministicHash(F"{ent_type}{predicate}")}'
                            part_code = F'PropertyPartition-{Grl.deterministicHash(F"{ent_type}{predicate}")}'
                            property_sel_buffer.write(preVal(VoidPlus.hasItem_ttl, Rsc.ga_resource_ttl(part_code)))
                            Node(Rsc.ga_resource_ttl(part_code), parent=root)

                            if part_code not in checker:
                                checker[part_code] = 'in'

                                buffer.write(F"### *** {algor_name} DATASET *** DETAIL ON {'SOURCE' if idx == 0 else 'TARGET'} "
                                             F" SELECTED PROPERTY ({'S'if idx == 0 else 'T'}-{ent_sel_id}-{i+1})\n")
                                buffer.write(F"{Rsc.ga_resource_ttl(part_code)}\n")

                                # THE PROPERTY PARTITION TYPE IS ALREADY IN THE SEQUENCE ==-> CONDITIONAL
                                buffer.write(
                                    preVal('a', VoidPlus.PropertyPartition_ttl)
                                    if 'VoidPlus:PropertyPartition' not in predicate else '')

                                buffer.write(
                                    preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{ent_sel_id}")))
                                buffer.write(preVal(Sns.VoID.property_ttl, predicate, end=True))
                                buffer.write("\n\n")

                    # #############################################
                    #       FORMULA EXPRESSION AND TREE           #
                    # #############################################
                    f_expression, f_tree = getExpressionAndTree(root)

                    # FORMULA EXPRESSION
                    property_sel_buffer.write(
                        preVal(VoidPlus.formulaDescription_ttl, Literal(f_expression).n3(MANAGER)))

                    # FORMULA TREE
                    property_sel_buffer.write(
                        preVal(VoidPlus.formulaTree_ttl, Literal(F"\n{space}{f_tree}").n3(MANAGER), end=True))

                    p_sel_writer.write(property_sel_buffer.getvalue() + "\n\n")
                    p_sel_writer.write(buffer.getvalue())
                    clearBuffer(property_sel_buffer)
                    clearBuffer(buffer)

            return rsc
        # == END OF intermediateSelections ================ #

        if 'intermediate' in algor_name.lower():

            codes = intermediateSelections(method_config)

            # intermediate_selection_id = method['method_config']['entity_type_selection']
            # intermediate_properties = method['method_config']['intermediate_source'] + method['method_config'][
            #     'intermediate_target']

            for key, code in codes.items():
                # sel_code = Grl.deterministicHash(F"{intermediate_selection_id}{intermediate_properties}")
                algor_writer.write(F"\n{space}### {key.upper()} PREDICATE(S) CONFIGURATION OF THE INTERMEDIATE DATASET \n")
                algor_writer.write(
                    preVal(VoidPlus.intermediateEntitySelection_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{code}")))

        # #########################################################
        #       MORE INFO ON THE SET MATCHING CONFIGURATION       #
        # #########################################################
        resetBuffer(algor_writer, F"{algor_writer.getvalue().rstrip()[:-1]}.\n")

        if appreciation_desc and appreciation not in checker:
            checker[appreciation] = 'in'
            algor_writer.write("\n### DESCRIPTION OF THE SET MATCH THRESHOLDS\n")
            algor_writer.write(F"{Rsc.ga_resource_ttl(appreciation)}\n")
            algor_writer.write(preVal(Sns.DCterms.description_ttl,  Literal(appreciation_desc).n3(MANAGER), end=True))

        # if appreciation_unique_desc and appreciation_unique_desc not in checker:
        #     checker[appreciation_unique_desc] = 'in'
        #     algor_writer.write("\n### DESCRIPTION OF THE SET MATCH THRESHOLDS\n")
        #     algor_writer.write(F"{Rsc.ga_resource_ttl(appreciation_unique)}\n")
        #     algor_writer.write(preVal(Sns.DCterms.description_ttl, Literal(appreciation_unique_desc).n3(MANAGER), end=True))

        if algorithm_seq_triple:
            resetBuffer(algor_writer, algor_writer.getvalue()[:-1].replace("### ALGORITHM SEQUENCE", algorithm_seq_triple[1]))
            algor_writer.write(F"\n\n### ALGORITHM SEQUENCE\n{algorithm_seq_triple[0][:-3]} .")

        return algor_writer.getvalue(), p_sel_writer.getvalue(), p_sequences_writer.getvalue(), seq_code

    # THE COMPLETE METHOD OF THE LINKSET
    def unboxingMethodsBox(job_id: str, methodBox: dict):

        methods_signature = Buffer()
        methods_predicates = Buffer()
        # print(methodBox, "\n\n")

        methods_signature.write(header('METHOD SIGNATURES', lines=1) + "\n")
        methods_predicates.write(header("METHODS'S PREDICATE SELECTIONS", lines=2))

        counter = [0]

        def writeMethodsBox(mtdBox: dict):

            box_list = mtdBox["conditions"]

            # LIST OF BOXES OR NESTED BOXES
            codes = deque()

            expression_tree, f_expression = None, None
            if 'conditions' in mtdBox and mtdBox['conditions']:

                # The formula root tree
                t_value = mtdBox['threshold'] if 'threshold' in mtdBox else 0

                # APPENDING THE THRESHOLD TO THE LOGIC OPERATOR
                cur_threshold = "" if t_value == 0 else (
                    F"[with sim ≥ {t_value}]" if t_value < 1 else F"[with sim = {t_value}]")

                # THE ROOT TRE NODE
                root = Node(F"{GET_LOGIC_OPERATOR(mtdBox['type'])} {cur_threshold}")

                # Generating the method formula tree
                method_formula(mtdBox['conditions'], parent=root)
                f_expression, expression_tree = getExpressionAndTree(root)

            for method_item in box_list:

                if "conditions" not in method_item:

                    algorithm, predicate_selections, seq_predicates, code = unboxingAlgorithm(job_id, method_item)

                    # APPEND CODE FOR THE LOGIC FORMULA
                    codes.append(code)

                    # WRITE THE CURRENT METHOD
                    methods_signature.write(algorithm)

                    # UPDATE THE ENTITY SELECTION WRITER
                    methods_predicates.write(predicate_selections)

                    # UPDATE THE SEQUENCE WRITER
                    # methods_sequences.write(seq_predicates)

                else:

                    # RECURSION
                    counter[0] = counter[0] + 1
                    writeMethodsBox(method_item)

            # THIS IS TO CREATE THE PARTS IN THE LOGIC EXPRESSION
            formula_parts.update({Rsc.ga_resource_ttl(code) for code in codes})

            return expression_tree, f_expression

        # ::: END OF FUNCTION writeMethodsBox ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        # RUNNING THE WRITE METHOD FUNCTION
        f_tree, f_exp = writeMethodsBox(methodBox)

        # THE METHOD SELECTED PREDICATES
        methods_signature.write(methods_predicates.getvalue())

        return methods_signature.getvalue(), methods_descriptions.getvalue(), f_tree, f_exp

    # #####################################################################################################
    # 1. THE LINKSET NAMESPACES IS SET IN THE LINKSET AS THE auto_prefixes
    # DICTIONARY NEEDS TO BE UPDATES WHEN CONVERTING THE CSV FILE
    # linkset_buffer.write(linksetNamespaces(auto_prefixes)
    # #####################################################################################################
    rsc_selection = resourceSelection(specs[Vars.linksetSpecs])

    # #####################################################################################################
    # 2. LINKSET GENERIC AND STATS METADATA DESCRIPTION
    # #####################################################################################################
    linkset_buffer.write(genericDes(job_code, specs[Vars.linksetSpecs]))

    # #####################################################################################################
    # 3. THE LINKSET LOGIC EXPRESSION
    # #####################################################################################################
    linkset_buffer.write(header("LINKSET LOGIC EXPRESSION", lines=2))
    linkset_buffer.write(F"\n\n{Rsc.ga_resource_ttl(formula_uri_place_holder)}\n\n")
    linkset_buffer.write(preVal('a', VoidPlus.LogicFormulation_ttl))
    linkset_buffer.write(F"### EXPRESSION PARTS ###\n")

    # NEW LINE INSIDE THE EXPRESSION FOR Literal TO WRITE IT AS """###LOGIC \n EXPRESSION###"""@en
    linkset_buffer.write(preVal(VoidPlus.formulaDescription_ttl, Literal('###LOGIC \n EXPRESSION###').n3(MANAGER), end=False))
    linkset_buffer.write(F"\n")
    linkset_buffer.write(preVal(VoidPlus.formulaTree_ttl, Literal('###LOGIC \n TREE###').n3(MANAGER), end=True))
    linkset_buffer.write("\n")

    # #####################################################################################################
    # 4. THE DESCRIPTION OF THE METHODS INVOLVED IN THE CREATION OF LINKS.
    # THIS INCLUDES (1) THE METHOD SIGNATURE (2) PREDICATES AND (3) PREDICATE PATHS
    # #####################################################################################################
    method_signature, method_description,  formula_tree, formula_exp = unboxingMethodsBox(
        job_code, specs[Vars.linksetSpecs][Vars.methods])

    # #####################################################################################################
    # 5. UPDATING THE FORMULA IN STANDBY IN PART 4:
    # (1) FORMULA URI (2) LOGIC EXPRESSION AND (3) EXPRESSION PARTS
    # THIS CAN ONLY BE DONE AFTER THE METHOD [unboxingMethodsBox] IS EXECUTED
    # #####################################################################################################
    parts = "".join(preVal(VoidPlus.part_ttl, part) for part in formula_parts)
    temp = linkset_buffer.getvalue().replace("###FORMULA URI###", job_code)
    temp = temp.replace('###LOGIC \n EXPRESSION###', formula_exp if formula_exp else " MISSING MATCHING METHODS ")
    temp = temp.replace('###LOGIC \n TREE###', F"\n{space}{formula_tree}\n{space}" if formula_tree else ' MISSING MATCHING METHODS ')
    resetBuffer(linkset_buffer, temp.replace("### EXPRESSION PARTS ###", parts))

    # 6. ENTITY SELECTION AND CONSTRAINTS
    linkset_buffer.write(rsc_selection)

    # 7. METHOD SIGNATURE
    linkset_buffer.write(method_signature)

    # 8. THE DESCRIPTION OF THE ALGORITHM(S) USED
    linkset_buffer.write(method_description)

    return linkset_buffer.getvalue()
