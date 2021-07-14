translation_table = str.maketrans({'\\': r'\\\\',
                                   '\b': r'\\b', '\f': r'\\f', '\n': r'\\n',
                                   '\r': r'\\r', '\t': r'\\t', '\v': r'\\v'})
array_translation_table = str.maketrans({'"': r'\\"'})


def prepare_for_copy(values):
    prepared_values = []
    for value in values:
        if value is None:
            prepared_values.append(r'\N')
        elif isinstance(value, str):
            prepared_values.append(value.translate(translation_table))
        else:
            array_values = [f'"{v.translate(translation_table).translate(array_translation_table)}"' for v in value]
            prepared_values.append('{' + ','.join(array_values) + '}')

    return prepared_values
