# SCRIPT OVERVIEW ######################################################################################################
#                                                                                                                      #
#   This keeps track of the namespace of the Lenticular Lenses Ontology used for documenting matching methods.         #
#   It defines:                                                                                                        #
#       1. prefixes:                                                                                                   #
#           ll      : http://lenticularlens.org/ontology/                                                              #
#           ll_algo : http://lenticularlens.org/ontology/matchingMethod/                                               #
#           ll_val  : http://lenticularlens.org/ontology/validation/                                                   #
#       2: Classes:                                                                                                    #
#           - ll:Linkset                                                                                               #
#           - ll:MatchingFormulation                                                                                   #
#           - ll:MatchingMethod                                                                                        #
#           - ll:ResourceSelection                                                                                     #
#           - ll:PropertySelection                                                                                     #
#           - ll:Validation                                                                                            #
#           - ll:PropertyConstraint                                                                                    #
#           - ll:MatchingAlgorithm                                                                                     #
#       3: Generic metadata                                                                                            #
#       4: specific metadata                                                                                           #
#                                                                                                                      #
# ######################################################################################################################

ll = 'http://lenticularlens.org/'
pref_size = 20


class LLNamespace:
    genericPrefix = "voidPlus"

    # ###############################################################################
    #                                     PREFIXES                                  #
    # ###############################################################################
    ontology = F'{ll}void+/'
    ontology_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."

    algorithm = F"{ontology}matchingMethod/"
    algorithm_prefix = F"@prefix {'ll_algo':>{pref_size}}: <{algorithm}> ."

    validation = F"{ontology}validation/"
    validation_prefix = F"@prefix {'ll_val':>{pref_size}}: <{validation}> ."

    resource = F"{ll}resource/"
    resource_prefix = F"@prefix {'resource':>{pref_size}}: <{resource}> ."

    linkset = F"{resource}linkset/"
    linkset_prefix = F"@prefix {'linkset':>{pref_size}}: <{resource}linkset/> ."

    lens = F"{resource}lens/"
    lens_prefix = F"@prefix {'lens':>{pref_size}}: <{resource}lens> ."

    # TYPES
    Project = F'{ontology}Project'
    Lens = F'{ontology}Lens'

    # ###############################################################################
    #                                   CLASSES                                     #
    # ###############################################################################
    Linkset = F'{ll}ontology/Linkset'
    Linkset_ttl = F'{genericPrefix}:Linkset'

    LogicFormulation = F'{ll}ontology/LinksetFormulation'
    LogicFormulation_ttl = F'{genericPrefix}:LinksetFormulation'

    MatchingMethod = F'{ll}ontology/MatchingMethod'
    MatchingMethod_ttl = F'{genericPrefix}:MatchingMethod'

    EntitySelection = F'{ll}ontology/ResourceSelection'
    EntitySelection_ttl = F'{genericPrefix}:ResourceSelection'

    PropertySelection = F'{ll}ontology/PropertySelection'
    PropertySelection_ttl = F'{genericPrefix}:PropertySelection'

    Validation = F'{ll}ontology/Validation'
    Validation_ttl = F'{genericPrefix}:Validation'

    PropertyPartition = F'{ll}ontology/PropertyPartition'
    PropertyPartition_ttl = F'{genericPrefix}:PropertyPartition'

    ClassPartition = F'{ll}ontology/ClassPartition'
    ClassPartition_ttl = F'{genericPrefix}:ClassPartition'

    PartitionFormulation = F'{ll}ontology/PartitionFormulation'
    PartitionFormulation_ttl = F'{genericPrefix}:PartitionFormulation'

    MatchingAlgorithm = F'{ll}ontology/MatchingAlgorithm'
    MatchingAlgorithm_ttl = F'{genericPrefix}:MatchingAlgorithm'

    ##############################################################################################################
    #                                              GENERIC METADATA                                              #
    ##############################################################################################################
    # linkset:Grid_2
    #     a                                        void:Linkset ;
    #     cc:attributionName                       "LenticularLens" ;
    #     void:feature                             format:Turtle ;
    # 	  cc:license                               <http://purl.org/NET/rdflicense/W3C1.0> ;
    # 	  void+:has-matching-logic-formulation     "<http://data.goldenagents.org/resource/EditDistance-H55b8f81b407d0ec>" ;
    #
    #     void:linkPredicate                       skos:exactMatch ;
    # 	  void:subjectsTarget                      <http://data.goldenagents.org/resource/dataset/Grid> ;
    # 	  void:objectsTarget                       <http://data.goldenagents.org/resource/dataset/Grid> ;
    #     dcterms:description                      "Deduplication of entities of type Education in the GRID dataset"@en ;
    #
    #     void:triples                             1692 ;
    #     void:entities                            1737 ;
    #     void:distinctSubjects                    1737 ;
    #     void:distinctObjects                     1737 ;
    #
    # 	  void:has-clusters                        619 ;
    # 	  ll_val:has-validations                   18 ;
    # 	  ll_val:has-accepted                      3 ;
    # 	  ll_val:has-rejected                      6 ;
    # 	  ll_val:has-remaining                     1683 .

    validation_tt = F"{genericPrefix}:hasValidation"

    contradictions_tt = F"{genericPrefix}:hasContradictions"

    validations_tt = F"{genericPrefix}:hasValidations"
    accepted_ttl = F"{genericPrefix}:hasAccepted"
    rejected_ttl = F"{genericPrefix}:hasRejected"
    remains_ttl = F"{genericPrefix}:hasRemaining"

    cluster = F"{ontology}hasClusters"
    cluster_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    cluster_ttl = F"{genericPrefix}:hasClusters"

    formulation = F"{ontology}hasFormulation"
    formulation_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    formulation_ttl = F'{genericPrefix}:hasFormulation'

    # The void:Dataset that contains the resources in the subject position of this void:Linkset's triples.
    subTarget = F"{ontology}subjectsTarget"
    subTarget_ttl = F"{genericPrefix}:subjectsTarget"

    # The void:Dataset that contains the resources in the object position of a void:Linkset's triples.
    objTarget = F"{ontology}objectsTarget"
    objTarget_ttl = F"{genericPrefix}:objectsTarget"

    # ###############################################################################
    #                             LOGIC FORMULA PARTS                               #
    # ###############################################################################

    part = F"{ontology}hasItem"
    part_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    part_ttl = F'{genericPrefix}:hasItem'

    formulaDescription = F"{ontology}hasFormulaDescription"
    formulaDescription_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    formulaDescription_ttl = F'{genericPrefix}:hasFormulaDescription'

    formulaTree = F"{ontology}hasFormulaTree"
    formulaTree_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    formulaTree_ttl = F'{genericPrefix}:hasFormulaTree'

    # ##############################################################################
    #                              METHOD SIGNATURES                               #
    # ##############################################################################
    # resource:EditDistance-H55b8f81b407d0ec
    # 	ll:has-matching-method                  ll_algo:EditDistance ;
    # 	ll:has-matching-threshold               0.9 ;
    # 	ll:link-acceptance-threshold-operator   <http://data.goldenagents.org/resource/Greater-than-or-equal-to> ;
    #
    # 	ll:has-subj-entity-selection            <http://data.goldenagents.org/resource/EntitySelection-PH61bd543e4ce34c2> ;
    # 	ll:has-subj-predicate-selected          <http://data.goldenagents.org/resource/PredicateSelection-PHab504e102405ab0> ;
    #
    # 	ll:has-obj-entity-selection             <http://data.goldenagents.org/resource/EntitySelection-PH61bd543e4ce34c2> ;
    # 	ll:has-obj-predicate-selected           <http://data.goldenagents.org/resource/PredicateSelection-PHab504e102405ab0> .

    method = F"{ontology}hasAlgorithm"
    method_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    method_ttl = F'{genericPrefix}:hasAlgorithm'

    threshold = F"{ontology}hasThreshold"
    threshold_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    threshold_ttl = F'{genericPrefix}:hasThreshold'

    thresholdRange = F"{ontology}hasThresholdRange"
    thresholdRange_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    thresholdRange_ttl = F'{genericPrefix}:hasThresholdRange'

    simOperator = F"{ontology}hasThresholdAcceptanceOperator"
    simOperator_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    simOperator_ttl = F'{genericPrefix}:hasThresholdAcceptanceOperator'

    strength = F"{ontology}hasMatchingStrength"
    strength_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    strength_ttl = F'{genericPrefix}:hasMatchingStrength'

    # A RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE AT THE SOURCE POSITION
    entitySelectionSubj = F"{ontology}hasSubjResourceSelection"
    entitySelectionSubjPrefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    entitySelectionSubj_ttl = F'{genericPrefix}:hasSubjResourceSelection'

    # A RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE AT THE TARGET POSITION
    entitySelectionObj = F"{ontology}hasObjResourceSelection"
    entitySelectionObj_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    entitySelectionObj_ttl = F'{genericPrefix}:hasObjResourceSelection'

    # THE URI OF GHE SELECTED ALGORITHM
    method_hash = F"{ontology}hasMatchingMethodHash"
    method_hash_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    method_hash_ttl = F'{genericPrefix}:hasMatchingMethodHash'

    sub_predicate_selected = F"{ontology}hasSubjPredicateSelection"
    sub_predicate_selected_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    sub_predicate_selected_ttl = F'{genericPrefix}:hasSubjPredicateSelection'

    obj_predicate_selected = F"{ontology}hasObjPredicateSelection"
    obj_predicate_selected_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    obj_predicate_selected_ttl = F'{genericPrefix}:hasObjPredicateSelection'

    # ##############################################################################
    #                        DATASET AND ENTITY SELECTIONS                         #
    # ##############################################################################
    #  resource:EntitySelection-PH61bd543e4ce34c2
    # 	ll:has-selected-dataset                 <http://data.goldenagents.org/resource/dataset/Grid> ;
    # 	ll:has-selected-data_type               <http://www.grid.ac/ontology/Education> .

    # THE SELECTED RESOURCE IF SUBSET OF A DATASET
    subset_of = F"{ontology}subsetOf"
    subset_of_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    subset_of_ttl = F'{genericPrefix}:subsetOf'

    # HAS FORMULATION
    hasFormulation = F"{ontology}hasFormulation"
    hasFormulation_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    hasFormulation_ttl = F'{genericPrefix}:hasFormulation'

    # HAS ITEM
    hasItem = F"{ontology}hasItem"
    hasItem_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    hasItem_ttl = F'{genericPrefix}:hasItem'

    # THE SELECTED DATASET FOR THE ENTITY SELECTED RESOURCE
    dataset = F"{ontology}hasDataset"
    dataset_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    dataset_ttl = F'{genericPrefix}:hasDataset'

    # THE SELECTED DATA TYPE FOR THE ENTITY SELECTED RESOURCE
    dataType = F"{ontology}hasEntityType"
    dataType_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    dataType_ttl = F'{genericPrefix}:hasEntityType'

    filterFunction = F"{ontology}hasFilterFunction"
    filterFunction_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    filterFunction_ttl = F'{genericPrefix}:hasFilterFunction'

    filterValue = F"{ontology}hasValueFunction"
    filterValue_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    filterValue_ttl = F'{genericPrefix}:hasValueFunction'

    filterFormat = F"{ontology}hasFormatFunction"
    filterFormat_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    filterFormat_ttl = F'{genericPrefix}:hasFormatFunction'

    # ##############################################################################
    #                             PREDICATE SELECTIONS                             #
    # ##############################################################################
    # resource:PredicateSelection-PHab504e102405ab0
    # 	ll:has-entity-selected                  resource:EntitySelection-PH61bd543e4ce34c2> ;
    # 	ll:has-subj-predicate                   <http://www.w3.org/2000/01/rdf-schema#label> .

    # THE URI OF THE RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE
    entity_selected = F"{ontology}hasEntitySelection"
    entity_selected_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    entity_selected_ttl = F'{genericPrefix}:hasEntitySelection'

    predicate = F"{ontology}hasPredicate"
    predicate_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    predicate_ttl = F'{genericPrefix}:hasPredicate'

    # ##############################################################################
    #                                 LENS OPERATORS                               #
    # ##############################################################################

    operator = F"{ontology}lensOperator/"

    union = F"{operator}union"
    union_prefix = F"@prefix {'ll_operator':>{pref_size}}: <{operator}> ."
    union_ttl = F"ll_operator:union"

    intersection = F"{operator}intersection"
    intersection_prefix = F"@prefix {'ll_operator':>{pref_size}}: <{operator}> ."
    intersection_ttl = F"ll_operator:intersection"

    transitive = F"{operator}transitive"
    transitive_prefix = F"@prefix {'ll_operator':>{pref_size}}: <{operator}> ."
    transitive_ttl = F"ll_operator:transitive"

    difference = F"{operator}difference"
    difference_prefix = F"@prefix {'ll_operator':>{pref_size}}: <{operator}> ."
    difference_ttl = F"ll_operator:difference"

    composition = F"{operator}composition"
    composition_prefix = F"@prefix {'ll_operator':>{pref_size}}: <{operator}> ."
    composition_ttl = F"ll_operator:composition"

    # ##############################################################################
    #                             ...................                             #
    # ##############################################################################

    mechanism = F"{ontology}hasMatchingMechanism"
    mechanism_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    mechanism_ttl = F"{genericPrefix}:hasMatchingMechanism"

    justification = F"{ontology}hasMatchingJustification"
    justification_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    justification_ttl = F"{genericPrefix}:hasMatchingJustification"

    view = F"{ontology}hasView/"
    view_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    view_ttl = F"{genericPrefix}:hasView"

    cluster_ID = F"{ontology}hasClustersID"
    cluster_ID_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    cluster_ID_ttl = F"{genericPrefix}:hasClustersID"

    clusterConstraint = F"{ontology}hasClusterConstrain"
    clusterConstraint_prefix = F"@prefix {F'{genericPrefix}':>{pref_size}}: <{ontology}> ."
    clusterConstraint_ttl = F"{genericPrefix}:hasClusterConstrain"

    # ##############################################################################
    #                                    LINKSET                                  #
    # ##############################################################################

    link_validation_tt = F"{genericPrefix}:hasLinkValidation"
