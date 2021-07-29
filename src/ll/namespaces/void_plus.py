class VoidPlus:
    # ###############################################################################
    #                                     PREFIXES                                  #
    # ###############################################################################

    ontology = "https://lenticularlens.org/voidPlus/"
    ontology_prefix = "voidPlus"

    resource = F"{ontology}resource/"
    resource_prefix = 'resource'

    linkset = F"{resource}linkset#"
    linkset_prefix = 'linkset'

    lens = F"{resource}lens#"
    lens_prefix = 'lens'

    cluster = F"{resource}cluster#"
    cluster_prefix = 'cluster'

    clusterset = F"{resource}clusterset#"
    clusterset_prefix = 'clusterset'

    validation = F"{resource}validation#"
    validation_prefix = 'validation'

    validationset = F"{resource}validationset#"
    validationset_prefix = 'validationset'

    # ###############################################################################
    #                                   CLASSES                                     #
    # ###############################################################################

    Linkset = F'{ontology_prefix}:Linkset'
    Lens = F'{ontology_prefix}:Lens'
    Cluster = F'{ontology_prefix}:Cluster'
    Clusterset = F'{ontology_prefix}:Clusterset'
    Validation = F'{ontology_prefix}:Validation'
    Validationset = F'{ontology_prefix}:Validationset'
    ValidationFlag = F'{ontology_prefix}:ValidationFlag'
    LinksetFormulation = F'{ontology_prefix}:LinksetFormulation'
    LensFormulation = F'{ontology_prefix}:LensFormulation'
    MatchingMethod = F'{ontology_prefix}:MatchingMethod'
    ResourceSelection = F'{ontology_prefix}:ResourceSelection'
    PropertyPartition = F'{ontology_prefix}:PropertyPartition'
    ClassPartition = F'{ontology_prefix}:ClassPartition'
    PartitionFormulation = F'{ontology_prefix}:PartitionFormulation'
    MatchingAlgorithm = F'{ontology_prefix}:MatchingAlgorithm'
    ClusteringAlgorithm = F'{ontology_prefix}:ClusteringAlgorithm'
    LensOperator = F'{ontology_prefix}:LensOperator'

    ##############################################################################################################
    #                                              GENERIC METADATA                                              #
    ##############################################################################################################

    clusters = F"{ontology_prefix}:clusters"
    hasClusterset = F"{ontology_prefix}:hasClusterset"
    hasFormulation = F'{ontology_prefix}:hasFormulation'
    hasTarget = F"{ontology_prefix}:hasTarget"
    subjectsTarget = F"{ontology_prefix}:subjectsTarget"
    objectsTarget = F"{ontology_prefix}:objectsTarget"
    sourceEntities = F"{ontology_prefix}:sourceEntities"
    targetEntities = F"{ontology_prefix}:targetEntities"
    srcTrgEntities = F"{ontology_prefix}:srcTrgEntities"
    hasOperator = F"{ontology_prefix}:hasOperator"
    hasOperand = F"{ontology_prefix}:hasOperand"

    # ###############################################################################
    #                                  CLUSTERS                                     #
    # ###############################################################################

    nodes = F"{ontology_prefix}:nodes"
    links = F"{ontology_prefix}:links"
    isExtended = F"{ontology_prefix}:isExtended"
    isReconciled = F"{ontology_prefix}:isReconciled"
    largestNodeCount = F"{ontology_prefix}:largestNodeCount"
    largestLinkCount = F"{ontology_prefix}:largestLinkCount"
    hasClusterID = F"{ontology_prefix}:hasClusterID"

    # ###############################################################################
    #                                  VALIDATION                                   #
    # ###############################################################################

    validations = F"{ontology_prefix}:validations"
    accepted = F"{ontology_prefix}:accepted"
    rejected = F"{ontology_prefix}:rejected"
    uncertain = F"{ontology_prefix}:uncertain"
    unchecked = F"{ontology_prefix}:unchecked"
    contradictions = F"{ontology_prefix}:contradictions"
    motivation = F"{ontology_prefix}:motivation"
    hasValidation = F"{ontology_prefix}:hasValidation"
    hasValidationStatus = F"{ontology_prefix}:hasValidationStatus"
    hasValidationSet = F"{ontology_prefix}:hasValidationSet"
    hasSourceEvidence = F"{ontology_prefix}:hasSourceEvidence"
    hasTargetEvidence = F"{ontology_prefix}:hasTargetEvidence"

    # ###############################################################################
    #                             LOGIC FORMULA PARTS                               #
    # ###############################################################################

    hasItem = F'{ontology_prefix}:hasItem'
    hasFormulaDescription = F'{ontology_prefix}:hasFormulaDescription'
    hasFormulaTree = F'{ontology_prefix}:hasFormulaTree'

    # ##############################################################################
    #                              METHOD SIGNATURES                               #
    # ##############################################################################

    hasAlgorithm = F'{ontology_prefix}:hasAlgorithm'
    isAppliedOnEncodedValues = F'{ontology_prefix}:isAppliedOnEncodedValues'
    hasAlgorithmSequence = F'{ontology_prefix}:hasAlgorithmSequence'
    similarityThreshold = F'{ontology_prefix}:similarityThreshold'
    combinationThreshold = F'{ontology_prefix}:combinationThreshold'
    similarityThresholdRange = F'{ontology_prefix}:similarityThresholdRange'
    matchingStrength = F'{ontology_prefix}:matchingStrength'
    hasSubjResourceSelection = F'{ontology_prefix}:hasSubjResourceSelection'
    hasObjResourceSelection = F'{ontology_prefix}:hasObjResourceSelection'
    hasInterSubjResourceSelection = F'{ontology_prefix}:hasInterSubjResourceSelection'
    hasInterObjResourceSelection = F'{ontology_prefix}:hasInterObjResourceSelection'
    stopWords = F'{ontology_prefix}:stopWords'
    stopWordsList = F'{ontology_prefix}:stopWordsList'
    hasTransformationFunction = F'{ontology_prefix}:hasTransformationFunction'
    hasTransformationParameters = F'{ontology_prefix}:hasTransformationParameters'
    hasListConfiguration = F'{ontology_prefix}:hasListConfiguration'
    listThreshold = F'{ontology_prefix}:listThreshold'
    appreciation = F'{ontology_prefix}:appreciation'

    # ##############################################################################
    #                        DATASET AND ENTITY SELECTIONS                         #
    # ##############################################################################

    subsetOf = F'{ontology_prefix}:subsetOf'
    hasFilterFunction = F'{ontology_prefix}:hasFilterFunction'
    hasValueFunction = F'{ontology_prefix}:hasValueFunction'
    hasFormatFunction = F'{ontology_prefix}:hasFormatFunction'
