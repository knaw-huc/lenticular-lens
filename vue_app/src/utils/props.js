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
        }
    }
};