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

import traceback
from time import time
from ll.org.Export.Scripts.General import getUriLocalNamePlus
from ll.org.Export.Scripts.LinkPredicates import LinkPredicates


RSC_SELECTION = {}
SAME_AS = Sns.OWL.sameAs_ttl
MANAGER = Graph().namespace_manager
DEFAULT_LICENCE = Sns.DCterms.license_ttl
GET_LOGIC_OPERATOR = lambda operator: FuzzyNorms.LogicOperations.operator_format[operator.lower()]
CSV_HEADERS = {
    "Valid": VoidPlus.has_validation_status_ttl,
    "Max Strength": VoidPlus.strength_ttl,
    "Cluster ID": VoidPlus.cluster_ID_ttl
}
NORMS = [

    'AND', 'OR',

    'AND [Minimum t-norm (⊤min)]', 'AND [Hamacher Product (⊤H0)]', 'AND [Product t-norm (⊤prod)]',
    'AND [Nilpotent Minimum (⊤nM)]', 'AND [Łukasiewicz t-norm (⊤Luk)]', 'AND [Drastic t-norm (⊤D)]',

    'OR [Maximum s-norm (⊥max)]', 'OR [Probabilistic Sum (⊥sum)]', 'OR [Bounded Sum (⊥Luk)]',
    'OR [Drastic s-norm (⊥D)]', 'OR [Nilpotent Maximum (⊥nM)]', 'OR [Einstein Sum (⊥D)]'
]
space = "    "
language_code = Sns.ISO()
CUMMULATED_METADATA = Buffer()


def mainHeader(message, linesAfter=1):
    liner = "\n"
    return F"""{'#' * 110}\n#{F'{message.upper()}':^108}#\n{'#' * 110}{liner * linesAfter}"""


def subHeader(message, linesBefore=2, linesAfter=2):
    liner = "\n"
    return F"{liner * linesBefore}\n{'#'*80:^110}\n{' '*15}#{message.upper():^78}#\n{'#'*80:^110}{liner * linesAfter}"


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
        item = item.strip()
        # NOT AN OPERATOR
        # if item and item.startswith("AND") is False and item.startswith("OR") is False:
        if item and True not in [item.startswith(operator.upper())
                                 for operator in ['AND', 'OR', 'UNION', 'INTERSECTION', 'DIFFERENCE']]:
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


# Given a URI such as http://www.w3.org/2004/02/skos/core#exactMatch
# reconstruct it in turtle format as skos:exactMatch,
# THIS FUNCTION ALSO UPDATES THE VARIABLE auto_prefixes
# WHICH SAVES ALL PREFIXES AUTOMATICALLY GENERATED
def uri2ttl(uri, auto_prefixes):

    if Grl.isNtFormat(uri):
        uri = Grl.undoNtFormat(uri)

    if True:

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
                    prefix = F"N{prefix.replace('.', '').replace(',', '')}"
                rsc_prefix = F"""{prefix.replace('-', '_')}_{code[:5]}"""

            # Update the global prefix dictionary
            auto_prefixes[rsc_namespace] = rsc_prefix

        # Compose the source and target of the URI
        turtle = F"{rsc_prefix}:{rsc_name}" if rsc_prefix is not None and not Grl.isNumber(rsc_prefix) else URIRef(
            uri).n3(MANAGER)

        return {"prefix": rsc_prefix, "namespace": rsc_namespace, "local_name": rsc_name, "short": turtle}

    # except Exception as err:
    #     print(F">>> [ERROR FROM uri_2_turtle] URI: \n{space}{uri:30}\n{space}{err}\n")

uri2ttl('http://www.vondel.humanities.uva.nl/ecartico/persons/4706', {})
uri2ttl('http://www.humanities.uva.nl/dataset/persons/4706', {})
uri2ttl('http://purl.org/vocab/bio/0.1/example-1', {})
uri2ttl('http://purl.org/vocab/bios/0.1/example-1', {})
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


# RETURNS A PREDICATE VALUE LINE
def preVal(predicate, value, end=False, line=True, position=1):

    new_line = '\n' if line is True else ''
    tab = F'{space*position}' if line is True else ''
    return F"{tab}{predicate:{Vars.PRED_SIZE}}{value} {'.' if end is True else ';'}{new_line}"


def objectList(objects, padding=1):
    return F" ,\n{space * padding}{' ' * Vars.PRED_SIZE}".join(Rsc.ga_resource_ttl(elt) for elt in objects)


def validationGraphs(set_id, validations):
    if not validations:
        return None
    return F" ,\n{' ' * (Vars.PRED_SIZE + 4)}".join(
        Rsc.validationset_ttl(F"{Grl.deterministicHash(validation)}-{set_id}") for validation in validations)


# RETURN THE GENERIC NAMESPACES USED IN A LINKSET
def linksetNamespaces(automated: dict, isValidated: bool, isClustered: bool):

    # TODO: make sure that the automated namespace dictionary does
    #  not duplicate the predefined shared or specific namespaces

    tab = "\t"
    new = "\n"
    validation = F"{new}{tab}{VoidPlus.Validation_prefix if isValidated else ''}"
    cluster = F"{new}{tab}{VoidPlus.Cluster_prefix if isClustered else ''}"
    validation_set = F'' if isValidated is False else F"{new}{tab}{Rsc.validationset_prefix}"
    clustered = '' if isClustered is False else F"{new}{tab}{Rsc.clusterset_prefix}"

    names = F"""{mainHeader('NAMESPACES')}

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
    {Rsc.linkset_prefix}{cluster}{clustered}{validation}{validation_set}"""

    if automated:
        names += "\n\n### AUTOMATED / EXTRACTED NAMESPACES"
        for count, (namespace, prefix) in enumerate(automated.items()):
            names += F"{'    ' if count > 0 else ''}\n\t@prefix {prefix:>{Vars.PREF_SIZE}}: {URIRef(namespace).n3(MANAGER)} ."

    return names + "\n"


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
def unboxingFilterBox(job_id, collection, checker, prefixes):

    global RSC_SELECTION
    writer = Buffer()
    identifier = collection[Vars.id]

    label = collection[Vars.label]
    description = collection[Vars.description] if Vars.description in collection else ""
    dataset = collection[Vars.dataset]
    RSC_SELECTION[identifier] = dataset
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

    formulation_code = Rsc.ga_resource_ttl(F"SelectionFormulation-{Grl.deterministicHash(expression)}-{identifier}")
    check_code = Grl.deterministicHash(F"{expression}{dataset['dataset_id']}{dataset['collection_id']}")

    if check_code not in checker:
        checker[check_code] = 'in'
    else:
        return ""

    # WRITE THE RESOURCE SELECTION ID AND THE TYPE OF THE RESOURCE
    writer.write(F"\n\n### RESOURCE {identifier}\n")
    writer.write(F"{Rsc.ga_resource_ttl(F'ResourceSelection-{job_id}-{identifier}')}\n\n")
    writer.write(preVal('a', F"{Sns.VoID.dataset_ttl}, {VoidPlus.EntitySelection_ttl}"))

    # LABEL AND  DESCRIPTION IF THEY EXISTS
    if len(label.strip()) > 0:
        writer.write(preVal(Sns.RDFS.label_ttl, Literal(label).n3(MANAGER)))

    if len(description.strip()) > 0:
        writer.write(preVal(Sns.DCterms.description_ttl, Literal(description).n3(MANAGER)))

    # THE RESOURCE IS A CLASS PARTITION WHICH IS A SUBSET OF THE SELECTED DATASET
    writer.write(preVal(VoidPlus.subset_of_ttl, Rsc.ga_resource_ttl(dataset['dataset_id'])))

    # DATASET NAME USINg DC-TERMs IDENTIFIER
    writer.write(preVal(Sns.DCterms.identifier_ttl, Rsc.literal_resource(dataset['name'])))

    # THE FORMULATION OF SELECTED DATASET WHICH SPECIFIES THE CLASS PARTITION
    writer.write(preVal(VoidPlus.hasFormulation_ttl, formulation_code, end=True))

    # FORMULATION HAS CLASS PARTITION
    writer.write(F"\n\n### CLASS PARTITION OF RESOURCE {identifier}\n")
    writer.write(F"{class_partition_rsc}\n")
    writer.write(preVal('a', F"{VoidPlus.ClassPartition_ttl}"))

    writer.write(preVal(Sns.VoID.voidClass_ttl, Rsc.ga_resource_ttl(dataset['short_uri']), end=True))

    # AN UPDATE OF THE PREFIX DICTIONARY IS REQUIRES DUE TO THE LINE ABOVE
    if dataset['long_uri'] == dataset['short_uri']:
        local_name = Grl.getUriLocalNamePlus(dataset['long_uri'])
        prefix_uri = dataset['long_uri'].replace(local_name, '')
        prefix = F"{getUriLocalNamePlus(prefix_uri)}_{Grl.deterministicHash(dataset['long_uri'], 2)}"
        if prefix_uri not in prefixes:
            prefixes[prefix_uri] = prefix
    else:
        ns = dataset['short_uri'].split(":")
        if len(ns) > 1:
            key = dataset['long_uri'].replace(ns[1], '')
            if key not in prefixes:
                prefixes[key] = ns[0]

    writer.write(F"\n\n### FORMULATION OF RESOURCE {identifier}\n")
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
    if not data:
        return "THE OBJECT OF printSpecs IS EMPTY"

    for i, (key, val) in enumerate(data.items()):

        # DICTIONARY
        if isinstance(val, dict):
            if tab == 1:
                print(F"\n{tab * space} {key} {{{i+1}/{len(data)}}}")
            else:
                print(F"{tab * space} - {key} {{{i+1}/{len(data)}}}")
            printSpecs(val, tab=tab + 1)

        # LIST OBJECT
        elif isinstance(val, (list, set)):
            if tab == 1:
                print(F"\n{tab * space} {key} [{len(val)}]")
            else:
                print(F"{tab * space} - {key} [{len(val)}]")

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
            print(F"{tab * space} -> {key:{pad - (tab - 1) * 4}}: {val}")


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
                        if ns[1] not in prefixes:
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
                                    if ns[1] not in prefixes:
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
                                    if ns[1] not in prefixes:
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
                # print("\n-->", method['method'])
                if 'date_part' in method['method'] and Sns.Time.time not in prefixes:
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
                                        if ns[1] not in prefixes:
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
                                                if ns[1] not in prefixes:
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
                                                if ns[1] not in prefixes:
                                                    prefixes[ns[1]] = ns[0]

                                        short_uris.append(short_uri)
                                        long_uris.append(long_uri)
                                # print('')

                            # update
                            choices['short_properties'] = short_uris
                            choices['long_properties'] = long_uris

        except KeyError:
            print(Grl.ERROR(page='SpecsBuilder', function='method_conditions',
                            location='For loop with variable [method_conditions_list]'))
            exit()


def getLinksetSpecs(linksetId: int, job: str, prefixes: dict, printSpec: bool = True):
    """
    :param linksetId        : An integer parameter denoting the ID of the linkset to convert into an RDF documentation.
    :param job              : A string parameter indicating the IF of job from which to find the selected linkset.
    :param printSpec        : A boolean parameter for displaying the specification object if needed.
    :return:
    """

    center, line = 70, 70
    clusters = {}
    # prefixes = {}
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

    # print(
    #     F"\n{'':>16}{'-' * line:^{center}}\n{'|':>16}{'BUILDING THE SPECIFICATION':^{center}}|\n{'|':>16}{F'JOB IDENTIFIER : {job}':^{center}}|\n"
    #     F"{'|':>16}{F'LINKSET INDEX : {linksetId}':^{center}}|\n{'':>16}{'-' * line:^{center}}\n")

    # ###############################################################################
    # 1. COLLECTING THE AVAILABLE DATASETS                                          #
    # ###############################################################################
    if True:

        # 1.1 REQUEST ON DATASET INFO
        try:
            dataset_specs = requests.get(dataset_url).json()

        except Exception as err:
            print(
                Grl.ERROR(
                    page='SpecsBuilder', function='linksetSpecsDataItr',
                    location='1.1 REQUEST ON DATASET INFO',
                    message="PROBLEM WITH REQUESTING INFO ON DATASETS FROM TIMBUKTU"
                )
            )
            return

        # 1.2 REQUEST ON LINKSET INFO
        try:
            lst_specs = requests.get(linkset_url).json()

            # GETTING THE ENTITY SELECTION OBJECT FROM THE lst_specs
            entity_type_selections = lst_specs['entity_type_selections']

            # RESET THE RIGHT lst_specs WITH THE ACTUAL SPECS
            try:
                found = False
                for counter, spec in enumerate(lst_specs['linkset_specs']):
                    if spec['id'] == int(linksetId):
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
                Grl.ERROR(
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

            while True:

                cluster_limit = F"{clusters_uri}with_properties=none&limit={limit}&offset={offset}&include_nodes=true"
                clusters_data = requests.get(cluster_limit).json()

                for item in clusters_data:
                    # Adding a set is better but will not work in the
                    # need of a deterministic hash output for the name of the cluster
                    # item['item'] = list()
                    clusters[item['id']] = item

                offset = offset + limit
                if len(clusters_data) < limit:
                    break

        except Exception as err:
            # print(F"{clusters_uri}limit={limit}&offset={offset}")
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

                for i, i_property in enumerate(info['property']):

                    # Odds numbers slots are container of a property name
                    if (i + 1) % 2 != 0:
                        try:
                            # print(F"{i_property}:{id}")
                            # print("\t", dataset_specs[id][
                            #     'collections'][entity_type]['properties'][i_property]['shortenedUri'])
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
                                    if ns[1] not in prefixes:
                                        prefixes[ns[1]] = ns[0]

                            short_properties.append(short_uri)
                            long_properties.append(long_uri)

                        except KeyError as err:
                            print(F"{i_property}:{id}")
                            print(dataset_specs[id]['collections'][entity_type]['properties'])
                            print(dataset_specs[id]['collections'][entity_type]['properties'][i_property])

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
                                if ns[1] not in prefixes:
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
                        if ns[1] not in prefixes:
                            prefixes[ns[1]] = ns[0]

                elif l_uri and s_uri and l_uri == s_uri:

                    local_name = getUriLocalNamePlus(l_uri)
                    prefix_uri = l_uri.replace(local_name, "")
                    prefix = F"{getUriLocalNamePlus(prefix_uri)}_{Grl.deterministicHash(l_uri, 2)}"
                    if prefix_uri not in prefixes:
                        prefixes[prefix_uri] = prefix

                entity_type_selections[item_id]['dataset']['short_uri'] = s_uri
                entity_type_selections[item_id]['dataset']['long_uri'] = l_uri

            else:

                # print("=====================================================")
                # print(l_uri)
                entity_type_selections[item_id]['dataset']['long_uri'] = l_uri

                if 'uri' in dataset_specs[id]['collections'][collection_id] and len(
                        dataset_specs[id]['collections'][collection_id]['uri']) > 0:

                    local_name = getUriLocalNamePlus(l_uri)
                    prefix_uri = F"{getUriLocalNamePlus(prefix_uri)}_{Grl.deterministicHash(l_uri, 2)}"
                    prefix = getUriLocalNamePlus(prefix_uri)

                    entity_type_selections[item_id]['dataset']['long_uri'] = dataset_specs[
                        id]['collections'][collection_id]['uri']

                    entity_type_selections[item_id]['dataset']['short_uri'] = F"{prefix}:{local_name}"
                    if prefix_uri not in prefixes:
                        prefixes[prefix_uri] = prefix

                else:
                    entity_type_selections[item_id]['dataset'][
                        'short_uri'] = "...... NO SHORT URI FOR THE RESOURCE ......"
                    entity_type_selections[item_id]['dataset'][
                        'long_uri'] = "...... NO LONG URI FOR THE RESOURCE ......"

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

    for data in stats_specs:
        if data['spec_id'] == linkset_name:
            stats_specs = data
            break

    # IF THE LINKSET HAS NO STATS YET, SET THE stats_specs OBJECT
    if isinstance(stats_specs, list):
        stats_specs = {}
        print("\t\t\t\t* THERE IS NOT CLUSTERING STATS.")

    # MOVE CLUSTER STATS TO LINKSET STATS
    stats_specs2 = requests.get(stats_url2).json()

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
        # print(F"{clusters_uri}limit={limit}&offset={offset}")
        print("\t\t\t\t* THE LINKS HAVE NOT YET BEEN VALIDATED.")
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

    specs = {'linksetStats': stats_specs, 'linksetSpecs': lst_specs, 'validations': []}

    if printSpec:
        printSpecs(specs, tab=1)

    return specs


# THE UNBOXING OF THE LINKSET SPECIFICATIONS
def unboxingLinksetSpecs(specs: dict, prefixes: dict, triples: bool = True):

    formula_parts = set()
    linkset_buffer = Buffer()
    checker = defaultdict(str)
    methods_descriptions = Buffer()
    job_code = specs[Vars.linksetSpecs][Vars.job_id]
    linkset_id = specs[Vars.linksetSpecs][Vars.id]
    formula_uri_place_holder = F"LinksetFormulation-###FORMULA URI###-{linkset_id}"

    def header(message, lines=2):
        liner = "\n"
        return F"{liner * lines}{'#'*80:^110}\n{' '*15}#{message:^78}#\n{'#'*80:^110}{liner * (lines-1)}"

    methods_descriptions.write(header("METHODS'S DESCRIPTION", lines=2))

    def genericStats(linksetStats: dict, validationGraph: str):

        stats = Buffer()
        has_validation = False
        stats.write(F"\n{space}### VOID LINKSET STATS\n")

        # TOTAL LINKS COUNT
        if Vars.triples in linksetStats and linksetStats[Vars.triples] > -1:
            stats.write(preVal(Sns.VoID.triples_ttl, Rsc.literal_resource(linksetStats[Vars.triples])))

        # THE TOTAL NUMBER OF ENTITIES
        if Vars.distinctLinkedEntities in linksetStats and linksetStats[Vars.distinctLinkedEntities] > -1:
            stats.write(preVal(Sns.VoID.entities_ttl, Rsc.literal_resource(linksetStats[Vars.distinctLinkedEntities])))

        # NUMBER OF DISTINCT SUBJECT RESOURCES IN THE LINKSET
        if Vars.distinctSub in linksetStats and linksetStats[Vars.distinctSub] > -1:
            stats.write(preVal(Sns.VoID.distinctSubjects_ttl, Rsc.literal_resource(linksetStats[Vars.distinctSub])))

        # NUMBER OF DISTINCT OBJECT RESOURCES IN THE LINKSET
        if Vars.distinctObj in linksetStats and linksetStats[Vars.distinctObj] > -1:
            stats.write(preVal(Sns.VoID.distinctObjects_ttl, Rsc.literal_resource(linksetStats[Vars.distinctObj])))

        stats.write(F"\n{space}### SOURCE AND TARGET DATASETS STATS\n")

        # NUMBER OF DISTINCT RESOURCES IN THE SOURCE AND TARGET DATASETS
        if Vars.distinctSrcTrgEntities in linksetStats and linksetStats[Vars.distinctSrcTrgEntities] > -1:
            stats.write(preVal(VoidPlus.srcTrgEntities_ttl, Rsc.literal_resource(linksetStats[Vars.distinctSrcTrgEntities])))

        # NUMBER OF DISTINCT RESOURCES IN THE TARGET DATASETS
        if Vars.distinctSourceEntities in linksetStats and linksetStats[Vars.distinctSourceEntities] > -1:
            stats.write(
                preVal(VoidPlus.sourceEntities_ttl,
                       Rsc.literal_resource(linksetStats[Vars.distinctSourceEntities])))

        # NUMBER OF DISTINCT RESOURCES IN THE TARGET DATASETS
        if Vars.distinctTargetEntities in linksetStats and linksetStats[Vars.distinctTargetEntities] > -1:
            stats.write(
                preVal(VoidPlus.targetEntities_ttl, Rsc.literal_resource(linksetStats[Vars.distinctTargetEntities])))

        stats.write(F"\n{space}### ABOUT CLUSTERS\n")

        # THE NUMBER OF CLUSTERS IF AVAILABLE
        if Vars.clusters in linksetStats and linksetStats[Vars.clusters] > -1:
            stats.write(preVal(VoidPlus.clusters_ttl, Literal(linksetStats[Vars.clusters]).n3(MANAGER)))
            stats.write(preVal(
                VoidPlus.clusterset_ttl,
                F"{Rsc.clusterset_ttl(Grl.deterministicHash(specs['linksetSpecs']['clusters']))}-{linkset_id}"))

        # # THE TOTAL AMOUNT OF LINKS ACCEPTED
        # if Vars.accepted in linksetStats and linksetStats[Vars.accepted] > -1:
        #     stats.write(preVal(VoidPlus.accepted_ttl, Rsc.literal_resource(linksetStats[Vars.accepted])))
        #
        # # THE TOTAL AMOUNT OF LINKS REJECTED
        # if Vars.rejected in linksetStats and linksetStats[Vars.rejected] > -1:
        #     stats.write(preVal(VoidPlus.rejected_ttl, Rsc.literal_resource(linksetStats[Vars.rejected])))
        #
        # # THE TOTAL AMOUNT OF LINKS NOT VALIDATED
        # if Vars.notValidated in linksetStats and linksetStats[Vars.notValidated] > -1:
        #     stats.write(preVal(VoidPlus.unchecked_ttl, Rsc.literal_resource(linksetStats[Vars.notValidated])))

        has_validation = Vars.notValidated in linksetStats and linksetStats[Vars.notValidated] < linksetStats[Vars.triples]

        if validationGraph:
            stats.write(F"\n{space}### ABOUT VALIDATIONS\n")

            # THE TOTAL AMOUNT OF CONTRADICTING LINKS
            if Vars.mixed in linksetStats and linksetStats[Vars.mixed] > -1:
                stats.write(preVal(VoidPlus.contradictions_ttl, Rsc.literal_resource(linksetStats[Vars.mixed])))

            if has_validation is True:
                stats.write(preVal(VoidPlus.has_validationset_ttl, validationGraph))
            stats.write("\n")

        return stats.getvalue()

    # Generic description of a linkset/les
    def genericDes(job_id: str, linksetSpecs: dict, validationGraph: str):

        g_meta = Buffer()
        g_meta.write(header('LINKSET GENERIC METADATA', lines=2))

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
            g_meta.write(preVal(Sns.DCterms.publisher_ttl, Literal(linksetSpecs["publisher"]).n3()))

        # LINKSET LINK-TYPE
        g_meta.write(preVal(Sns.VoID.linkPredicate_tt, linksetSpecs[Vars.linkType][Vars.short]))

        # 2. USER'S LABEL
        if len(Literal(linksetSpecs[Vars.label].strip())) > 0:
            g_meta.write(preVal(Sns.RDFS.label_ttl, Literal(linksetSpecs[Vars.label]).n3()))

        # 3. LINKSET DESCRIPTION
        if Vars.description in linksetSpecs and len(Literal(linksetSpecs[Vars.description].strip())) > 0:
            g_meta.write(preVal(
                Sns.DCterms.description_ttl, Literal(linksetSpecs[Vars.description]).n3()))
            g_meta.write("\n")

        # LINKSET STATS
        g_meta.write(genericStats(specs[Vars.linksetStats], validationGraph))

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
        entity_constraints.write(F"{header('LINKSET RESOURCE SELECTIONS')}")

        # AT THE SOURCE OR TARGET, THERE CAN EXIST MORE THAN ONE SELECTED RESOURCE
        for logic_box in linksetSpecs[Vars.sources]:

            filter_triples = unboxingFilterBox(job_code, logic_box, checker, prefixes)
            if filter_triples not in checker:
                checker[filter_triples] = "in"
                entity_constraints.write(filter_triples)

        # Source selected at the target
        if linksetSpecs[Vars.sources] != linksetSpecs[Vars.targets]:
            for logic_box in linksetSpecs[Vars.targets]:
                filter_triples = unboxingFilterBox(job_code, logic_box, checker, prefixes)
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
            methods_descriptions.write(F"\n{Rsc.ga_resource_ttl(algor_name)}\n")
            methods_descriptions.write(preVal('a', VoidPlus.MatchingAlgorithm_ttl))

            methods_descriptions.write(
                preVal(Sns.DCterms.description_ttl,
                       Algorithm.short_illustration(algor_name.lower()), end=False))

            # SEE ALSO
            methods_descriptions.write(
                preVal(Sns.RDFS.seeAlso_ttl,
                       F" ,\n{' ' * (Vars.PRED_SIZE + 4)}".join(
                           Rsc.ga_resource_ttl(link) for link in Algorithm.seeAlso(algor_name)), end=True))

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
            algor_writer.write(
                preVal(VoidPlus.thresholdRange_ttl, Literal(Algorithm.range(algor_name.lower())).n3(MANAGER)))

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

                # ADDING THE TIME NAMESPACE
                if Sns.Time.time not in prefixes:
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
                                        'transformer': transformer
                                    }
                                ]
                            }

                        else:
                            group_check[ent_sel_id]['predicates'].append(
                                {
                                    'property': str(src_sequence[0]),
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

                                                if Sns.ISO.iso3166_1 not in prefixes:
                                                    prefixes[Sns.ISO.iso3166_1] = Sns.ISO.prefix_code
                                                stopwords_buffer.write(
                                                    preVal(Sns.DC.language_ttl,
                                                           iso369 if iso369 else Literal(language).n3(), end=False))

                                                stopwords_buffer.write(
                                                    preVal("voidPlus:stopWordsList", stopwords, end=True))

                                                # UPDATE THE USE OF A NEW NAMESPACE
                                                if Sns.DC.dc not in prefixes:
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
            # print(codes)

            # intermediate_selection_id = method['method_config']['entity_type_selection']
            # intermediate_properties = method['method_config']['intermediate_source'] + method['method_config'][
            #     'intermediate_target']

            for key, code in codes.items():
                # sel_code = Grl.deterministicHash(F"{intermediate_selection_id}{intermediate_properties}")
                algor_writer.write(F"\n{space}### {key.upper()} PREDICATE(S) CONFIGURATION OF THE INTERMEDIATE DATASET \n")
                algor_writer.write(
                    preVal(VoidPlus.intermediateSubjEntitySelection_ttl if key == "source"
                           else VoidPlus.intermediateObjEntitySelection_ttl,
                           Rsc.ga_resource_ttl(F"ResourceSelection-{code}")))

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

                # THE ROOT NODE OF THE TREE
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
    validation_graphs = validationGraphs(linkset_id, specs['validations'])
    linkset_buffer.write(
        genericDes(
            job_code,
            specs[Vars.linksetSpecs],
            validation_graphs
        ))

    # #####################################################################################################
    # 3. THE LINKSET LOGIC EXPRESSION
    # #####################################################################################################
    linkset_buffer.write(header("LINKSET LOGIC EXPRESSION", lines=2))
    linkset_buffer.write(F"\n\n{Rsc.ga_resource_ttl(formula_uri_place_holder)}\n\n")
    linkset_buffer.write(preVal('a', VoidPlus.LinksetLogicFormulation_ttl))
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


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
#            FUNCTIONS FOR DEALING WITH LENS            #
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

def default_fuzzy(set_operator):

    set_operator = set_operator.lower()

    if set_operator.startswith('union'):
        return 'OR [Maximum s-norm (⊥max)]'

    if set_operator.startswith('intersection'):
        return 'AND [Minimum t-norm (⊤min)]'

    if set_operator.__contains__('difference'):
        return ''

    return 'an unknown operator'


def operator_message(operation, limit, hazy):

    tester = operation.lower().__contains__('difference')
    # print(F"{operation} {limit} {tester}")

    if limit > 0:
        text = F"{operation}{' using' if tester else ' using'} " \
               F"{FuzzyNorms.LogicOperations.operator_format.get(hazy.lower(), default_fuzzy(operation))}" \
               F" with{'' if tester else ' combination'} sim ≥ {limit}"
    else:
        text = F"{operation}{'' if tester else ' using'} " \
               F"{FuzzyNorms.LogicOperations.operator_format.get(hazy.lower(), default_fuzzy(operation))}" \
               # F" {'' if tester else 'with no threshold restriction'}"

    return text


def lensFormulaExpression(job_id, operator, threshold, fuzzy, operands, position=1, detail=None, root=None, parts=None):

    # PARTS IS A COLLECTION OF LEAFS WHICH ARE IN OTHER WORDS ONLY LINKSETS.
    if parts is None:
        parts = set()

    # THE ROOT NODE OF THE TREE
    if root is None:
        root = Node(F"{operator_message(operation=operator, limit=threshold, hazy=fuzzy)}")
        detail = []

    for i, operand in enumerate(operands):
        # print("\n", operand_data)
        # operand = operand_data[0]
        # DEALING WITH A LENS
        if operand.startswith('lens'):

            id = F"{position}.{chr(i+97)}"
            detail.append(F"({id}): created as {operand}")

            # GET THE LENS ID
            lens_id = operand.split('-')[1]

            # FETCH THE SPECS OF THE CURRENT LENS
            lens_specs = getLensSpecs(lensId=lens_id, job=job_id, printSpec=False)

            # THE OPERANDS OF THE CURRENT LENS
            new_operands = [
                Rsc.lens_ttl(F"{lens_specs['job_id']}-{lens['id']}") if lens['type'].lower() == 'lens'
                else Rsc.linkset_ttl(F"{lens_specs['job_id']}-{lens['id']}") for lens in lens_specs['specs']['elements']]

            # GENERATING A NEW TREE NODE
            new_threshold = lens_specs['specs']['threshold']
            new_fuzzy = lens_specs['specs']['t_conorm']
            parent = Node(
                operator_message(operation=F"{lens_specs['specs']['type']} ({id})", limit=new_threshold, hazy=new_fuzzy),
                parent=root)

            # RECURSIVE CALL WITH THE NEW NODE
            lensFormulaExpression(
                job_id=job_id, operator=lens_specs['specs']['type'], fuzzy=new_fuzzy,
                threshold=new_threshold, operands=new_operands, position=position+1, detail=detail, root=parent, parts=parts)

        # WE HAVE REACHED THE LEAF (LINKSET)
        else:
            Node(operand, parent=root)
            parts.add(operand)

    detail.sort()
    return root, parts, detail


def getLensSpecs(lensId: int, job: str, printSpec: bool = True):
    """
    :param lensId           : An integer parameter denoting the ID of the linkset to convert into an RDF documentation.
    :param job              : A string parameter indicating the IF of job from which to find the selected linkset.
    :param printSpec        : A boolean parameter for displaying the specification object if needed.
    :return:
    """
    job_specs = None
    lens_specs = None
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

    except ValueError as err:
        print("\nTHE JOB REQUEST CAN N0T BE PLACED")
        print(
            Grl.ERROR(
                page='SpecsBuilder',
                function='lensSpecsDataItr',
                location='FETCH THE LIST OF JOBS',
                message=F'Fetching the list of jobs run under the job id: {job}'
            ))

    # ###############################################################################
    # 3. FETCH THE RIGHT LENS SPECS FROM THE LIST OF JOBS                           #
    # ###############################################################################
    try:
        found = False
        for counter, spec in enumerate(job_specs['lens_specs']):
            if spec['id'] == int(lensId):
                found, lens_specs = True, spec
                break

        if found is False:
            print(F"\nTHE LENS WITH ID: [{lensId}] COULD NOT BE FOUND IN THE JOB: {job}")
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

    # printSpecs(lens_specs)
    # # printSpecs(stats_specs)

    if printSpec:
        printSpecs(lens_specs, tab=1)

    return lens_specs


def unboxingLensSpecs(specs: dict, prefixes: dict, isValidated: bool = False, isClustered: bool = False):

    lens_writer = Buffer()
    lens_specs = specs['lensSpecs']
    lens_stats = specs['lensStats']
    operator = lens_specs['specs']['type']
    lens_id = lens_specs['id']
    lens_name = F"{lens_specs['job_id']}-{lens_id}"
    targets = []
    operators = []
    legend = []
    parts = set()

    def getTargets(operation_box, stem, position=0):

        # 1. This code primarily is to fetch targets (operands) in the lens operation.
        # This allows for collecting the metadata of all linksets in the target list.
        # 2. While executing this the tree structure of the logic box is (simple) is extracted.
        # In the event that the lens is not simple or contains one or more intermediate lenses,
        # this tree is discarded and a new one that contains in depth detail is generated.
        # 3. Finally, the list list of operators helps detecting a complex lens. A lens is
        # deemed complex if it is composed of at least one lens or more than one operators.

        def leaf(job_id, child, parent, idx):

            infant = Rsc.lens_ttl(F"{job_id}-{child['id']}") \
                if child['type'].lower() == 'lens' \
                else Rsc.linkset_ttl(F"{job_id}-{child['id']}")

            if child['type'].lower() == 'lens':
                id = F"{position}.{chr(idx + 97)}"
                legend.append(F"({id}): created as {infant}")

                # GET THE LENS ID
                lens_identifier = infant.split('-')[1]

                # FETCH THE SPECS OF THE CURRENT LENS
                lens_specifications = getLensSpecs(lensId=lens_identifier, job=job_id, printSpec=False)

                # GENERATING A NEW TREE NODE
                new_threshold = lens_specifications['specs']['threshold']
                new_fuzzy = lens_specifications['specs']['t_conorm']
                parent = Node(
                    operator_message(operation=F"{lens_specifications['specs']['type']} ({id})", limit=new_threshold,
                                     hazy=new_fuzzy),
                    parent=parent)

                # RECURSIVE CALL WITH THE NEW NODE
                getTargets(lens_specifications['specs'], parent, position+1)
                # lensFormulaExpression(
                #     job_id=job_id, operator=lens_specs['specs']['type'], fuzzy=new_fuzzy,
                #     threshold=new_threshold, operands=new_operands, position=position + 1, detail=detail, root=parent,
                #     parts=parts)

            else:
                Node(infant, parent=parent)
                parts.add(infant)

            return infant

        if 'elements' in operation_box:
            operation, operands = operation_box['type'], operation_box['elements']
            threshold = operation_box['threshold'] if 'threshold' in operation_box else None
            logic_combination = operation_box['t_conorm'] if 't_conorm' in operation_box else None
            # APPEND THE CURRENT OPERATOR. THIS WILL LATER HELP CHECKING WHETHER THE LENS IS COMPLEX OR SIMPLE
            operators.append(operation)

            # CREATE THE ROOT OF THE TREE
            if stem is None:
                stem = Node(operator_message(operation, threshold, logic_combination))

            # CHECKING THE ELEMENTS IN THE OPERATION BOX
            for index, new_box in enumerate(operands):
                # print(F"L2605 {new_box}")
                # THERE EXIST A NEW LOGIC BOX
                if 'elements' in new_box:
                    operation, operands = new_box['type'], new_box['elements']
                    threshold = new_box['threshold'] if 'threshold' in new_box else None
                    logic_combination = new_box['t_conorm'] if 't_conorm' in new_box else None
                    node = Node(operator_message(operation, threshold, logic_combination), parent=stem)
                    getTargets(new_box, stem=node, position=position+1)

                # WE HAVE REACHED THE LEAF
                else:
                    targets.append(leaf(job_id=lens_specs['job_id'], child=new_box, parent=stem, idx=index))

        # TODO: CHECK WHETHER THE LAST CONDITION IS NECESSARY
        else:
            targets.append(leaf(job_id=lens_specs['job_id'], child=operation_box, parent=stem, idx=position))

        return stem

    # EXTRACT THE TREE, TARGETS AND OPERATORS OF A POTENTIALLY SIMPLE LENS
    root = getTargets(lens_specs['specs'], stem=None)

    # print(parts)
    # USING PARTS, COLLECT THE METADATA OF LINKSETS INVOLVED IN THE CREATION OF THE CURRENT LENS
    print("\t\t- Gathering the metadata of the linksets composing the lens.")
    for linkset in parts:
        linkset_id = linkset.split('-')[1]
        print(F"\t\t\t• {linkset}")
        linkset_specs = getLinksetSpecs(linksetId=linkset_id, job=lens_specs['job_id'], prefixes=prefixes, printSpec=False)
        metadata = unboxingLinksetSpecs(specs=linkset_specs, prefixes=prefixes)
        CUMMULATED_METADATA.write(F"{metadata}\n\n")

    # REMOVE SHARED PREFIXES ENDING UP IN AUTOMATED PREFIXES
    for key in [Sns.CC.cc, Sns.RDF.rdf, Sns.RDFS.rdfs, Sns.DCterms.dcterms,
                Sns.Formats.formats, Sns.VoID.void, Sns.XSD.xsd]:

        if key in prefixes:
            del prefixes[key]

    # -------------------------------------------
    # NAMESPACES USED IN THE ANNOTATION OF A LENS
    # -------------------------------------------
    lens_writer.write(mainHeader("NAMESPACES", 2))
    lens_writer.write(
        F"\n{space}### PREDEFINED SHARED NAMESPACES"
        F"\n{space}{Sns.CC.prefix}"
        F"\n{space}{Sns.DCterms.prefix}"
        F"\n{space}{Sns.Formats.prefix}"
        # F"\n{space}{Sns.OWL.prefix}"
        F"\n{space}{Sns.RDF.prefix}"
        F"\n{space}{Sns.RDFS.prefix}"
        F"\n{space}{Sns.VoID.prefix}"
        F"\n{space}{Sns.XSD.prefix}"
        
        F"\n\n{space}### PREDEFINED SPECIFIC NAMESPACES"
        F"\n{space}{VoidPlus.Cluster_prefix if isClustered else ''}"
        F"\n{space}{VoidPlus.Clusterset_prefix if isClustered else ''}"
        F"\n{space}{VoidPlus.Lens_prefix}"
        F"\n{space}{VoidPlus.Linkset_prefix}"
        F"\n{space}{VoidPlus.LensOperator_prefix}" 
        F"\n{space}{Rsc.resource_prefix}"
        F"\n{space}{VoidPlus.Validation_prefix if isValidated else ''}"
        F"\n{space}{VoidPlus.Validationset_prefix if isValidated else ''}"
        F"\n{space}{VoidPlus.ontology_prefix}"
    )

    if prefixes:
        lens_writer.write(F"\n\n{space}### AUTOMATED / EXTRACTED NAMESPACES")
        for count, (namespace, prefix) in enumerate(prefixes.items()):
            lens_writer.write(F"{'    ' if count > 0 else ''}"
                              F"\n{space}@prefix {prefix:>{Vars.PREF_SIZE}}: {URIRef(namespace).n3(MANAGER)} .")

    lens_writer.write(subHeader("LENS METADATA", 2, 2))

    # --------------
    # LENS OPERATORS
    # --------------
    import ll.org.Export.Scripts.LensOperator as Operator
    operators_rsc = []
    for operator in set(operators):

        operator_rsc = Operator.resource_ttl(operator)
        operators_rsc.append(operator_rsc)
        lens_writer.write("### LENS OPERATOR\n")

        # OPERATOR RESOURCE
        lens_writer.write(F"{operator_rsc}\n")

        # OPERATOR TYPE
        lens_writer.write(preVal('a', VoidPlus.LensOperator_ttl))

        # OPERATOR LABEL
        lens_writer.write(preVal(Sns.RDFS.label_ttl, Literal(Operator.label(operator)).n3()))

        # OPERATOR DESCRIPTION
        lens_writer.write(preVal(Sns.DCterms.description_ttl, Literal(
            Operator.description(operator), lang='en').n3(), end=True))

        lens_writer.write("\n")

    # -----------------------------
    # GENERIC DESCRIPTION OF A LENS
    # -----------------------------

    lens_writer.write("\n### LENS RESOURCE DESCRIPTION\n")

    # LENS NAME
    lens_writer.write(F"{Rsc.lens_ttl(lens_name)}\n")

    # TYPE: lens
    lens_writer.write(preVal('a', VoidPlus.Lens_ttl))

    # FEATURE: Turtle and Trig
    lens_writer.write(preVal(Sns.VoID.feature_ttl, F"{Sns.Formats.turtle_ttl}, {Sns.Formats.triG_ttl}"))

    # ATTRIBUTION: LenticularLens
    lens_writer.write(preVal(Sns.CC.attributionName_ttl, Literal('LenticularLens', 'en').n3()))

    # LICENCE OF THE LL
    lens_writer.write(preVal(Sns.CC.license_ttl, Rsc.uri_resource(Vars.LICENCE)))

    # LINKSET TIMESTAMP
    lens_writer.write(preVal(Sns.DCterms.created_ttl, Grl.getXSDTimestamp()))

    if "creator" in lens_specs and len(lens_specs["creator"].strip()) > 0:
        lens_writer.write(preVal(Sns.DCterms.creator_ttl, Literal(lens_specs["creator"]).n3()))

    if "publisher" in lens_specs and len(lens_specs["publisher"].strip()) > 0:
        lens_writer.write(preVal(Sns.DCterms.publisher_ttl, Literal(lens_specs["publisher"]).n3()))

    # UNIQUE LINK-TYPE ACROSS ALL LENSES OR LNKSETS IN THE CURRENT LENS
    lens_writer.write(preVal(Sns.VoID.linkPredicate_tt, lens_specs[Vars.linkType]['short']))

    # USER'S LABEL
    if len(Literal(lens_specs[Vars.label].strip())) > 0:
        lens_writer.write(preVal(Sns.RDFS.label_ttl, Literal(lens_specs[Vars.label]).n3()))

    # LINKSET DESCRIPTION
    if Vars.description in lens_specs and len(Literal(lens_specs[Vars.description].strip())) > 0:
        lens_writer.write(preVal(
            Sns.DCterms.description_ttl, Literal(lens_specs[Vars.description]).n3()))
        lens_writer.write("\n")

    # OPERATOR FUNCTION
    lens_writer.write("\n")
    lens_writer.write(preVal(VoidPlus.hasOperator_ttl, objectList(operators_rsc)))
    if len(operators_rsc) > 1:
        lens_writer.write("\n")

    lens_writer.write(
        preVal(VoidPlus.hasOperand_ttl, objectList(set(targets), padding=1)))

    # COMBINATION THRESHOLD
    if lens_specs['specs']['threshold'] > 0:
        lens_writer.write(preVal(VoidPlus.combiThreshold_ttl, lens_specs['specs']['threshold']))

    # -------------------------------
    # NUMERICAL DESCRIPTION OF A LENS
    # -------------------------------

    if len(lens_stats) > 0 and 'result' not in lens_stats:

        # TRIPLES
        lens_writer.write("\n")
        lens_writer.write(preVal(Sns.VoID.triples_ttl, Literal(lens_stats[Vars.triples]).n3(MANAGER)))

        # CLUSTERS
        if Vars.clusters in lens_stats and lens_stats[Vars.clusters] > -1:
            lens_writer.write("\n")

            # THE NUMBER OF CLUSTERS IF AVAILABLE
            lens_writer.write(preVal(VoidPlus.clusters_ttl, Literal(lens_stats[Vars.clusters]).n3(MANAGER)))

            # THE CLUSTER SET
            lens_writer.write(preVal(
                VoidPlus.clusterset_ttl,
                F"{Rsc.clusterset_ttl(Grl.deterministicHash(specs['clusters']))}-{lens_id}"))

        # ABOUT VALIDATION
        has_validation = Vars.notValidated in lens_stats and lens_stats[Vars.notValidated] < lens_stats[Vars.triples]
        if has_validation is True:
            lens_writer.write("\n")

            # THE TOTAL AMOUNT OF CONTRADICTING LINKS
            if Vars.mixed in lens_stats and lens_stats[Vars.mixed] > -1:
                lens_writer.write(preVal(VoidPlus.contradictions_ttl, Rsc.literal_resource(lens_stats[Vars.mixed])))

            # THE VALIDATION SET
            lens_writer.write(preVal(VoidPlus.has_validationset_ttl, validationGraphs(lens_id, specs['validations'])))

        # THE TOTAL NUMBER OF ENTITIES
        if Vars.distinctLinkedEntities in lens_stats and lens_stats[Vars.distinctLinkedEntities] > -1:
            lens_writer.write(preVal(Sns.VoID.entities_ttl, Rsc.literal_resource(lens_stats[Vars.distinctLinkedEntities])))

    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # LOGIC FORMULATION
    # =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    print("\t\t- Building the lens formulation expression and tree.")
    # EXTRACTING THE FORMULATION'S EXPRESSION AND TREE
    # ONLY UPDATE THE TREE IF WE ARE DEALING WITH A COMPLEX LENS
    # if len(operators) == 1 or True in [elt.__contains__('lens') for elt in targets]:
    exp, tree = getExpressionAndTree(root)
    legend = '\n\n\t\tLegend:\n\t\t\t' + '\n\t\t\t'.join(line for line in legend) if legend else ''
    tree = F"{tree}{legend}"
    exp = F"{exp}{legend}"
    print(F"\n\t{'=-=-='*23}\n{tree}\n\t{'=-=-='*22}\n")

    # FORMULATION RESOURCE
    formulation_rsc = F"LinksetFormulation-{lens_specs['job_id']}-{lens_id}"

    lens_writer.write(F"\n")
    lens_writer.write(preVal(VoidPlus.formulation_ttl, Rsc.ga_resource_ttl(formulation_rsc), end=True))

    lens_writer.write(subHeader('LENS LOGIC EXPRESSION', 1, 3))
    lens_writer.write(F"{Rsc.ga_resource_ttl(formulation_rsc)}\n")
    lens_writer.write(preVal('a', VoidPlus.LensOperator_ttl))
    # lens_writer.write("".join(preVal(VoidPlus.part_ttl, part) for part in parts))
    lens_writer.write(preVal(VoidPlus.part_ttl, objectList(parts)))

    # NEW LINE INSIDE THE EXPRESSION FOR Literal TO WRITE IT AS """###LOGIC \n EXPRESSION###"""@en
    lens_writer.write(preVal(VoidPlus.formulaDescription_ttl, Literal(exp).n3(MANAGER), end=False))
    lens_writer.write(F"\n")
    lens_writer.write(preVal(VoidPlus.formulaTree_ttl, Literal(F'\n{space}{tree}\n{space}').n3(MANAGER), end=True))
    lens_writer.write("\n")

    lens_writer.write("\n\n")
    lens_writer.write(mainHeader(F"METADATA OF THE LINKSETS COMPOSING lens:{lens_name}", linesAfter=3))
    # print(lens_writer.getvalue())
    lens_writer.write(CUMMULATED_METADATA.getvalue())

    return lens_writer.getvalue()
