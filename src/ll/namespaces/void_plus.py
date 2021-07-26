ll = 'https://lenticularlens.org/'
pref_size = 20


class VoidPlus:
    generic_prefix = "voidPlus"

    # ###############################################################################
    #                                     PREFIXES                                  #
    # ###############################################################################

    ontology = F'{ll}voidPlus/'
    ontology_prefix = generic_prefix
    ontology_prefix_ttl = F"@prefix {ontology_prefix:>{pref_size}}: <{ontology}> ."

    algorithm = F"{ontology}matchingMethod/"
    algorithm_prefix = 'll_algo'
    algorithm_prefix_ttl = F"@prefix {algorithm_prefix:>{pref_size}}: <{algorithm}> ."

    validation = F"{ontology}validation/"
    validation_prefix = 'll_val'
    validation_prefix_ttl = F"@prefix {validation_prefix:>{pref_size}}: <{validation}> ."

    resource = F"{ontology}resource/"
    resource_prefix = 'resource'
    resource_prefix_ttl = F"@prefix {resource_prefix:>{pref_size}}: <{resource}> ."

    linkset = F"{resource}linkset#"
    linkset_prefix = 'linkset'
    linkset_prefix_ttl = F"@prefix {linkset_prefix:>{pref_size}}: <{linkset}> ."

    lens = F"{resource}lens#"
    lens_prefix = 'lens'
    lens_prefix_ttl = F"@prefix {lens_prefix:>{pref_size}}: <{lens}> ."

    # operator = F"{resource}lensOperator#"
    # operator_prefix = F"@prefix {'operator':>{pref_size}}: <{resource_ns}lensOperator#> ."
    #
    # validationset = F"{resource}validationset#"
    # validationset_prefix = F"@prefix {'validationset':>{pref_size}}: <{resource_ns}validationset#> ."
    #
    # validation = F"{resource}validation#"
    # validation_prefix = F"@prefix {'validationset':>{pref_size}}: <{resource_ns}validation#> ."
    #
    # clusterset = F"{resource}clusterset#"
    # clusterset_prefix = F"@prefix {'clusterset':>{pref_size}}: <{resource_ns}clusterset#> ."
    #
    # cluster = F"{resource}clusterset#"
    # cluster_prefix = F"@prefix {'clusterset':>{pref_size}}: <{resource_ns}cluster#> ."
    #
    # singleton = F"{resource}singleton#"
    # singleton_prefix = F"@prefix {'singleton':>{pref_size}}: <{resource_ns}singleton#> ."
    #
    # dataset = F"{resource}dataset#"
    # dataset_prefix = F"@prefix {'dataset':>{pref_size}}: <{resource}dataset#> ."
    #
    # project = F"{resource}singleton#"
    # project_prefix = F"@prefix {'singleton':>{pref_size}}: <{resource}project#> ."
    #
    # researchQ = F"{resource}research-question#"
    # researchQ_prefix = F"@prefix {'researchQ':>{pref_size}}: <{resource}research-question#> ."

    # ###############################################################################
    #                                   CLASSES                                     #
    # ###############################################################################

    Linkset = F'{ontology}Linkset'
    Linkset_ttl = F'{generic_prefix}:Linkset'

    Lens = F'{ontology}Lens'
    Lens_ttl = F'{generic_prefix}:Lens'

    Cluster = F'{ontology}Cluster'
    Cluster_ttl = F'{generic_prefix}:Cluster'

    Clusterset = F'{ontology}Clusterset'
    Clusterset_ttl = F'{generic_prefix}:Clusterset'

    Validation = F'{ontology}Validation'
    Validation_ttl = F'{generic_prefix}:Validation'

    Validationset = F'{ontology}Validationset'
    Validationset_ttl = F'{generic_prefix}:Validationset'

    ValidationFlag = F'{ontology}ValidationFlag'
    ValidationFlag_ttl = F'{generic_prefix}:ValidationFlag'

    LinksetLogicFormulation = F'{ontology}LinksetFormulation'
    LinksetLogicFormulation_ttl = F'{generic_prefix}:LinksetFormulation'

    LensFormulation = F'{ontology}LensFormulation'
    LensFormulation_ttl = F'{generic_prefix}:LensFormulation'

    MatchingMethod = F'{ontology}MatchingMethod'
    MatchingMethod_ttl = F'{generic_prefix}:MatchingMethod'

    EntitySelection = F'{ontology}ResourceSelection'
    EntitySelection_ttl = F'{generic_prefix}:ResourceSelection'

    PropertyPartition = F'{ontology}PropertyPartition'
    PropertyPartition_ttl = F'{generic_prefix}:PropertyPartition'

    algoSequence = F'{ontology}AlgorithmSequence'
    algoSequence_ttl = F'{generic_prefix}:AlgorithmSequence'

    ClassPartition = F'{ontology}ClassPartition'
    ClassPartition_ttl = F'{generic_prefix}:ClassPartition'

    PartitionFormulation = F'{ontology}PartitionFormulation'
    PartitionFormulation_ttl = F'{generic_prefix}:PartitionFormulation'

    MatchingAlgorithm = F'{ontology}MatchingAlgorithm'
    MatchingAlgorithm_ttl = F'{generic_prefix}:MatchingAlgorithm'

    ClusteringAlgorithm = F'{ontology}ClusteringAlgorithm'
    ClusteringAlgorithm_ttl = F'{generic_prefix}:ClusteringAlgorithm'

    LensOperator = F'{ontology}LensOperator'
    LensOperator_ttl = F'{generic_prefix}:LensOperator'

    ##############################################################################################################
    #                                              GENERIC METADATA                                              #
    ##############################################################################################################

    clusters = F"{ontology}clusters"
    clusters_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    clusters_ttl = F"{generic_prefix}:clusters"

    clusterset = F"{ontology}hasClusterset"
    clusterset_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    clusterset_ttl = F"{generic_prefix}:hasClusterset"

    formulation = F"{ontology}hasFormulation"
    formulation_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    formulation_ttl = F'{generic_prefix}:hasFormulation'

    hasTarget = F"{ontology}hasTarget"
    hasTarget_ttl = F"{generic_prefix}:hasTarget"

    subTarget = F"{ontology}subjectsTarget"
    subTarget_ttl = F"{generic_prefix}:subjectsTarget"

    objTarget = F"{ontology}objectsTarget"
    objTarget_ttl = F"{generic_prefix}:objectsTarget"

    sourceEntities = F"{ontology}sourceEntities"
    sourceEntities_ttl = F"{generic_prefix}:sourceEntities"

    targetEntities = F"{ontology}targetEntities"
    targetEntities_ttl = F"{generic_prefix}:targetEntities"

    srcTrgEntities = F"{ontology}srcTrgEntities"
    srcTrgEntities_ttl = F"{generic_prefix}:srcTrgEntities"

    hasOperator = F"{ontology}hasOperator"
    hasOperator_ttl = F"{generic_prefix}:hasOperator"

    hasOperand = F"{ontology}hasOperand"
    hasOperand_ttl = F"{generic_prefix}:hasOperand"

    # ###############################################################################
    #                                  CLUSTERS                                     #
    # ###############################################################################

    id_ttl = F"{generic_prefix}:id"
    size_ttl = F"{generic_prefix}:nodes"
    links_ttl = F"{generic_prefix}:links"
    extended_ttl = F"{generic_prefix}:isExtended"
    reconciled_ttl = F"{generic_prefix}:isReconciled"
    largestNodeCount_ttl = F"{generic_prefix}:largestNodeCount"
    largestLinkCount_ttl = F"{generic_prefix}:largestLinkCount"

    # ###############################################################################
    #                                  VALIDATION                                   #
    # ###############################################################################

    contradictions_ttl = F"{generic_prefix}:contradictions"
    validations_ttl = F"{generic_prefix}:validations"
    accepted_ttl = F"{generic_prefix}:accepted"
    rejected_ttl = F"{generic_prefix}:rejected"
    uncertain_ttl = F"{generic_prefix}:uncertain"
    unchecked_ttl = F"{generic_prefix}:unchecked"
    remains_ttl = F"{generic_prefix}:remaining"
    motivation_ttl = F"{generic_prefix}:motivation"
    has_validation_ttl = F"{generic_prefix}:hasValidation"
    has_validation_status_ttl = F"{generic_prefix}:hasValidationStatus"
    has_validationset_ttl = F"{generic_prefix}:hasValidationSet"

    hasSourceEvidence_ttl = F"{generic_prefix}:hasSourceEvidence"
    hasTargetEvidence_ttl = F"{generic_prefix}:hasTargetEvidence"

    # ###############################################################################
    #                             LOGIC FORMULA PARTS                               #
    # ###############################################################################

    part = F"{ontology}hasItem"
    part_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    part_ttl = F'{generic_prefix}:hasItem'

    formulaDescription = F"{ontology}hasFormulaDescription"
    formulaDescription_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    formulaDescription_ttl = F'{generic_prefix}:hasFormulaDescription'

    formulaTree = F"{ontology}hasFormulaTree"
    formulaTree_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    formulaTree_ttl = F'{generic_prefix}:hasFormulaTree'

    # ##############################################################################
    #                              METHOD SIGNATURES                               #
    # ##############################################################################

    method = F"{ontology}hasAlgorithm"
    method_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    method_ttl = F'{generic_prefix}:hasAlgorithm'

    normalized = F"{ontology}isAppliedOnEncodedValues"
    normalized_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    normalized_ttl = F'{generic_prefix}:isAppliedOnEncodedValues'

    methodSequence = F"{ontology}hasAlgorithmSequence"
    methodSequence_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    methodSequence_ttl = F'{generic_prefix}:hasAlgorithmSequence'

    simThreshold = F"{ontology}similarityThreshold"
    simThreshold_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    simThreshold_ttl = F'{generic_prefix}:similarityThreshold'

    combiThreshold = F"{ontology}combinationThreshold"
    combiThreshold_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    combiThreshold_ttl = F'{generic_prefix}:combinationThreshold'

    thresholdRange = F"{ontology}similarityThresholdRange"
    thresholdRange_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    thresholdRange_ttl = F'{generic_prefix}:similarityThresholdRange'

    combiThresholdRange = F"{ontology}combinationThresholdRange"
    combiThresholdRange_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    combiThresholdRange_ttl = F'{generic_prefix}:combinationThresholdRange'

    simOperator = F"{ontology}hasThresholdAcceptanceOperator"
    simOperator_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    simOperator_ttl = F'{generic_prefix}:hasThresholdAcceptanceOperator'

    strength = F"{ontology}matchingStrength"
    strength_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    strength_ttl = F'{generic_prefix}:matchingStrength'

    entitySelectionSubj = F"{ontology}hasSubjResourceSelection"
    entitySelectionSubjPrefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    entitySelectionSubj_ttl = F'{generic_prefix}:hasSubjResourceSelection'

    entitySelectionObj = F"{ontology}hasObjResourceSelection"
    entitySelectionObj_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    entitySelectionObj_ttl = F'{generic_prefix}:hasObjResourceSelection'

    intermediateSubjEntitySelection = F"{ontology}hasInterSubjResourceSelection"
    intermediateSubjEntitySelectionPrefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    intermediateSubjEntitySelection_ttl = F'{generic_prefix}:hasInterSubjResourceSelection'

    intermediateObjEntitySelection = F"{ontology}hasInterObjResourceSelection"
    intermediateObjEntitySelectionPrefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    intermediateObjEntitySelection_ttl = F'{generic_prefix}:hasInterObjResourceSelection'

    method_hash = F"{ontology}matchingMethodHash"
    method_hash_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    method_hash_ttl = F'{generic_prefix}:matchingMethodHash'

    sub_predicate_selected = F"{ontology}hasSubjPredicateSelection"
    sub_predicate_selected_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    sub_predicate_selected_ttl = F'{generic_prefix}:hasSubjPredicateSelection'

    obj_predicate_selected = F"{ontology}hasObjPredicateSelection"
    obj_predicate_selected_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    obj_predicate_selected_ttl = F'{generic_prefix}:hasObjPredicateSelection'

    # ##############################################################################
    #                        DATASET AND ENTITY SELECTIONS                         #
    # ##############################################################################

    subset_of = F"{ontology}subsetOf"
    subset_of_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    subset_of_ttl = F'{generic_prefix}:subsetOf'

    hasFormulation = F"{ontology}hasFormulation"
    hasFormulation_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    hasFormulation_ttl = F'{generic_prefix}:hasFormulation'

    hasItem = F"{ontology}hasItem"
    hasItem_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    hasItem_ttl = F'{generic_prefix}:hasItem'

    dataset = F"{ontology}hasDataset"
    dataset_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    dataset_ttl = F'{generic_prefix}:hasDataset'

    dataType = F"{ontology}hasEntityType"
    dataType_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    dataType_ttl = F'{generic_prefix}:hasEntityType'

    filterFunction = F"{ontology}hasFilterFunction"
    filterFunction_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    filterFunction_ttl = F'{generic_prefix}:hasFilterFunction'

    filterValue = F"{ontology}hasValueFunction"
    filterValue_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    filterValue_ttl = F'{generic_prefix}:hasValueFunction'

    filterFormat = F"{ontology}hasFormatFunction"
    filterFormat_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    filterFormat_ttl = F'{generic_prefix}:hasFormatFunction'

    # ##############################################################################
    #                             PREDICATE SELECTIONS                             #
    # ##############################################################################

    entity_selected = F"{ontology}hasEntitySelection"
    entity_selected_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    entity_selected_ttl = F'{generic_prefix}:hasEntitySelection'

    predicate = F"{ontology}hasPredicate"
    predicate_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    predicate_ttl = F'{generic_prefix}:hasPredicate'

    # ##############################################################################
    #                             ...................                             #
    # ##############################################################################

    mechanism = F"{ontology}hasMatchingMechanism"
    mechanism_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    mechanism_ttl = F"{generic_prefix}:hasMatchingMechanism"

    justification = F"{ontology}hasMatchingJustification"
    justification_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    justification_ttl = F"{generic_prefix}:hasMatchingJustification"

    view = F"{ontology}hasView/"
    view_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    view_ttl = F"{generic_prefix}:hasView"

    cluster_ID = F"{ontology}hasClusterID"
    cluster_ID_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    cluster_ID_ttl = F"{generic_prefix}:hasClusterID"

    cluster_size = F"{ontology}hasClusterSize"
    cluster_size_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    cluster_size_ttl = F"{generic_prefix}:hasClusterSize"

    clusterConstraint = F"{ontology}hasClusterConstrain"
    clusterConstraint_prefix = F"@prefix {F'{generic_prefix}':>{pref_size}}: <{ontology}> ."
    clusterConstraint_ttl = F"{generic_prefix}:hasClusterConstrain"