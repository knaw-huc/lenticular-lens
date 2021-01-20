from ll.data.property_field import PropertyField
from ll.util.helpers import get_json_from_file


class MatchingMethodProperty:
    _transformers = get_json_from_file('transformers.json')

    def __init__(self, data, job, field_type_info, norm_template, norm_properties):
        self._data = data
        self._job = job
        self._field_type_info = field_type_info
        self._norm_template = norm_template
        self._norm_properties = norm_properties

    @property
    def prop_original(self):
        return PropertyField(self._data['property'], job=self._job,
                             transformers=self._get_field_transformers(normalized=False))

    @property
    def prop_normalized(self):
        if not self._norm_template:
            return None

        return PropertyField(self._data['property'], job=self._job,
                             transformers=self._get_field_transformers(normalized=True))

    def _get_field_transformers(self, normalized=False):
        field_transformers = self._data.get('transformers', []).copy()

        for transformer in field_transformers:
            if transformer['name'] in self._transformers:
                transformer['sql_template'] = self._transformers[transformer['name']]
            else:
                raise NameError('Transformer %s is not defined' % transformer['name'])

        if self._field_type_info['type'] == 'number':
            field_transformers.append({
                'sql_template': self._transformers['TO_NUMERIC_IMMUTABLE'],
                'parameters': {}
            })
        elif self._field_type_info['type'] == 'date':
            field_transformers.append({
                'sql_template': self._transformers['TO_DATE_IMMUTABLE'],
                'parameters': {'format': self._field_type_info['parameters']['format']}
            })

        if normalized:
            field_transformers.append({
                'sql_template': self._norm_template,
                'parameters': self._norm_properties
            })

        return field_transformers
