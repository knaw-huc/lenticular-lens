from ll.org.Export.Scripts.Variables import PREF_SIZE, LL

# SCRIPT OVERVIEW ######################################################################################################
#                                                                                                                      #
#   This keeps track of the namespace of the Lenticular Lens Ontology used for documenting matching methods.           #
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


class VoidPlus:

    genericPrefix = "voidPlus"
    resource_ns = F"{LL}resource/"

    # ###############################################################################
    #                                     PREFIXES                                  #
    # ###############################################################################
    ontology = F'{LL}voidPlus/'
    ontology_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."

    algorithm = F"{ontology}matchingMethod/"
    algorithm_prefix = F"@prefix {'ll_algo':>{PREF_SIZE}}: <{algorithm}> ."

    validation = F"{ontology}validation/"
    validation_prefix = F"@prefix {'ll_val':>{PREF_SIZE}}: <{validation}> ."

    # TYPES
    Project = F'{ontology}Project'

    # ###############################################################################
    #                                   CLASSES                                     #
    # ###############################################################################

    Linkset = F'{ontology}Linkset'
    Linkset_ttl = F'{genericPrefix}:Linkset'

    Lens = F'{ontology}Lens'
    Lens_ttl = F'{genericPrefix}:Lens'

    Cluster = F'{ontology}Cluster'
    Cluster_ttl = F'{genericPrefix}:Cluster'

    Clusterset = F'{ontology}Clusterset'
    Clusterset_ttl = F'{genericPrefix}:Clusterset'

    Validation = F'{ontology}Validation'
    Validation_ttl = F'{genericPrefix}:Validation'

    Validationset = F'{ontology}Validationset'
    Validationset_ttl = F'{genericPrefix}:Validationset'

    ValidationFlag = F'{ontology}ValidationFlag'
    ValidationFlag_ttl = F'{genericPrefix}:ValidationFlag'

    LinksetLogicFormulation = F'{ontology}LinksetFormulation'
    LinksetLogicFormulation_ttl = F'{genericPrefix}:LinksetFormulation'

    LensFormulation = F'{ontology}LensFormulation'
    LensFormulation_ttl = F'{genericPrefix}:LensFormulation'

    MatchingMethod = F'{ontology}MatchingMethod'
    MatchingMethod_ttl = F'{genericPrefix}:MatchingMethod'

    EntitySelection = F'{ontology}ResourceSelection'
    EntitySelection_ttl = F'{genericPrefix}:ResourceSelection'

    # PropertySelection = F'{ontology}PropertySelection'
    # PropertySelection_ttl = F'{genericPrefix}:PropertySelection'

    PropertyPartition = F'{ontology}PropertyPartition'
    PropertyPartition_ttl = F'{genericPrefix}:PropertyPartition'

    algoSequence = F'{ontology}AlgorithmSequence'
    algoSequence_ttl = F'{genericPrefix}:AlgorithmSequence'

    ClassPartition = F'{ontology}ClassPartition'
    ClassPartition_ttl = F'{genericPrefix}:ClassPartition'

    PartitionFormulation = F'{ontology}PartitionFormulation'
    PartitionFormulation_ttl = F'{genericPrefix}:PartitionFormulation'

    MatchingAlgorithm = F'{ontology}MatchingAlgorithm'
    MatchingAlgorithm_ttl = F'{genericPrefix}:MatchingAlgorithm'

    ClusteringAlgorithm = F'{ontology}ClusteringAlgorithm'
    ClusteringAlgorithm_ttl = F'{genericPrefix}:ClusteringAlgorithm'

    LensOperator = F'{ontology}LensOperator'
    LensOperator_ttl = F'{genericPrefix}:LensOperator'

    # ###############################################################################
    #                            PREDEFINED RESOURCES                               #
    # ###############################################################################
    Linkset_prefix = F"@prefix {'linkset':>{PREF_SIZE}}: <{resource_ns}linkset#> ."
    Lens_prefix = F"@prefix {'lens':>{PREF_SIZE}}: <{resource_ns}lens#> ."
    LensOperator_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{resource_ns}lensOperator#> ."
    Cluster_prefix = F"@prefix {'cluster':>{PREF_SIZE}}: <{resource_ns}cluster#> ."
    Clusterset_prefix = F"@prefix {'clusterset':>{PREF_SIZE}}: <{resource_ns}clusterset#> ."
    Validation_prefix = F"@prefix {'validation':>{PREF_SIZE}}: <{resource_ns}validation#> ."
    Validationset_prefix = F"@prefix {'validationset':>{PREF_SIZE}}: <{resource_ns}validationset#> ."
    ValidationFlag_prefix = F"@prefix {'flag':>{PREF_SIZE}}: <{resource_ns}validationFlag#> ."

    ##############################################################################################################
    #                                              GENERIC METADATA                                              #
    ##############################################################################################################
    # linkset:Grid_2
    #
    #     a                                        void:Linkset ;
    #     cc:attributionName                       "LenticularLens" ;
    #     void:feature                             format:Turtle ;
    # 	  cc:license                               <http://purl.org/NET/rdflicense/W3C1.0> ;
    # 	  void+:has-matching-logic-formulation     """<http://data.goldenagents.org/resource/EditDistance-H55b8f81b407d0ec>
    # 	  """ ;
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
    # 	  void+:has-clusters                          619 ;
    # 	  ll_val:has-validations                   18 ;
    # 	  ll_val:has-accepted                      3 ;
    # 	  ll_val:has-rejected                      6 ;
    # 	  ll_val:has-remaining                     1683 .

    exportDate = F"{ontology}exportDate"
    exportDate_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    exportDate_ttl = F"{genericPrefix}:exportDate"

    clusters = F"{ontology}clusters"
    clusters_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    clusters_ttl = F"{genericPrefix}:clusters"

    clusterset = F"{ontology}hasClusterset"
    clusterset_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    clusterset_ttl = F"{genericPrefix}:hasClusterset"

    formulation = F"{ontology}hasFormulation"
    formulation_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    formulation_ttl = F'{genericPrefix}:hasFormulation'

    hasTarget = F"{ontology}hasTarget"
    hasTarget_ttl = F"{genericPrefix}:hasTarget"

    # The void:Dataset that contains the resources in the subject position of this void:Linkset's triples.
    subTarget = F"{ontology}subjectsTarget"
    subTarget_ttl = F"{genericPrefix}:subjectsTarget"

    # The void:Dataset that contains the resources in the object position of a void:Linkset's triples.
    objTarget = F"{ontology}objectsTarget"
    objTarget_ttl = F"{genericPrefix}:objectsTarget"

    sourceEntities = F"{ontology}sourceEntities"
    sourceEntities_ttl = F"{genericPrefix}:sourceEntities"

    targetEntities = F"{ontology}targetEntities"
    targetEntities_ttl = F"{genericPrefix}:targetEntities"

    srcTrgEntities = F"{ontology}srcTrgEntities"
    srcTrgEntities_ttl = F"{genericPrefix}:srcTrgEntities"

    hasOperator = F"{ontology}hasOperator"
    hasOperator_ttl = F"{genericPrefix}:hasOperator"
    hasOperand = F"{ontology}hasOperand"
    hasOperand_ttl = F"{genericPrefix}:hasOperand"

    # ###############################################################################
    #                                  CLUSTERS                                     #
    # ###############################################################################

    id_ttl = F"{genericPrefix}:id"
    intID_ttl = F"{genericPrefix}:intID"
    hashID_ttl = F"{genericPrefix}:hashID"
    # network_ID_ttl = F"{genericPrefix}:networkID"
    size_ttl = F"{genericPrefix}:nodes"
    links_ttl = F"{genericPrefix}:links"
    extended_ttl = F"{genericPrefix}:isExtended"
    reconciled_ttl = F"{genericPrefix}:isReconciled"
    largestNodeCount_ttl = F"{genericPrefix}:largestNodeCount"
    largestLinkCount_ttl = F"{genericPrefix}:largestLinkCount"

    # ###############################################################################
    #                                  VALIDATION                                   #
    # ###############################################################################

    contradictions_ttl = F"{genericPrefix}:contradictions"
    validations_ttl = F"{genericPrefix}:validations"
    accepted_ttl = F"{genericPrefix}:accepted"
    rejected_ttl = F"{genericPrefix}:rejected"
    uncertain_ttl = F"{genericPrefix}:uncertain"
    unchecked_ttl = F"{genericPrefix}:unchecked"
    remains_ttl = F"{genericPrefix}:remaining"
    motivation_ttl = F"{genericPrefix}:motivation"
    has_validation_ttl = F"{genericPrefix}:hasValidation"
    has_validation_status_ttl = F"{genericPrefix}:hasValidationStatus"
    has_validationset_ttl = F"{genericPrefix}:hasValidationSet"

    hasSourceEvidence_ttl = F"{genericPrefix}:hasSourceEvidence"
    hasTargetEvidence_ttl = F"{genericPrefix}:hasTargetEvidence"

    # ###############################################################################
    #                             LOGIC FORMULA PARTS                               #
    # ###############################################################################

    part = F"{ontology}hasItem"
    part_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    part_ttl = F'{genericPrefix}:hasItem'

    formulaDescription = F"{ontology}hasFormulaDescription"
    formulaDescription_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    formulaDescription_ttl = F'{genericPrefix}:hasFormulaDescription'

    formulaTree = F"{ontology}hasFormulaTree"
    formulaTree_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    formulaTree_ttl = F'{genericPrefix}:hasFormulaTree'

    # ##############################################################################
    #                              METHOD SIGNATURES                               #
    # ##############################################################################
    # resource:EditDistance-H55b8f81b407d0ec
    #
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
    method_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    method_ttl = F'{genericPrefix}:hasAlgorithm'

    methodSequence = F"{ontology}hasAlgorithmSequence"
    methodSequence_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    methodSequence_ttl = F'{genericPrefix}:hasAlgorithmSequence'

    simThreshold = F"{ontology}similarityThreshold"
    simThreshold_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    simThreshold_ttl = F'{genericPrefix}:similarityThreshold'

    deltaThreshold = F"{ontology}deltaThreshold"
    deltaThreshold_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    deltaThreshold_ttl = F'{genericPrefix}:deltaThreshold'

    combiThreshold = F"{ontology}combinationThreshold"
    combiThreshold_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    combiThreshold_ttl = F'{genericPrefix}:combinationThreshold'

    thresholdRange = F"{ontology}similarityThresholdRange"
    thresholdRange_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    thresholdRange_ttl = F'{genericPrefix}:similarityThresholdRange'

    combiThresholdRange = F"{ontology}combinationThresholdRange"
    combiThresholdRange_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    combiThresholdRange_ttl = F'{genericPrefix}:combinationThresholdRange'

    simOperator = F"{ontology}hasThresholdAcceptanceOperator"
    simOperator_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    simOperator_ttl = F'{genericPrefix}:hasThresholdAcceptanceOperator'

    strength = F"{ontology}matchingStrength"
    strength_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    strength_ttl = F'{genericPrefix}:matchingStrength'

    # A RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE AT THE SOURCE POSITION
    entitySelectionSubj = F"{ontology}hasSubjResourceSelection"
    entitySelectionSubjPrefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    entitySelectionSubj_ttl = F'{genericPrefix}:hasSubjResourceSelection'

    # A RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE AT THE TARGET POSITION
    entitySelectionObj = F"{ontology}hasObjResourceSelection"
    entitySelectionObj_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    entitySelectionObj_ttl = F'{genericPrefix}:hasObjResourceSelection'

    # THE INTERMEDIATE DATASET
    intermediateSubjEntitySelection = F"{ontology}hasInterSubjResourceSelection"
    intermediateSubjEntitySelectionPrefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    intermediateSubjEntitySelection_ttl = F'{genericPrefix}:hasInterSubjResourceSelection'

    intermediateObjEntitySelection = F"{ontology}hasInterObjResourceSelection"
    intermediateObjEntitySelectionPrefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    intermediateObjEntitySelection_ttl = F'{genericPrefix}:hasInterObjResourceSelection'

    # THE URI OF GHE SELECTED ALGORITHM
    method_hash = F"{ontology}matchingMethodHash"
    method_hash_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    method_hash_ttl = F'{genericPrefix}:matchingMethodHash'

    sub_predicate_selected = F"{ontology}hasSubjPredicateSelection"
    sub_predicate_selected_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    sub_predicate_selected_ttl = F'{genericPrefix}:hasSubjPredicateSelection'

    obj_predicate_selected = F"{ontology}hasObjPredicateSelection"
    obj_predicate_selected_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    obj_predicate_selected_ttl = F'{genericPrefix}:hasObjPredicateSelection'

    # ##############################################################################
    #                        DATASET AND ENTITY SELECTIONS                         #
    # ##############################################################################
    #  resource:EntitySelection-PH61bd543e4ce34c2
    # 	ll:has-selected-dataset                 <http://data.goldenagents.org/resource/dataset/Grid> ;
    # 	ll:has-selected-data_type               <http://www.grid.ac/ontology/Education> .

    # THE SELECTED RESOURCE IF SUBSET OF A DATASET
    subset_of = F"{ontology}subsetOf"
    subset_of_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    subset_of_ttl = F'{genericPrefix}:subsetOf'

    # HAS FORMULATION
    hasFormulation = F"{ontology}hasFormulation"
    hasFormulation_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    hasFormulation_ttl = F'{genericPrefix}:hasFormulation'

    # HAS ITEM
    hasItem = F"{ontology}hasItem"
    hasItem_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    hasItem_ttl = F'{genericPrefix}:hasItem'

    # THE SELECTED DATASET FOR THE ENTITY SELECTED RESOURCE
    dataset = F"{ontology}hasDataset"
    dataset_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    dataset_ttl = F'{genericPrefix}:hasDataset'

    # THE SELECTED DATA TYPE FOR THE ENTITY SELECTED RESOURCE
    dataType = F"{ontology}hasEntityType"
    dataType_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    dataType_ttl = F'{genericPrefix}:hasEntityType'

    filterFunction = F"{ontology}hasFilterFunction"
    filterFunction_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    filterFunction_ttl = F'{genericPrefix}:hasFilterFunction'

    filterValue = F"{ontology}hasValueFunction"
    filterValue_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    filterValue_ttl = F'{genericPrefix}:hasValueFunction'

    filterFormat = F"{ontology}hasFormatFunction"
    filterFormat_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    filterFormat_ttl = F'{genericPrefix}:hasFormatFunction'

    # ##############################################################################
    #                             PREDICATE SELECTIONS                             #
    # ##############################################################################
    # resource:PredicateSelection-PHab504e102405ab0
    # 	ll:has-entity-selected                  resource:EntitySelection-PH61bd543e4ce34c2> ;
    # 	ll:has-subj-predicate                   <http://www.w3.org/2000/01/rdf-schema#label> .

    # THE URI OF THE RESOURCE DESCRIBING THE SELECTED DATASET AND DATATYPE FOR A SELECTED PREDICATE
    entity_selected = F"{ontology}hasEntitySelection"
    entity_selected_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    entity_selected_ttl = F'{genericPrefix}:hasEntitySelection'

    predicate = F"{ontology}hasPredicate"
    predicate_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    predicate_ttl = F'{genericPrefix}:hasPredicate'

    # ##############################################################################
    #                                 LENS OPERATORS                               #
    # ##############################################################################

    operator = F"{ontology}lensOperator#"

    union = F"{operator}union"
    union_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{operator}> ."
    union_ttl = F"operator:union"

    intersection = F"{operator}intersection"
    intersection_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{operator}> ."
    intersection_ttl = F"operator:intersection"

    transitive = F"{operator}transitive"
    transitive_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{operator}> ."
    transitive_ttl = F"operator:transitive"

    difference = F"{operator}difference"
    difference_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{operator}> ."
    difference_ttl = F"operator:difference"

    composition = F"{operator}composition"
    composition_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{operator}> ."
    composition_ttl = F"operator:composition"

    deltaSign = F"{ontology}deltaSign"
    deltaSign_ttl = F'{genericPrefix}:deltaSign'

    # ##############################################################################
    #                             ...................                             #
    # ##############################################################################

    mechanism = F"{ontology}hasMatchingMechanism"
    mechanism_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    mechanism_ttl = F"{genericPrefix}:hasMatchingMechanism"

    justification = F"{ontology}hasMatchingJustification"
    justification_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    justification_ttl = F"{genericPrefix}:hasMatchingJustification"

    view = F"{ontology}hasView/"
    view_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    view_ttl = F"{genericPrefix}:hasView"

    cluster_ID = F"{ontology}hasClusterID"
    cluster_ID_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    cluster_ID_ttl = F"{genericPrefix}:hasClusterID"

    cluster_Int_ID = F"{ontology}clusterIntID"
    cluster_Int_ID_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    cluster_Int_ID_ttl = F"{genericPrefix}:clusterIntID"

    network_ID = F"{ontology}networkID"
    network_ID_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    network_ID_ttl = F"{genericPrefix}:networkID"

    cluster_size = F"{ontology}hasClusterSize"
    cluster_size_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    cluster_size_ttl = F"{genericPrefix}:hasClusterSize"

    clusterConstraint = F"{ontology}hasClusterConstrain"
    clusterConstraint_prefix = F"@prefix {F'{genericPrefix}':>{PREF_SIZE}}: <{ontology}> ."
    clusterConstraint_ttl = F"{genericPrefix}:hasClusterConstrain"

    # ##############################################################################
    #                                    LINKSET                                  #
    # ##############################################################################


