from schema import Schema, SchemaError, And, Or, Use, Optional
from ll.util.helpers import get_json_from_file

transformers = get_json_from_file('transformers.json')
filter_functions = get_json_from_file('filter_functions.json')
matching_methods = get_json_from_file('matching_methods.json')


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

            logicbox['type'] = data['type'].upper()
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
            'type': And(str, Use(str.lower), lambda t: t in filter_functions.keys()),
            Optional('value'): Or(And(str, len), int),
            Optional('format'): And(str, len),
        }, ignore_extra_keys=True), 'conditions', ('and', 'or'))),
        Optional('limit', default=-1): And(int, lambda n: n > 0 or n == -1),
        Optional('random', default=False): bool,
        Optional('properties', default=list): And(list, is_list_of_lists, Use(filter_properties)),
    }, ignore_extra_keys=True)


def get_linkset_spec_schema(ets_ids):
    return Schema({
        'id': Use(int),
        'label': And(str, len),
        Optional('description', default=None): Or(str, None),
        Optional('use_counter', default=True): bool,
        'sources': [EntityTypeSelection(ets_ids)],
        'targets': [EntityTypeSelection(ets_ids)],
        'methods': And(LogicBox(Schema({
            'method': {
                'name': And(str, Use(str.upper), lambda m: m in matching_methods.keys()),
                'config': And(dict, MatchingMethodConfig(ets_ids)),
            },
            Optional('sim_method', default={'name': None, 'config': {}, 'normalized': False}): {
                Optional('name', default=None):
                    Or(None, And(str, Use(str.upper), lambda m: m in matching_methods.keys())),
                Optional('config', default={}): And(dict, MatchingMethodConfig(ets_ids)),
                Optional('normalized', default=False): bool,
            },
            Optional('fuzzy', default={'t_norm': 'MINIMUM_T_NORM', 't_conorm': 'MAXIMUM_T_CONORM', 'threshold': 0}): {
                Optional('t_norm', default='MINIMUM_T_NORM'):
                    lambda s: s in ('MINIMUM_T_NORM', 'PRODUCT_T_NORM', 'LUKASIEWICZ_T_NORM',
                                    'DRASTIC_T_NORM', 'NILPOTENT_MINIMUM', 'HAMACHER_PRODUCT'),
                Optional('t_conorm', default='MAXIMUM_T_CONORM'):
                    lambda s: s in ('MAXIMUM_T_CONORM', 'PROBABILISTIC_SUM', 'BOUNDED_SUM',
                                    'DRASTIC_T_CONORM', 'NILPOTENT_MAXIMUM', 'EINSTEIN_SUM'),
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
                            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
                            'parameters': dict
                        }],
                    }]
                },
                Optional('transformers', default=list): [{
                    'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
                    'parameters': dict
                }],
            },
            'targets': {
                'properties': {
                    EntityTypeSelection(ets_ids): [{
                        'property': And(Use(filter_property), len),
                        Optional('property_transformer_first', default=False): bool,
                        Optional('transformers', default=list): [{
                            'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
                            'parameters': dict
                        }],
                    }]
                },
                Optional('transformers', default=list): [{
                    'name': And(str, Use(str.upper), lambda n: n in transformers.keys()),
                    'parameters': dict
                }],
            }
        }, ignore_extra_keys=True), name='conditions', types=(
            'and', 'or', 'minimum_t_norm', 'product_t_norm', 'lukasiewicz_t_norm', 'drastic_t_norm',
            'nilpotent_minimum', 'hamacher_product', 'maximum_t_conorm', 'probabilistic_sum',
            'bounded_sum', 'drastic_t_conorm', 'nilpotent_maximum', 'einstein_sum'
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
            'union', 'intersection', 'difference', 'sym_difference', 'in_set_and', 'in_set_or'
        ), elements_schema=Schema({
            'type': str,
            'elements': list,
            Optional('t_conorm', default=''):
                lambda s: s in ('', 'MAXIMUM_T_CONORM', 'PROBABILISTIC_SUM', 'BOUNDED_SUM',
                                'DRASTIC_T_CONORM', 'NILPOTENT_MAXIMUM', 'EINSTEIN_SUM'),
            Optional('threshold', default=0): Or(float, Use(lambda t: 0)),
        }, ignore_extra_keys=True)), dict),
    }, ignore_extra_keys=True)


def get_view_schema():
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
                'type': And(str, Use(str.lower), lambda t: t in filter_functions.keys()),
                Optional('value'): Or(And(str, len), int),
                Optional('format'): And(str, len),
            }, ignore_extra_keys=True), 'conditions', ('and', 'or')),
        }]
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
