export default {
    matchingMethods: {
        '=': {
            label: 'Exact Match',
            items: []
        },
        'LEVENSHTEIN': {
            label: 'Levenshtein distance',
            items: [
                {
                    key: 'max_distance',
                    label: 'Maximum distance',
                    type: 1,
                    minValue: 0,
                }
            ]
        },
        'LEVENSHTEIN_APPROX': {
            label: 'Approximated Levenshtein',
            items: [
                {
                    key: 'threshold',
                    label: 'Similarity threshold',
                    type: 0.7,
                    minValue: 0,
                    maxValue: 1,
                }
            ]
        },
        'LL_SOUNDEX': {
            label: 'Approximated Soundex',
            items: [
                {
                    key: 'threshold',
                    label: 'Similarity threshold',
                    type: 0.7,
                    minValue: 0,
                    maxValue: 1,
                }
            ]
        },
        'BLOOTHOOFT_REDUCT': {
            label: 'Approximated Bloothooft Reduction',
            items: [
                {
                    key: 'name_type',
                    label: '',
                    type: '',
                    choices: {
                        'First name': 'first_name',
                        'Family name': 'family_name',
                    },
                },
                {
                    key: 'threshold',
                    label: 'Similarity threshold',
                    type: 0.7,
                    minValue: 0,
                    maxValue: 1,
                }
            ]
        },
        'BLOOTHOOFT_REDUCT_APPROX': {
            label: 'Similar Bloothooft Reduction',
            items: [
                {
                    key: 'name_type',
                    label: '',
                    type: '',
                    choices: {
                        'First name': 'first_name',
                        'Family name': 'family_name',
                    },
                },
                {
                    key: 'threshold',
                    label: 'Similarity threshold',
                    type: 0.7,
                    minValue: 0,
                    maxValue: 1,
                }
            ]
        },
        'TRIGRAM_DISTANCE': {
            label: 'Trigram distance',
            items: [
                {
                    key: 'threshold',
                    label: 'Similarity threshold',
                    type: 0.3,
                    minValue: 0,
                    maxValue: 1,
                }
            ]
        },
        'TIME_DELTA': {
            label: 'Time Delta',
            transformers: ['PARSE_DATE'],
            items: [
                {
                    key: 'days',
                    label: '',
                    type: 0,
                    minValue: 0,
                },
                {
                    key: 'multiplier',
                    label: '',
                    type: '',
                    choices: {
                        'Years': 365,
                        'Months': 30,
                        'Days': 1,
                    }
                }
            ]
        },
        'SAME_YEAR_MONTH': {
            label: 'Same Year/Month',
            items: [
                {
                    key: 'date_part',
                    label: '',
                    type: '',
                    choices: {
                        'Year': 'year',
                        'Month': 'month',
                        'Year and Month': 'year_month',
                    }
                }
            ]
        },
        'DISTANCE_IS_BETWEEN': {
            label: 'Distance is between',
            transformers: ['PARSE_NUMERIC'],
            items: [
                {
                    key: 'distance_start',
                    label: 'Start',
                    type: 0,
                },
                {
                    key: 'distance_end',
                    label: 'End',
                    type: 0,
                }
            ]
        }
    },
    transformers: {
        'ECARTICO_FULL_NAME': {
            label: 'Ecartico full name',
            items: []
        },
        'PARSE_DATE': {
            label: 'Parse date',
            items: [{
                key: 'format',
                label: 'Date format',
                type: 'YYYY-MM-DD'
            }]
        },
        'PARSE_NUMERIC': {
            label: 'Parse numeric',
            items: []
        },
        'PREFIX': {
            label: 'Prefix',
            items: [{
                key: 'prefix',
                label: 'Prefix with',
                type: ''
            }]
        },
        'SUFFIX': {
            label: 'Suffix',
            items: [{
                key: 'suffix',
                label: 'Suffix with',
                type: ''
            }]
        },
        'REPLACE': {
            label: 'Replace',
            items: [{
                key: 'from',
                label: 'From',
                type: ''
            }, {
                key: 'to',
                label: 'To',
                type: ''
            }]
        }
    },
    lensOptions: {
        UNION: 'Union (A ∪ B)',
        INTERSECTION: 'Intersection (A ∩ B)',
        DIFFERENCE: 'Difference (A - B)',
        SYM_DIFFERENCE: 'Symmetric difference (A ∆ B)',
        IN_SET_AND: 'Source and target resources match',
        IN_SET_OR: 'Source or target resources match',
        IN_SET_SOURCE: 'Source resources match',
        IN_SET_TARGET: 'Target resources match'
    },
    lensOptionGroups: {
        'Operations on links': ['UNION', 'INTERSECTION', 'DIFFERENCE', 'SYM_DIFFERENCE'],
        'Operations on link resources': ['IN_SET_AND', 'IN_SET_OR', 'IN_SET_SOURCE', 'IN_SET_TARGET'],
    },
    lensOptionDescriptions: {
        UNION: 'All links of both linksets/lenses',
        INTERSECTION: 'Only links that appear in both linksets/lenses',
        DIFFERENCE: 'Only links from the first linkset/lens, not from the second linkset/lens',
        SYM_DIFFERENCE: 'Only links which appear in either one linkset/lens, but not both',
        IN_SET_AND: 'Both the source and target resource from the first linkset/lens must appear in the the set of resources from the second linkset/lens',
        IN_SET_OR: 'Either the source or the target resource from the first linkset/lens must appear in the the set of resources from the second linkset/lens',
        IN_SET_SOURCE: 'The source resource from the first linkset/lens must appear in the the set of resources from the second linkset/lens',
        IN_SET_TARGET: 'The target resource from the first linkset/lens must appear in the the set of resources from the second linkset/lens'
    },
};