TAB = '    '


def get_pred_size(tabs=1):
    return 55 - (4 * (tabs - 1))


def pred_val(predicate, value, end=False, line=True, tabs=1):
    new_line = '\n' if line else ''
    tab = (TAB * tabs) if line else ''
    pred_size = get_pred_size(tabs)
    return f"{tab}{predicate:{pred_size}}{value} {'.' if end else ';'}{new_line}"


def multiple_val(values, tabs=1):
    pred_size = get_pred_size(tabs)
    return f" ,\n{TAB * tabs}{'':{pred_size}}".join(values)


def blank_node(pred_values, type_predicate=None, tabs=1):
    seq = pred_val('a', type_predicate, tabs=(tabs + 2)) if type_predicate else ''
    for (pred, value) in pred_values:
        seq += pred_val(pred, value, tabs=(tabs + 2))

    return f"\n{TAB * (tabs + 1)}[\n{seq}{TAB * 2}]"


def rdfs_sequence(values, type_predicate='rdfs:Sequence', tabs=1):
    return blank_node([(f'rdf:_{idx + 1}', value) for idx, value in enumerate(values)], type_predicate, tabs=tabs)
