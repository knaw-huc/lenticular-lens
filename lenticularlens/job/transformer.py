from schema import Schema, SchemaError, And, Or, Use, Optional

from lenticularlens.util.db_functions import get_filter_functions, get_matching_methods, get_transformers


class LogicBox:
    def __init__(self, schema, name, types, elements_schema=None):
        self.schema = schema
        self.name = name
        self.types = types
        self.elements_schema = elements_schema

    def validate(self, data):
        if type(data) is not dict:
            raise SchemaError('not an dict')

        if 'type' in data and data['type'].lower() in self.types and \
                self.name in data and type(data[self.name]) is list:
            elements = [self.validate(c) for c in data[self.name]]
            if len(elements) == 0:
                return None

            logicbox = {}
            if self.elements_schema:
                logicbox = self.elements_schema.validate(data)

            logicbox['type'] = data['type']
            logicbox[self.name] = elements

            return logicbox

        return self.schema.validate(data)


class EntityTypeSelection:
    def __init__(self, valid_ets_ids):
        self.valid_ets_ids = valid_ets_ids

    def validate(self, ets_id):
        try:
            ets_id = int(ets_id)
            if ets_id not in self.valid_ets_ids:
                raise SchemaError('entity-type selection %s not valid' % ets_id)

            return ets_id
        except Exception:
            raise SchemaError('entity-type selection %s not valid' % ets_id)


class MatchingMethodConfig:
    def __init__(self, valid_ets_ids):
        self.ets = EntityTypeSelection(valid_ets_ids)

    def validate(self, values):
        new_values = values.copy()
        if 'entity_type_selection' in new_values:
            new_values['entity_type_selection'] = self.ets.validate(new_values['entity_type_selection'])

        return new_values


def is_list_of_lists(l):
    return all(isinstance(i, list) for i in l)


def filter_property(prop):
    return [p for p in prop if p != '' and p != '__value__']


def filter_properties(props):
    return [filter_property(prop) for prop in props if len(filter_property(prop)) > 0]


def get_entity_type_selection_schema():
    filter_functions_info = get_filter_functions()

    return Schema({
        'id': Use(int),
        'label': And(str, len),
        Optional('description', default=None): Or(str, None),
        'dataset': {
            'dataset_id': And(str, len),
            'collection_id': And(str, len),
            'timbuctoo_graphql': And(str, len),
        },
        Optional('filter', default=None): Or(None, LogicBox(Schema({
            'property': And(Use(filter_property), len),
            'type': And(str, Use(str.lower), lambda t: t in filter_functions_info.keys()),
            Optional('value'): Or(And(str, len), int),
            Optional('format'): And(str, len),
        }, ignore_extra_keys=True), 'conditions', ('and', 'or'))),
        Optional('limit', default=-1): And(int, lambda n: n > 0 or n == -1),
        Optional('random', default=False): bool,
        Optional('properties', default=list): And(list, is_list_of_lists, Use(filter_properties)),
    }, ignore_extra_keys=True)


def get_linkset_spec_schema(ets_ids):
    matching_methods_info = get_matching_methods()
    transformers_info = get_transformers()

    return Schema({
        'id': Use(int),
        'label': And(str, len),
        Optional('description', default=None): Or(str, None),
        Optional('use_counter', default=True): bool,
        'sources': [EntityTypeSelection(ets_ids)],
        'targets': [EntityTypeSelection(ets_ids)],
        'methods': And(LogicBox(Schema({
            'method': {
                'name': And(str, Use(str.lower), lambda m: m in matching_methods_info.keys()),
                'config': And(dict, MatchingMethodConfig(ets_ids)),
            },
            Optional('sim_method', default={'name': None, 'config': {}, 'normalized': False}): {
                Optional('name', default=None):
                    Or(None, And(str, Use(str.lower), lambda m: m in matching_methods_info.keys())),
                Optional('config', default={}): And(dict, MatchingMethodConfig(ets_ids)),
                Optional('normalized', default=False): bool,
            },
            Optional('fuzzy', default={'t_norm': 'minimum_t_norm', 's_norm': 'maximum_s_norm', 'threshold': 0}): {
                Optional('t_norm', default='minimum_t_norm'):
                    lambda s: s in ('minimum_t_norm', 'product_t_norm', 'lukasiewicz_t_norm',
                                    'drastic_t_norm', 'nilpotent_minimum', 'hamacher_product'),
                Optional('s_norm', default='maximum_s_norm'):
                    lambda s: s in ('maximum_s_norm', 'probabilistic_sum', 'bounded_sum',
                                    'drastic_s_norm', 'nilpotent_maximum', 'einstein_sum'),
                Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
            },
            Optional('list_matching', default={'threshold': 0, 'is_percentage': False}): {
                Optional('threshold', default=0): int,
                Optional('is_percentage', default=False): bool,
            },
            'sources': {
                'properties': {
                    EntityTypeSelection(ets_ids): [{
                        'property': And(Use(filter_property), len),
                        Optional('property_transformer_first', default=False): bool,
                        Optional('transformers', default=list): [{
                            'name': And(str, Use(str.lower), lambda n: n in transformers_info.keys()),
                            'parameters': dict
                        }],
                    }]
                },
                Optional('transformers', default=list): [{
                    'name': And(str, Use(str.lower), lambda n: n in transformers_info.keys()),
                    'parameters': dict
                }],
            },
            'targets': {
                'properties': {
                    EntityTypeSelection(ets_ids): [{
                        'property': And(Use(filter_property), len),
                        Optional('property_transformer_first', default=False): bool,
                        Optional('transformers', default=list): [{
                            'name': And(str, Use(str.lower), lambda n: n in transformers_info.keys()),
                            'parameters': dict
                        }],
                    }]
                },
                Optional('transformers', default=list): [{
                    'name': And(str, Use(str.lower), lambda n: n in transformers_info.keys()),
                    'parameters': dict
                }],
            }
        }, ignore_extra_keys=True), name='conditions', types=(
            'and', 'or', 'minimum_t_norm', 'product_t_norm', 'lukasiewicz_t_norm', 'drastic_t_norm',
            'nilpotent_minimum', 'hamacher_product', 'maximum_s_norm', 'probabilistic_sum',
            'bounded_sum', 'drastic_s_norm', 'nilpotent_maximum', 'einstein_sum'
        ), elements_schema=Schema({
            'type': str,
            'conditions': list,
            Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
        }, ignore_extra_keys=True)), dict),
    }, ignore_extra_keys=True)


def get_lens_spec_schema():
    return Schema({
        'id': Use(int),
        'label': And(str, len),
        Optional('description', default=None): Or(str, None),
        'specs': And(LogicBox(Schema({
            'id': Use(int),
            'type': Or('linkset', 'lens')
        }, ignore_extra_keys=True), name='elements', types=(
            'union', 'intersection', 'difference', 'sym_difference',
            'in_set_and', 'in_set_or', 'in_set_source', 'in_set_target'
        ), elements_schema=Schema({
            'type': str,
            'elements': list,
            Optional('s_norm', default=''):
                lambda s: s in ('', 'maximum_s_norm', 'probabilistic_sum', 'bounded_sum',
                                'drastic_s_norm', 'nilpotent_maximum', 'einstein_sum'),
            Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
        }, ignore_extra_keys=True)), dict),
    }, ignore_extra_keys=True)


def get_view_schema():
    filter_functions_info = get_filter_functions()

    return Schema({
        'id': Use(int),
        'type': Or('linkset', 'lens'),
        Optional('properties', default=[]): [{
            'dataset_id': And(str, len),
            'collection_id': And(str, len),
            'timbuctoo_graphql': And(str, len),
            'properties': And(list, is_list_of_lists, Use(filter_properties)),
        }],
        Optional('filters', default=[]): [{
            'dataset_id': And(str, len),
            'collection_id': And(str, len),
            'timbuctoo_graphql': And(str, len),
            'filter': LogicBox(Schema({
                'property': And(Use(filter_property), len),
                'type': And(str, Use(str.lower), lambda t: t in filter_functions_info.keys()),
                Optional('value'): Or(And(str, len), int),
                Optional('format'): And(str, len),
            }, ignore_extra_keys=True), 'conditions', ('and', 'or')),
        }],
        Optional('prefix_mappings', default={}): dict
    }, ignore_extra_keys=True)


def transform(entity_type_selections_org, linkset_specs_org, lens_specs_org, views_org):
    entity_type_selections, linkset_specs, lens_specs, views, errors = [], [], [], [], []

    for entity_type_selection_org in entity_type_selections_org:
        try:
            entity_type_selections.append(get_entity_type_selection_schema().validate(entity_type_selection_org))
        except SchemaError as e:
            errors.append(e)

    ets_ids = [ets['id'] for ets in entity_type_selections]

    for linkset_spec_org in linkset_specs_org:
        try:
            linkset_specs.append(get_linkset_spec_schema(ets_ids).validate(linkset_spec_org))
        except SchemaError as e:
            errors.append(e)

    for lens_org in lens_specs_org:
        try:
            lens_specs.append(get_lens_spec_schema().validate(lens_org))
        except SchemaError as e:
            errors.append(e)

    for view_org in views_org:
        try:
            views.append(get_view_schema().validate(view_org))
        except SchemaError as e:
            errors.append(e)

    return entity_type_selections, linkset_specs, lens_specs, views, errors
