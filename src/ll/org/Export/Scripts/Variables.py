# >>> from types import SimpleNamespace
# >>> d = {'key1': 'value1', 'key2': 'value2'}
# >>> n = SimpleNamespace(**d)

# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   LIST OF VARIABLES USED in the lenticular lens.                                                        #
#                                                                                                         #
# #########################################################################################################

job_id = "job_id"

# ##################################
#        LINKSET STATISTICS        #
# ##################################
linksetStats = 'linksetStats'
lensStats = 'lensStats'
triples = 'links_count'

distinctLinkedEntities = 'linkset_entities_count'
distinctSub = 'linkset_sources_count'
distinctObj = 'linkset_targets_count'

distinctSourceEntities = 'sources_count'
distinctTargetEntities = 'targets_count'
distinctSrcTrgEntities = 'entities_count'

clusters = 'clusters_count'

accepted = 'accepted'
rejected = 'rejected'
mixed = 'mixed'
notValidated = 'not_validated'
remains = 'remains'
validations = 'validations'
not_sure = 'not_sure'

contradictions = 'contradictions'

dataset = 'dataset'

# ##################################
#       LINKSET SPECIFICATIONS     #
# ##################################
linksetSpecs = 'linksetSpecs'
lensSpecs = 'lensSpecs'
id = 'id'
label = "label"
linkType = 'linkType'
description = 'description'
sources = 'sources'
targets = 'targets'
methods = 'methods'
properties = 'properties'
short = 'short'
long = 'long'

# ##################################
#   ENTITY FILTER SPECIFICATIONS   #
# ##################################
selectionFilter = "filter"
filterConditions = "conditions"
filterProperty = "property"
short_properties = "short_properties"
filterType = "type"
filterValue = "value"
filterFormat = "format"
operator = "type"

# ##################################
#     METHODS SPECIFICATIONS      #
# ##################################
# methods = "methods"
# operator = "type"
conditions = "conditions"
methodName = "name"
methodValue = "method_value"
# sources = 'sources'
entityTypeSelection = "entity_type_selection"
sim_config = 'sim_config'
normalized = 'normalized'

property = "property"
transformers = "transformers"
name = "name"
parameters = "parameters"
format = "format"
# targets = 'targets'


long_properties = 'long_properties'
source_predicates = "source_predicates"
target_predicates = "target_predicates"
algorithm = "algorithm"
threshold = "threshold"
threshold_operator = "threshold_operator"
prefix_weight = "prefix_weight"
max_distance = "max_distance"
soundex_size = "size"
Bloothooft_name_type = "name_type"

UNIT = "unit"

# ###############################################################################
#                          T-NORMS AND T-CONORMS LABELS                        #
# ###############################################################################
# MINIMUM = "⊤min"
# PRODUCT = "⊤prod"
# LUK = "⊤Luk"
# DRASTIC = "⊤D"
# NILPOTENT = "⊤nM"
# HAMACHER = "⊤H0"

MIN = 'minimum'
MAX = 'maximum'
minimum = 'minimum'
hamacher = 'hamacher'
prod = 'product'
product = 'product'
nil = 'nilpotent'
nilpotent = 'nilpotent'
luk = 'luk'
drastic = 'drastic'


# Predicate length in the turtle file format
PRED_SIZE = 55

# Prefix length in the turtle file format
PREF_SIZE = 20


# The golden agent domain
DOMAIN_NAME = "lenticularlens.org"


# THe Golden Agent Lenticular Lens namespace
LL = F"https://{DOMAIN_NAME}/"


RESOURCE = F"{LL}resource/"


LOV = "https://lov.linkeddata.es/dataset/lov/sparql"


RIGHHTS = "http://purl.org/NET/rdflicense/W3C1.0"
# http://www.w3.org/Consortium/Legal/2015/copyright-software-and-document


# W3C Software Notice and License
LICENCE = "http://purl.org/NET/rdflicense/W3C1.0"


# http://rdflicense.appspot.com/rdflicense/W3C1.0.ttl
legalcode = """
        ----------------
             LICENCE
        ----------------
        By obtaining, using and/or copying this work, you (the licensee) agree that you have read, understood,  
        and will comply with the following terms and conditions. 
        Permission to copy, modify, and distribute this software and its documentation, with or without  
        modification, for any purpose and without fee or royalty is hereby granted, provided that you include 
        the following on ALL  copies of the software and documentation or portions thereof, including modifications: 
        The full text of this NOTICE in a location viewable to users of the redistributed or derivative work. Any 
        pre-existing intellectual property disclaimers, notices, or terms and conditions. If none exist, the W3C 
        Software Short Notice should be included (hypertext is preferred, text is permitted) within the body of any 
        redistributed or derivative code.
        Notice of any changes or modifications to the files, including the date changes were made. (We recommend you 
        provide URIs to the location from which the code is derived.)
        ----------------
           DISCLAIMERS
        ----------------
        THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS," AND COPYRIGHT HOLDERS MAKE NO REPRESENTATIONS OR  
        WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY OR FITNESS  
        FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD  
        PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.
        COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING  
        OUT OF ANY USE OF THE SOFTWARE OR DOCUMENTATION.
        The name and trademarks of copyright holders may NOT be used in advertising or publicity pertaining to the 
        software without specific, written prior permission. Title to copyright in this software and any associated 
        documentation will at all times remain with copyright holders.
        ----------------
             NOTES
        ----------------
        This version: http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
        This formulation of W3C's notice and license became active on December 31 2002. This version removes the 
        copyright ownership notice such that this license can be used with materials other than those owned by  
        the W3C, reflects that ERCIM is now a host of the W3C, includes references to this specific dated version  
        of the license, and removes the ambiguous grant of "use". Otherwise, this version is the same as the 
        previous version and is  written so as to preserve the Free Software Foundation's assessment of GPL 
        compatibility and OSI's certification  under the Open Source Definition.
"""


def threshold_operators(operator: str):

    return {

        '<': 'Less-than',
        'LESS THAN': 'Less-than',

        '<=': 'Less-than-or-equal-to',
        'LESS EQUAL': 'Less-than-or-equal-to',
        'LESS THAN OR EQUAL TO': 'Less-than-or-equal-to',

        '>': 'Greater-than',
        'GREATER THAN': 'Greater-than',

        '>=': 'Greater-than-or-equal-to',
        'GREATER EQUAL': 'Greater-than-or-equal-to',
        'GREATER THAN OR EQUAL TO': 'Greater-than-or-equal-t0',

        '=': 'Equal',
        'EQUAL': 'Equal'}.get(operator.upper(), None)


norms_format = {

    'min': '⊤min',
    'minimum': '⊤min',

    'hamacher': '⊤H0',

    'prod': '⊤prod',
    'product': '⊤prod',

    'nil': '⊤nM',
    'nilpotent': '⊤nM',

    'luk': '⊤Luk',

    'drastic': '⊤D'
}

conorms_format = {

    'max': '⊥max',
    'maximum': '⊥max',

    'prob': '⊥sum',
    "probabilistic": "⊥sum",
    "probabilistic sum": "⊥sum",

    'bounded': '⊥Luk',
    'bounded sum ': '⊥Luk',

    'drastic': '⊥D',

    'nil': '⊤nM',
    'nilpotent': '⊥nM',
    'nil max': '⊥nM',
    'nilpotent maximum': '⊥nM',

    'einstein': '⊥D',
    'einstein sum': '⊥D'
}
