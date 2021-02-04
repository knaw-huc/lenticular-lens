# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   DOCUMENTATION OF THE WHO - WHAT AND HOW OF A LINKSET BASED ON THE USERS'S SPECIFICATION               #
#                                                                                                         #
# #########################################################################################################


import ll.org.Export.Scripts.Variables as Vars
import ll.org.Export.Scripts.General as Grl
from collections import defaultdict, deque
from io import StringIO as Buffer
from rdflib import URIRef, Literal
from ll.org.Export.Scripts.Algotithms import Algorithm
from ll.org.Export.Scripts.Resources import Resource as Rsc
from ll.org.Export.Scripts.Namespaces import Namespaces as LLns
from ll.org.Export.Scripts.SharedOntologies import Namespaces as Sns
from string import digits
from anytree import Node, RenderTree, DoubleStyle, PreOrderIter, PostOrderIter, LevelGroupOrderIter
# from ll.org.Export.Scripts.Tree import filter_formula
import requests



"""
( resource:Normalised-EditDistance-PH9679d348fc0a2dbf3bd7 OR (⊥MAX) resource:SoundexDistance-PH7340cefe130f135b0214 ) 
    AND (⊤MIN) 
( resource:Normalised-EditDistance-PH9679d348fc0a2dbf3bd7  OR (⊥MAX) resource:SoundexDistance-PH7340cefe130f135b0214 ) 
    AND (⊤MIN) ( resource:Exact-PHf59e4946abdb2377860a 
    AND (⊤MIN) resource:Exact-PHf59e4946abdb2377860a )
"""


CSV_HEADERS = {
    "Valid": LLns.link_validation_tt,
    "Max Strength": LLns.strength_ttl,
    "Cluster ID": LLns.cluster_ID_ttl
}

same_as = Sns.OWL.sameAs_ttl
default_licence = Sns.DCterms.license_ttl
# checker = defaultdict(str)
# {
#     "id": 1,                                          // An integer as identifier
#     "label": "My linkset",                            // The label of the linkset in the GUI
#     "description": "",                                // A description of this linkset by the user; optional field
#     "is_association": false,                          // Work in progress; optional field, defaults to 'false'
#     "sources": [1],                                   // The identifiers of entity-type selections to use as source
#     "targets": [1],                                   // The identifiers of entity-type selections to use as targets
#     "methods": {                                      // The matching configuration for finding links; requires at least one condition
#         "conditions": [{                              // The matching configuration is composed of a logic box
#             "method_name": "=",                       // The type of matching to apply; see table below for allowed values
#             "method_value": {},                       // Some types of matching methods require extra configuration
#             "sources": [{                             // The source properties to use during matching
#                 "entity_type_selection": 1,           // The identifier of the entity-type selection to use
#                 "property": ["schema_birthDate"],     // The property path to which this condition applies
#                 "transformers": [{                    // The transformers to apply to transform the value before matching; see table below for allowed values
#                     "name": "PARSE_DATE",
#                     "parameters": {
#                         "format": "YYYY-MM-DD"
#                     }
#                 }]
#             }],
#             "targets": [{                             // The target properties to use during matching
#                 "entity_type_selection": 1,
#                 "property": ["schema_birthDate"],
#                 "transformers": []
#             }]
#         }],
#         "type": "AND"                                 // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR')
#     },
#     "properties": [{                                  // A list of property paths to use for obtaining data while reviewing the linkset; optional field
#         "entity_type_selection": 1,                   // The identifier of the entity-type selection to use
#         "property": ["schema_birthDate"]              // The property path
#     }]
# }


# FEELS IT UP A FORMULA PATTERN (tracker) USING THE VALUE LIST (formulae)

def expressionFormatter(tracker, formulae):

    tab = "\t"
    if formulae:

        formula_expression = ""
        # print(F"\n\ntested: {formula_tracking}")

        for count, expression in enumerate(tracker):

            move, options = F"{tab}{count * tab}", expression.split()

            if formula_expression == "":
                formula_expression += F"\t\t{expression}"

            else:

                if F"({options[0]})" in formula_expression:

                    formula_expression = formula_expression.replace(
                        F"({options[0]})", F"\n{move}({move}\n{move}\t{expression}\n{move})")

                else:
                    formula_expression = formula_expression.replace(F"{options[0]}", F"{expression}")

        # line = "\n\t"
        # print(F"FORMULA TRACKER: {tracker} \n\n{formula_expression}\n\n")
        # print(F"EXPRESSIONS :\n\n\t{F'{line}'.join(expression for expression in formulae)}")
        # print(F"\n\nFINAL FORMULA: \n\n{formula_expression.format(* formulae) if formulae else formula_expression}")

        return F"\n{formula_expression.format(* formulae) if formulae else formula_expression}"

    else:
        return None


# CLEARS THE StringIO GIVEN OBJECT
def clearBuffer(buffer):

    buffer.seek(0)
    buffer.truncate(0)


# CLEARS THE StringIO GIVEN OBJECT AND WRITES TO IT THE PROVIDED STRING
def resetBuffer(buffer, text):

    buffer.seek(0)
    buffer.truncate(0)
    buffer.write(text)


# RETURN (1) <PREDICATE> <PREDICATE-VALUE> IF A SINGLE PROPERTY IS PROVIDED AND A (2) PREFIX:NAME
# RETURN (1) AN RDF SEQUENCE AND (2) PREFIX:NAME IF A PROPERTY PATH IS PROVIDED
def rdfSequence(sequence: list, auto=True):

    if len(sequence) == 0:
        return None, None

    if len(sequence) == 1 and auto is True:
        # SEQUENCE TYPE
        triples = preVal('a', LLns.PropertyPartition_ttl)
        # triples = preVal(Sns.VoID.property_tt, Rsc.uri_resource(sequence[0]), line=True)
        triples += preVal(Sns.VoID.property_ttl, Rsc.ga_resource_ttl(sequence[0] if sequence[0] else '...........'), line=True)
        code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(triples)}")
        triples = F"{code}\n{triples}"

    else:

        # SEQUENCE TYPE
        triples = preVal('a', LLns.PropertyPartition_ttl)
        triples += F"\t{Sns.VoID.property_ttl}\n"

        # THE RDF SEQUENCE
        seq = F"\t\t{preVal('a', Sns.RDFS.sequence_ttl)}"
        for index, item in enumerate(sequence):
            pred = F"rdf:_{index+1}"
            end = "" if index == len(sequence) - 1 else ";"
            # seq += F"\t\t\t{pred:{Vars.PRED_SIZE}} {Rsc.uri_resource(item)} {end}\n"
            seq += F"\t\t\t{pred:{Vars.PRED_SIZE}} {Rsc.ga_resource_ttl(item if item else '...........')} {end}\n"

        # THE SEQUENCE CODE
        triples += F"\t\t[\n {seq} \t\t]"
        code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(triples)}")

        # THE FINAL SEQUENCE

        triples = F"{code}\n{triples} ;"

    # print(triples)
    # exit()
    return triples, code

    # print(rdf_sequence(["https://w3id.org/pnv#PersonName",
    #               "https://data.goldenagents.org/datasets/SAA/ontology/inventoryNumber",
    #               "http://www.w3.org/2000/01/rdf-schema#label"]))


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
            # print(F"+ {rsc_prefix}:{rsc_name} --> {uri}")

        else:
            # print("\tNAME SPACE", rsc_namespace)
            # Check if the namespace is registered in LOV's dataset
            result = Grl.queryEndpoint(query=getLovPrefixes(rsc_namespace), endpoint=Vars.LOV)

            if result and result["results"]["bindings"]:
                rsc_prefix = result["results"]["bindings"][0]['output']["value"]
                # print(F"- {rsc_prefix}:{rsc_name} --> {uri}")

            else:
                # As the namespace is not in the global prefix dictionary and LOV let us automate it
                prefix = Grl.getUriLocalNamePlus(uri=rsc_namespace, sep="_")
                code = Grl.hasher(rsc_namespace.replace(prefix, ""))

                if prefix[0] in digits:
                    prefix = F"N{prefix}"
                # rsc_prefix = F"""{prefix.replace('-', '_')}{'' if not index else F'_{index}'}"""
                rsc_prefix = F"""{prefix.replace('-', '_')}_{code[:5]}"""
                # print(F"* {rsc_prefix}:{rsc_name} --> {uri}")
                # print("last")

            # Update the global prefix dictionary
            auto_prefixes[rsc_namespace] = rsc_prefix

        # Compose the source and target of the URI
        turtle = F"{rsc_prefix}:{rsc_name}" if rsc_prefix is not None and not Grl.isNumber(rsc_prefix) else URIRef(
            uri).n3()

        # print(rsc_prefix, rsc_namespace, rsc_name, turtle)

        return rsc_prefix, rsc_namespace, rsc_name, turtle

    except Exception as err:
        print(F">>> [ERROR FROM uri_2_turtle] URI: \n\t{uri:30}\n\t{err}\n")


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

        # print(query)
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
    tab = '\t' if line is True else ''
    return F"{tab}{predicate:{Vars.PRED_SIZE}} {value} {'.' if end is True else ';'}{new_line}"


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
    {LLns.ontology_prefix}
    {Rsc.resource_prefix}
    {Rsc.linkset_prefix}

### AUTOMATED / EXTRACTED NAMESPACES
    """
    if automated:
        for count, (namespace, prefix) in enumerate(automated.items()):
            names += F"{'    ' if count > 0 else ''}@prefix {prefix:>{Vars.PREF_SIZE}}: {URIRef(namespace).n3()} .\n"

    return names


def expression_generator(postOrder):

    temporary = []
    new = []

    for item in postOrder:
        if item.lower() not in ['and', 'or']:
            temporary.append(item)
            # print(temporary)
        else:

            if len(temporary) > 1:
                # print(temporary)
                new.append(F'( {F" {item.upper()} ".join(temporary)} )')
                temporary.clear()

            elif len(temporary) == 1:
                # print(temporary)
                new = [F'( {F" {item.upper()} ".join(new + temporary)} )']
                # new.append(F' {item.upper()} {temporary[0]} ')
                temporary.clear()

            else:
                new.append(item)
            # print("\t\tnew:", new, "\n")

    if len(new) > 1:
        # print(F"CALL: {new}")
        new = expression_generator(new)

    return new


# THE UNBOXING OF A FILTER LOGIC BOX
def unboxingFilter(logicBox, checker):

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
                    # print(conditions, "\n")
                    # sequence = rdfSequence(item[Vars.filterProperty])
                    sequence = rdfSequence(
                        item[Vars.filterTtlProperty]
                        if Vars.filterTtlProperty in item and len(item[Vars.filterTtlProperty]) > 0
                        else item[Vars.uri_properties] if Vars.uri_properties in item else item[Vars.filterProperty])

                    # print(item[Vars.filterProperty], sequence[1])
                    seq_function = item[Vars.filterType] if Vars.filterType in item else ""
                    seq_value = item[Vars.filterValue] if Vars.filterValue in item else ""
                    seq_format = item[Vars.format] if Vars.format in item else ""

                    new_info = len(seq_function) > 0 or len(seq_value) > 0 or len(seq_format) > 0

                    if new_info is True:

                        # THE FILTER FUNCTION
                        if len(seq_function) > 0:
                            temp.write(
                                preVal(LLns.filterFunction_ttl, Literal(seq_function, lang='en').n3()))

                        # THE FILTER VALUE
                        if len(seq_value) > 0:
                            temp.write(preVal(LLns.filterValue_ttl, Literal(seq_value, lang='en').n3()
                            if Grl.isDecimalLike(seq_value) is False else seq_value))

                        # THE FILTER FORMAT TO APPLY
                        if len(seq_format) > 0:
                            temp.write(preVal(LLns.filterFormat_ttl, Literal(seq_format, lang='en').n3()))

                    code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(sequence[0] + temp.getvalue())}")
                    sequence = sequence[0].replace(sequence[1], code)
                    # print(sequence)
                    # IF THE SEQUENCE IS NOT EMPTY
                    if sequence:

                        predicate_selection.write(preVal(LLns.hasItem_ttl, code))

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
    formula_tree, expression, root = None, None, None
    if 'conditions' in logicBox and logicBox['conditions']:
        root = Node(logicBox['type'])
        filter_formula(logicBox['conditions'], parent=root)
        formula_tree = '\n\t'.join(["%s%s" % (pre, node.name) for pre, fill, node in RenderTree(root, style=DoubleStyle)])
        post_order = [node.name for node in PostOrderIter(root)]
        expression = expression_generator(post_order)[0]

    return predicate_selection.getvalue(), expression, predicate_sequences.getvalue(), F"\n\t{formula_tree}", root


# THE UNBOXING OF THE ENTITY SELECTION FILTER
#  ### RESOURCE
def unboxingFilterBox(collection, checker):

    # print(collection)
    writer = Buffer()
    id = collection[Vars.id]
    label = collection[Vars.label]
    description = collection[Vars.description] if Vars.description in collection else ""
    dataset = collection[Vars.dataset]
    # operator = "\t\t" + collection[Vars.selectionFilter]['type']

    pred_selections, expression, sequences, formula_tree, root = unboxingFilter(logicBox=collection['filter'], checker=checker)

    check_code = Grl.deterministicHash(F"{expression}{dataset['dataset_id']}{dataset['collection_id']}")

    if check_code not in checker:
        checker[check_code] = 'in'
    else:
        return ""

    # WRITE THE RESOURCE SELECTION ID AND THE TYPE OF THE RESOURCE
    writer.write(F"\n\n### RESOURCE {id}\n")
    writer.write(F"{Rsc.ga_resource_ttl(F'ResourceSelection-{id}')}\n\n")
    writer.write(preVal('a', F"{Sns.VoID.dataset_ttl}, {LLns.EntitySelection_ttl}"))

    # LABEL AND  DESCRIPTION IF THEY EXISTS
    if len(label.strip()) > 0:
        writer.write(preVal(Sns.RDFS.label_ttl, Literal(label, lang='en').n3()))
    if len(description.strip()) > 0:
        writer.write(preVal(Sns.DCterms.description_ttl, Literal(description, lang='en').n3()))

    # DATASET AND DATA-TYPE
    writer.write(preVal(LLns.subset_of_ttl, Rsc.ga_resource_ttl(dataset['dataset_id'])))

    # DATASET NAME
    writer.write(preVal(Sns.DCterms.identifier_ttl, Rsc.literal_resource(dataset['name'])))

    # FORMULATION
    formulation_code = Rsc.ga_resource_ttl(F"Formulation-{Grl.deterministicHash(expression)}")
    writer.write(preVal(LLns.hasFormulation_ttl, formulation_code,  end=True))

    # FORMULATION HAS CLASS PARTITION
    class_partition = F"[ {Sns.VoID.voidClass_ttl} {Rsc.ga_resource_ttl(dataset['collection_id'])} ]"
    class_partition_rsc = Rsc.ga_resource_ttl(F"ClassPartition-{Grl.deterministicHash(class_partition)}")

    writer.write(F"\n\n### CLASS PARTITION OF RESOURCE {id}\n")
    writer.write(F"{class_partition_rsc}\n")
    writer.write(preVal('a', F"{LLns.ClassPartition_ttl}"))
    writer.write(preVal(Sns.VoID.voidClass_ttl, Rsc.ga_resource_ttl(dataset['short_uri']), end=True))

    writer.write(F"\n\n### FORMULATION OF RESOURCE {id}\n")
    writer.write(F"{formulation_code}\n\n")
    writer.write(preVal('a', F"{LLns.PartitionFormulation_ttl}"))
    writer.write(preVal(LLns.hasItem_ttl, class_partition_rsc, end=True if not pred_selections else False))

    # PREDICATE SELECTION
    # writer.write("\n" if pred_selections else "")
    writer.write(pred_selections)

    # FORMULA EXPRESSION
    if expression :
        writer.write("\n")
        writer.write(preVal(
            LLns.formulaDescription_ttl, Literal(F"{class_partition_rsc} AND {expression}", lang='en').n3(), end=False))

        root.parent = Node("AND")
        Node(class_partition_rsc, parent=root.parent)
        f_tree = '\n\t'.join(
            ["%s%s" % (pre, node.name) for pre, fill, node in RenderTree(root.parent, style=DoubleStyle)])

        writer.write("\n")
        writer.write(
            preVal(LLns.formulaTree_ttl, Literal(F"\n\t{f_tree}", lang='en').n3(),
                   end=True))

        # print(f_tree)

    # FORMULA SEQUENCES
    writer.write(sequences)

    return writer.getvalue()


# Method for printing the linkset specs
def printSpecs(data, tab=1):
    example = "\t"
    pad = 60

    for i, (key, val) in enumerate(data.items()):

        # DICTIONARY
        if isinstance(val, dict):
            if tab == 1:
                print(F"\n{tab * example} {key} {{{i+1}/{len(data)}}}")
            else:
                print(F"{tab * example}- {key} {{{i+1}/{len(data)}}}")
            printSpecs(val, tab=tab + 1)

        # LIST OBJECT
        elif isinstance(val, (list, set)):
            if tab == 1:
                print(F"\n{tab * example} {key} [{len(val)}]")
            else:
                print(F"{tab * example}- {key} [{len(val)}]")

            for counter, item in enumerate(val):
                # print(F"{tab * example}\t{counter + 1}. {item}")
                if isinstance(item, dict):
                    if tab == 1:
                        print(F"\n{tab * example}\t- {key} [{counter + 1}/{len(val)}] {{{len(item)}}}")
                    else:
                        print(F"{tab * example}\t- {key} [{counter + 1}/{len(val)}] {{{len(item)}}}")
                    printSpecs(item, tab=tab + 2)
                else:
                    print(F"{tab * example}\t  {counter+1}. {item}")
        else:
            print(F"{tab * example}- {key:{pad - (tab - 1) * 4}}: {val}")


# CODE TO GENERATE THE FORMULA EXPRESSION OF THE FILTER LOGIC BOX OF THE SELECTED ENTITY
def filter_formula(filter_list, parent=None):

    # List of conditions
    for condition in filter_list:
        temp = Buffer()

        # New nested list of conditions
        if 'conditions' in condition:
            node = Node(condition['type'], parent=parent)
            filter_formula(condition['conditions'], parent=node)

        else:
            # Sequence for generating the resource hash code
            sequence = rdfSequence(
                condition[Vars.filterTtlProperty]
                if Vars.filterTtlProperty in condition and len(condition[Vars.filterTtlProperty]) > 0
                else condition[Vars.uri_properties]
                if Vars.uri_properties in condition else condition[Vars.filterProperty])

            # print(item[Vars.filterProperty], sequence[1])
            seq_function = condition[Vars.filterType] if Vars.filterType in condition else ""
            seq_value = condition[Vars.filterValue] if Vars.filterValue in condition else ""
            seq_format = condition[Vars.format] if Vars.format in condition else ""

            new_info = len(seq_function) > 0 or len(seq_value) > 0 or len(seq_format) > 0

            if new_info is True:

                # THE FILTER FUNCTION
                if len(seq_function) > 0:
                    temp.write(
                        preVal(LLns.filterFunction_ttl, Literal(seq_function, lang='en').n3()))

                # THE FILTER VALUE
                if len(seq_value) > 0:
                    temp.write(preVal(LLns.filterValue_ttl, Literal(seq_value, lang='en').n3()
                    if Grl.isDecimalLike(seq_value) is False else seq_value))

                # THE FILTER FORMAT TO APPLY
                if len(seq_format) > 0:
                    temp.write(preVal(LLns.filterFormat_ttl, Literal(seq_format, lang='en').n3()))

            code = Rsc.ga_resource_ttl(F"PropertyPartition-{Grl.deterministicHash(sequence[0] + temp.getvalue())}")

            node = Node(code, parent=parent)
            # print(condition)


# CODE TO GENERATE THE FORMULA EXPRESSION OF THE METHOD'S LOGIC BOX
def method_formula(filter_list, parent=None):

    # List of conditions
    for condition in filter_list:
        temp = Buffer()

        # New nested list of conditions
        if 'conditions' in condition:
            # recursive call
            method_formula(condition['conditions'], parent=Node(condition['type'], parent=parent))

        else:
            # print(condition, "\n")
            ttl_algorithm = condition['method_name'].split(":")

            # THE ALGORITHM CONDITION URI
            seq_code = F"{ttl_algorithm[1]}-{Grl.deterministicHash(condition)}" \
                if len(ttl_algorithm) > 1 else F"{condition['method_name']}-{Grl.deterministicHash(condition)}"

            code = Rsc.ga_resource_ttl(F"{seq_code}")
            Node(code, parent=parent)


# THE UNBOXING OF THE LINKSET SPECIFICATIONS
def unboxingLinksetSpecs(specs: dict, triples: bool = True):

    formula_parts = set()
    lset = Buffer()
    main_expression = deque()
    formula_tracking = deque()
    checker = defaultdict(str)

    def header(x, lines=2):
        liner = "\n"
        return F"{liner * lines}{'#'*80:^110}\n{' '*15}#{x:^78}#\n{'#'*80:^110}{liner * (lines-1)}"

    methods_descriptions = Buffer()
    methods_descriptions.write(header("METHODS'S DESCRIPTION", lines=2))

    def genericStats(linksetStats: dict):

        stats = Buffer()
        stats.write("\n\t### VOID LINKSET STATS\n")

        if Vars.triples in linksetStats and linksetStats[Vars.triples] and linksetStats[Vars.triples] > -1:
            stats.write(preVal(Sns.VoID.triples_ttl, linksetStats[Vars.triples]))

        if Vars.entities in linksetStats and linksetStats[Vars.entities] and linksetStats[Vars.entities] > -1:
            stats.write(preVal(Sns.VoID.entities_ttl, linksetStats[Vars.entities]))

        if Vars.distinctSub in linksetStats and linksetStats[Vars.distinctSub] and linksetStats[Vars.distinctSub] > -1:
            stats.write(preVal(Sns.VoID.distinctSubjects_ttl, linksetStats[Vars.distinctSub]))

        if Vars.distinctObj in linksetStats and linksetStats[Vars.distinctObj] and linksetStats[Vars.distinctObj] > -1:
            stats.write(preVal(Sns.VoID.distinctObjects_ttl, linksetStats[Vars.distinctObj]))

        stats.write("\n\t### LENTICULAR LENS LINKSET STATS\n")

        if Vars.clusters in linksetStats and linksetStats[Vars.clusters] and linksetStats[Vars.clusters] > -1:
            stats.write(preVal(LLns.cluster_ttl, linksetStats[Vars.clusters]))

        if Vars.validations in linksetStats and linksetStats[Vars.validations] and linksetStats[Vars.validations] > -1:
            stats.write(preVal(LLns.validations_tt, linksetStats[Vars.validations]))

        if Vars.remains in linksetStats and linksetStats[Vars.remains] and linksetStats[Vars.remains] > -1:
            stats.write(preVal(LLns.remains_ttl, linksetStats[Vars.remains]))

        if Vars.contradictions in linksetStats and linksetStats[Vars.contradictions] and linksetStats[Vars.contradictions] > -1:
            stats.write(preVal(LLns.contradictions_tt, linksetStats[Vars.contradictions]))

        stats.write("\n")

        return stats.getvalue()

    # Generic description of a linkset/les
    def genericDes(linksetSpecs: dict):

        g_meta = Buffer()
        g_meta.write(header('GENERIC METADATA', lines=2))

        # 1. The LINKSET'S NAME OR ID
        uri = linksetSpecs[Vars.id]
        g_meta.write(F"\n\n### LINKSET {uri}\n")
        g_meta.write(F"linkset:{uri}\n\n")
        # g_meta.write(preVal('a', Sns.VoID.linkset_ttl))
        g_meta.write(preVal('a', LLns.Linkset_ttl))

        # LINKSET FORMAT (TURTLE)
        g_meta.write(preVal(Sns.VoID.feature_ttl, Sns.Formats.turtle_ttl))

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

        # LINKSET LINKTYPE
        g_meta.write(preVal(Sns.VoID.linkPredicate_tt, linksetSpecs[Vars.linkType]))

        # 2. USER'S LABEL
        if len(Literal(linksetSpecs[Vars.label].strip())) > 0:
            g_meta.write(preVal(Sns.RDFS.label_ttl, Literal(linksetSpecs[Vars.label], lang='en').n3()))

        # 3. LINKSET DESCRIPTION
        if Vars.description in linksetSpecs and len(Literal(linksetSpecs[Vars.description].strip())) > 0:
            g_meta.write(preVal(
                Sns.DCterms.description_ttl, Literal(linksetSpecs[Vars.description], lang='en').n3()))
            g_meta.write("\n")

        # LINKSET STATS
        g_meta.write(genericStats(specs[Vars.linksetStats]))

        g_meta.write("\t### SOURCE ENTITY TYPE SELECTION(S)\n")
        # 4. SELECTED ENTITY AT THE SOURCE
        g_meta.write("".join(preVal(
            LLns.subTarget_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{selection[Vars.id]}"))
                             for selection in linksetSpecs[Vars.sources]))

        g_meta.write("\n\t### TARGET ENTITY TYPE SELECTION(S)\n")
        g_meta.write("".join(preVal(
            LLns.objTarget_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{selection[Vars.id]}"))
                             for selection in linksetSpecs[Vars.targets]))

        g_meta.write("\n\t### THE LOGIC FORMULA\n")
        g_meta.write(preVal(LLns.formulation_ttl, Rsc.ga_resource_ttl("###FORMULA URI###"), end=True))

        # return F"{g_meta.getvalue().rstrip()[:-1]}.\n\n"
        return g_meta.getvalue()

    # Documentation of the selected resource by unboxing the collection filter
    def resourceSelection(linksetSpecs):

        entity_constraints = Buffer()
        entity_constraints.write(F"{header('RESOURCE SELECTIONS')}")

        # AT THE SOURCE OR TARGET, THERE CAN EXIST MORE THAN ONE SELECTED RESOURCE
        for logic_box in linksetSpecs[Vars.sources]:
            # print(F"1")
            filter_triples = unboxingFilterBox(logic_box, checker)
            if filter_triples not in checker:
                checker[filter_triples] = "in"
                entity_constraints.write(filter_triples)

        # Source selected at the target
        if linksetSpecs[Vars.sources] != linksetSpecs[Vars.targets]:
            for logic_box in linksetSpecs[Vars.targets]:
                # print("--->", logic_box)
                filter_triples = unboxingFilterBox(logic_box, checker)
                if filter_triples not in checker:
                    checker[filter_triples] = "in"
                    entity_constraints.write(F"{filter_triples}")

        # print(entity_constraints.getvalue())
        return F"{entity_constraints.getvalue().rstrip()[:-1]}.\n"

    # ### METHOD SPECIFICATIONS --- ### SOURCE
    def unboxingAlgorithm(method: dict):

        # print(F"\n\n{algorithm}")
        algo_writer = Buffer()
        pred_sel_writer = Buffer()
        pred_sequences_writer = Buffer()
        algo_name = method[Vars.methodName]

        # COMPATIBILITY
        algo_name = Algorithm.exact_ttl if algo_name == "=" else algo_name

        ttl_algo = algo_name.split(":")

        # THE ALGORITHM CONDITION URI
        seq_code = F"{ttl_algo[1]}-{Grl.deterministicHash(method)}" \
            if len(ttl_algo) > 1 else F"{algo_name}-{Grl.deterministicHash(method)}"

        if algo_name not in checker:
            checker[algo_name] = 'i'
            methods_descriptions.write(F"\n\n### ALGORITHM : {algo_name}")
            methods_descriptions.write(F"\n{Rsc.ga_resource_ttl(algo_name)}\n\n")
            methods_descriptions.write(preVal('a', LLns.MatchingAlgorithm_ttl))
            methods_descriptions.write(preVal(Sns.DCterms.description_ttl, Algorithm.illustration(algo_name), end=True))

        algo_writer.write(F"\n\n### METHOD SPECIFICATIONS {algo_name}\n")
        algo_writer.write(F"{Rsc.ga_resource_ttl(seq_code)}\n\n")
        algo_writer.write(preVal('a', LLns.MatchingMethod_ttl))

        # ALGORITHM NAME - OPERATOR - THRESHOLD - THRESHOLD RANGE
        algo_writer.write(preVal(LLns.method_ttl, Rsc.ga_resource_ttl(algo_name)))

        if Vars.threshold_operator in method:
            algo_writer.write(preVal(LLns.simOperator_ttl, Rsc.ga_resource_ttl(method[Vars.threshold_operator])))

        if Vars.threshold in method:
            algo_writer.write(preVal(LLns.threshold_ttl, method[Vars.threshold]))
        algo_writer.write(preVal(LLns.thresholdRange_ttl, Literal(Algorithm.range(algo_name)).n3()))

        def entitySelections(method_cont, subject=True):

            # LIST OF SOURCE PROPERTIES SELECTIONS
            algo_writer.write("\n\t### SOURCE PREDICATE CONFIGURATION\n"
                              if subject is True else "\n\t### TARGET PREDICATE CONFIGURATION\n")

            predicate_type = LLns.entitySelectionSubj_ttl if subject is True else LLns.entitySelectionObj_ttl

            sources = method[method_cont]

            for item in sources:

                ent_sel = item[Vars.entityTypeSelection]

                # A SELECTED PROPERTY PATH
                if len(item[Vars.property]) > 1:

                    # GET THE PROPERTY PATH SEQUENCE AND ITS URI
                    # src_sequence = rdfSequence(item[Vars.property])
                    src_sequence = rdfSequence(item[Vars.filterTtlProperty] if len(item[Vars.filterTtlProperty]) > 0 else item[Vars.uri_properties])

                    # THE SELECTED PROPERTY IS COUPLED WITH ITS ORIGIN
                    # (DATASET - DATA-TYPE) SO WE GENERATE A NEW URI FOR IT
                    sel_code = Grl.deterministicHash(F"{ent_sel}{src_sequence[1]}")
                    algo_writer.write(preVal(predicate_type, Rsc.ga_resource_ttl(F"ResourceSelection-{sel_code}")))

                    # GATHER THE ACTUAL PREDICATE
                    predicate_uri = src_sequence[1]

                    # WRITING THE SEQUENCE
                    if src_sequence[1] not in checker:
                        pred_sequences_writer.write(F"\n\n{src_sequence[0].rstrip()[:-1]}.\n")
                        checker[src_sequence[1]] = str(src_sequence[0])

                # A SINGLE PROPERTY
                else:
                    sel_code = Grl.deterministicHash(F"{ent_sel}{item[Vars.property][0]}")
                    # predicate_uri = Rsc.ga_resource_ttl(item[Vars.property][0])
                    predicate_uri = Rsc.ga_resource_ttl(item[Vars.filterTtlProperty][0] if len(item[Vars.filterTtlProperty]) > 0 else item[Vars.uri_properties])
                    algo_writer.write(preVal(predicate_type, Rsc.ga_resource_ttl(F"ResourceSelection-{sel_code}")))

                # PREDICATE SELECTION
                if sel_code not in checker:
                    checker[sel_code] = "in"
                    pred_sel_writer.write(F'\n\n{Rsc.ga_resource_ttl(F"ResourceSelection-{sel_code}")}\n')
                    pred_sel_writer.write(preVal('a', LLns.EntitySelection_ttl))

                    # SUBSET
                    pred_sel_writer.write(preVal(LLns.subset_of_ttl, Rsc.ga_resource_ttl(F"ResourceSelection-{ent_sel}")))

                    # SEQUENCE / FORMULATION
                    if predicate_uri.__contains__("resource:"):
                        pred_sel_writer.write(preVal(LLns.hasFormulation_ttl, F"[ {LLns.hasItem_ttl}\t{predicate_uri} ]", end=True))
                    else:
                        pred_sel_writer.write(preVal(LLns.hasFormulation_ttl, F"[ {LLns.hasItem_ttl}\t[ {Sns.VoID.property_ttl} {predicate_uri} ] ]", end=True))

        entitySelections(Vars.sources, subject=True)
        entitySelections(Vars.targets, subject=False)

        # print(F">>>{pred_sequences_writer.getvalue()}")

        return F"{algo_writer.getvalue().rstrip()[:-1]}.\n", pred_sel_writer.getvalue(), \
               pred_sequences_writer.getvalue(), seq_code

    def unboxingMethodsBox(methodBox: dict, position=0):

        methods = Buffer()
        methods_predicates = Buffer()
        methods_sequences = Buffer()

        methods.write(header('METHOD SIGNATURES', lines=1) + "\n")
        methods_predicates.write(header("METHODS'S PREDICATE SELECTIONS", lines=2))
        methods_sequences.write(header("METHODS'S PREDICATE SEQUENCES", lines=2))

        counter = [0]
        test = deque()

        def writeMethodsBox(mtdBox: dict, pos=position):

            box_list = mtdBox["conditions"]
            operator = F" {mtdBox[Vars.filterType].upper()} "

            # LIST OF BOXES OR NESTED BOXES
            codes = deque()

            formula_tree, f_expression = None, None
            if 'conditions' in mtdBox and mtdBox['conditions']:
                # The formula root tree
                root = Node(mtdBox['type'])
                # Generating the method formula tree
                method_formula(mtdBox['conditions'], parent=root)
                # List of operations in post order for generating the formula expression
                post_order = [node.name for node in PostOrderIter(root)]
                # A copy of the rendered formula tree
                formula_tree = '\n\t'.join(
                    ["%s%s" % (pre, node.name) for pre, fill, node in RenderTree(root, style=DoubleStyle)])
                # The method's formula expression
                f_expression = expression_generator(post_order)[0]
                # print(formula_tree)
                # print(f_expression)

            for method_item in box_list:

                if "conditions" not in method_item:

                    algorithm, predicate_selections, seq_predicates, code = unboxingAlgorithm(method_item)

                    # APPEND CODE FOR THE LOGIC FORMULA
                    codes.append(code)

                    # WRITE THE CURRENT METHOD
                    methods.write(algorithm)

                    # UPDATE THE ENTITY SELECTION WRITER
                    methods_predicates.write(predicate_selections)

                    # UPDATE THE SEQUENCE WRITER
                    methods_sequences.write(seq_predicates)

                else:

                    # RECURSION
                    counter[0] = counter[0] + 1
                    x, y, z = writeMethodsBox(method_item, counter[0])
                    # print(pos, x)

                    test.appendleft(x)

                    formula_tracking.appendleft(F"{{{pos}}} {operator} ({{{x}}})")

            # THIS IS TO CREATE THE PARTS IN THE LOGIC EXPRESSION
            formula_parts.update({Rsc.ga_resource_ttl(code) for code in codes})

            formulation = F" {operator} ".join(Rsc.ga_resource_ttl(code) for code in codes)

            main_expression.appendleft(formulation)

            return pos, formula_tree, f_expression

        # ::: END OF FUNCTION writeMethodsBox ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        # RUNNING THE WRITE METHOD FUNCTION
        pos, f_tree, f_exp = writeMethodsBox(methodBox)

        # THE METHOD ALGORITHM DESCRIPTION
        methods.write(methods_descriptions.getvalue())

        # THE METHOD SELECTED PREDICATES
        methods.write(methods_predicates.getvalue())

        # THE SELECTED PREDICATES SEQUENCES
        if len(methods_sequences.getvalue()) > 320:
            methods.write(methods_sequences.getvalue())

        test.appendleft(0)

        if not formula_tracking:
            formula_tracking.append("{0}")

        temp = [0 for item in main_expression]
        for index, value in enumerate(test):
            temp[value] = main_expression[index]

        # Method no longer used
        # formula_expression = expressionFormatter(formula_tracking, temp)
        # print(formula_expression)
        # print(f_exp)

        return methods.getvalue(), f_tree, f_exp

    # 1. THE LINKSET NAMESPACES IS SET IN THE LINKSET AS THE auto_prefixes
    # DICTIONARY NEEDS TO BE UPDATES WHEN CONVERTING THE CSV FILE
    # lset.write(linksetNamespaces(auto_prefixes)

    # 2. LINKSET GENERIC AND STATS METADATA DESCRIPTION
    lset.write(genericDes(specs[Vars.linksetSpecs]))

    # 3. ENTITY SELECTION AND CONSTRAINTS
    lset.write(resourceSelection(specs[Vars.linksetSpecs]))

    # 4. THE LINKSET LOGIC EXPRESSION
    lset.write(header("LINKSET LOGIC EXPRESSION", lines=2))
    lset.write(F"\n\n{Rsc.ga_resource_ttl('###FORMULA URI###')}\n\n")
    lset.write(preVal('a', LLns.LogicFormulation_ttl))
    lset.write(F"### EXPRESSION PARTS ###")
    # NEW LINE INSIDE THE EXPRESSION TO FOR Literal TO WRITE IT AS """###LOGIC \n EXPRESSION###"""@en
    lset.write(F"\n")
    lset.write(preVal(LLns.formulaDescription_ttl, Literal('###LOGIC \n EXPRESSION###', 'en').n3(), end=False))
    lset.write(F"\n")
    lset.write(preVal(LLns.formulaTree_ttl, Literal('###LOGIC \n TREE###', 'en').n3(), end=True))
    lset.write("\n")

    # 5. THE DESCRIPTION OF THE METHODS INVOLVED IN THE CREATION OF LINKS.
    # THIS INCLUDES (1) THE METHOD SIGNATURE (2) PREDICATES AND (3) PREDICATE PATHS
    method_description, f_tree, f_exp = unboxingMethodsBox(specs[Vars.linksetSpecs][Vars.methods])
    lset.write(method_description)

    # 6. UPDATING THE FORMULA IN STAND BY IN PART 4:
    # (1) FORMULA URI (2) LOGIC EXPRESSION AND (3) EXPRESSION PARTS
    # THIS CAN ONLY BE DONE AFTER THE METHOD [unboxingMethodsBox] IS EXECUTED
    parts = "".join(preVal(LLns.part_ttl, part) for part in formula_parts)
    temp = lset.getvalue().replace("###FORMULA URI###", Grl.deterministicHash(f_exp))
    # temp = temp.replace('###LOGIC \n EXPRESSION###', expression)
    temp = temp.replace('###LOGIC \n EXPRESSION###', f_exp)
    temp = temp.replace('###LOGIC \n TREE###', F"\n\t{f_tree}\n\t")
    resetBuffer(lset, temp.replace("### EXPRESSION PARTS ###", parts))

    return lset.getvalue()
