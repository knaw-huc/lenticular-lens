export default {
    matchingMethods: {
        '=': {
            'label': 'Exact Match',
            'items': []
        },
        'LL_SOUNDEX': {
            'label': 'Similar Soundex',
            'items': [
                {
                    'key': 'threshold',
                    'label': 'Similarity threshold',
                    'type': 0.7,
                    'minValue': 0,
                    'maxValue': 1,
                }
            ]
        },
        'BLOOTHOOFT_REDUCT': {
            'label': 'Same Bloothooft Reduction',
            'items': [
                {
                    'key': 'name_type',
                    'label': 'Type of Name',
                    'type': '',
                    'choices': {
                        'First name': 'first_name',
                        'Family name': 'family name',
                    },
                },
                {
                    'key': 'threshold',
                    'label': 'Similarity threshold',
                    'type': 0.7,
                    'minValue': 0,
                    'maxValue': 1,
                }
            ]
        },
        'BLOOTHOOFT_REDUCT_APPROX': {
            'label': 'Similar Bloothooft Reduction',
            'items': [
                {
                    'key': 'name_type',
                    'label': 'Type of Name',
                    'type': '',
                    'choices': {
                        'First name': 'first_name',
                        'Family name': 'family name',
                    },
                },
                {
                    'key': 'threshold',
                    'label': 'Similarity threshold',
                    'type': 0.7,
                    'minValue': 0,
                    'maxValue': 1,
                }
            ]
        },
        'TRIGRAM_DISTANCE': {
            'label': 'Trigram distance',
            'items': [
                {
                    'key': 'threshold',
                    'label': 'Similarity threshold',
                    'type': 0.3,
                    'minValue': 0,
                    'maxValue': 1,
                }
            ]
        },
        'LEVENSHTEIN': {
            'label': 'Levenshtein distance',
            'items': [
                {
                    'key': 'max_distance',
                    'label': 'Maximum distance',
                    'type': 1,
                    'minValue': 0,
                }
            ]
        },
        'TIME_DELTA': {
            'label': 'Time Delta',
            'items': [
                {
                    'key': 'days',
                    'label': '',
                    'type': 0,
                    'minValue': 0,
                },
                {
                    'key': 'multiplier',
                    'label': '',
                    'type': '',
                    'choices': {
                        'Years': 365,
                        'Months': 30,
                        'Days': 1,
                    }
                }
            ]
        },
        'SAME_YEAR_MONTH': {
            'label': 'Same Year/Month',
            'items': [
                {
                    'key': 'date_part',
                    'label': '',
                    'type': '',
                    'choices': {
                        'Year': 'year',
                        'Month': 'month',
                        'Year and Month': 'year_month',
                    }
                }
            ]
        },
        'DISTANCE_IS_BETWEEN': {
            'label': 'Distance is between',
            'items': [
                {
                    'key': 'distance_start',
                    'label': 'Start',
                    'type': 0,
                },
                {
                    'key': 'distance_end',
                    'label': 'End',
                    'type': 0,
                }
            ]
        },
        'IS_IN_SET': {
            'label': 'Is a Match in Set',
            'items': [
                {
                    'key': 'alignment',
                    'label': '',
                    'type': {
                        'type': 'matching_label',
                    }
                }
            ]
        }
    },
    transformers: ['ecartico_full_name', 'to_date_immutable']
};