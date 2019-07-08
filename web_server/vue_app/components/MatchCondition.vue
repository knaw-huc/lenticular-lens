<template>
    <div class="border border-dark p-3 mb-3">
        <div class="row justify-content-between">
            <div class="col-auto">
                <div class="row">
                    <label class="h4 col-auto align-self-center">Method</label>
                    <div class="col-auto form-group">
                        <v-select v-model="condition.method_name" @input="handleMethodIndexChange"
                                  v-bind:class="{'is-invalid': errors.includes('method_name')}">
                            <option disabled selected value="">Select a method</option>
                            <option v-for="(method, name) in matching_methods" :value="name">{{ method.label }}</option>
                        </v-select>

                        <div class="invalid-feedback" v-show="errors.includes('method_name')">
                            Please specify a matching method
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-4">
                <div class="row">
                    <div v-for="(item, index) in method_value_template.items" class="col">
                        <div class="form-group">
                            <label>
                                <span>
                                    {{ item.label }}
                                </span>

                                <input v-if="typeof item.type === 'number'"
                                       class="form-control" type="number" step="0.1"
                                       v-model.number="condition.method_value[item.key]"
                                       v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">

                                <select v-if="item.type.hasOwnProperty('type') && item.type.type === 'matching_label'"
                                        class="form-control" v-model="condition.method_value[item.key].value"
                                        v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">
                                    <option disabled selected value="">Select a Mapping</option>
                                    <option v-for="match in $root.$children[0].matches" :value="match.id">{{ match.label }}</option>
                                </select>

                                <select v-if="item.choices"
                                        class="form-control" v-model="condition.method_value[item.key]"
                                        v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">
                                    <option disabled selected value="">Select an option</option>
                                    <option v-for="(choice_value, choice_label) in item.choices"
                                            :value="choice_value">{{ choice_label }}</option>
                                </select>

                                <div class="invalid-feedback" v-show="errors.includes(`method_value_${item.key}`)">
                                    Please specify a valid value
                                </div>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-auto">
                <div class="row justify-content-end">
                    <div class="form-group col-auto">
                        <button-delete @click="$emit('remove')" title="Delete this Method" class="pt-1 pr-0"/>
                    </div>

                    <div class="form-group col-auto">
                        <button-add v-on:click="$emit('add-matching-method')" title="Add Method and Create Group"/>
                    </div>
                </div>
            </div>
        </div>

        <div class="row pl-5 mb-3" v-for="resources_key in ['sources', 'targets']">
            <div class="col">
                <div class="row">
                    <div class="h4 col-auto">{{ resources_key | capitalize }} properties</div>
                    <div v-if="unusedResources[resources_key].length > 0" class="col-auto form-group">
                        <v-select @input="condition[resources_key][$event].push({'property': [$event, '']})">
                            <option value="" disabled selected>Add property for Collection:</option>
                            <option v-for="resource in unusedResources[resources_key]" :value="resource">
                                {{ $root.$children[0].getResourceById(resource).label }}
                            </option>
                        </v-select>
                    </div>
                </div>
                <template v-for="collection_properties in condition[resources_key]">
                    <div v-for="(resource, index) in collection_properties" class="row">
                        <div class="col ml-5 p-3 border-top">
                            <property-component
                                    v-if="resource.property"
                                    :property="resource.property"
                                    @clone="collection_properties.splice(index + 1, 0, {'property': [collection_properties[index]['property'][0], '']})"
                                    @delete="$delete(collection_properties, index)"
                                    @resetProperty="resetProperty(collection_properties, index, $event)"
                                    ref="propertyComponents"
                            />

                            <div class="row">
                                <div class="col-auto h5 pt-1">Transformers</div>

                                <div class="form-group col-auto p-0">
                                    <button-add
                                            @click="$root.$children[0].getOrCreate(resource, 'transformers', []).push('')"
                                            scale="0.7"
                                            title="Add Transformer"
                                    />
                                </div>
                                <div v-for="(transformer, index) in resource.transformers" class="col-auto">
                                    <div class="row">
                                        <div class="form-group col-auto pr-0">
                                            <v-select v-model="resource.transformers[index]"
                                                      v-bind:class="{'is-invalid': errors.includes(`${resources_key}_transformers`)}">
                                                <option value="" selected disabled>Select a function</option>
                                                <option v-for="av_transformer in transformers" :value="av_transformer">{{ av_transformer }}</option>
                                            </v-select>

                                            <div class="invalid-feedback" v-show="errors.includes(`${resources_key}_transformers`)">
                                                Please specify a transformer or remove the transformer
                                            </div>
                                        </div>

                                        <div class="form-group col-auto pl-0">
                                            <button-delete @click="resource.transformers.splice(index, 1)" scale="1.3" class="pt-1"/>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>

                <div class="invalid-feedback d-block">
                    <template v-if="errors.includes(resources_key)">
                        Please specify at least one property
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        computed: {
            method_value_template() {
                if (this.matching_methods.hasOwnProperty(this.condition.method_name))
                    return this.matching_methods[this.condition.method_name];

                return {label: '', items: []};
            },
            unusedResources() {
                let resource_keys = ['sources', 'targets'];
                let unused_resources = {};

                resource_keys.forEach(resource_key => {
                    unused_resources[resource_key] = Object.keys(this.condition[resource_key]).filter(
                        resource_id => this.condition[resource_key][resource_id].length < 1
                    );
                });

                return unused_resources;
            },
        },
        data() {
            return {
                'matching_methods': {
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
                'transformers': ['ecartico_full_name', 'to_date_immutable']
            }
        },
        methods: {
            validateMatchCondition() {
                const methodNameValid = this.validateField('method_name', this.condition.method_name.length > 0);

                let methodValueValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('method_value_'));
                this.method_value_template.items.forEach(value_item => {
                    const value = this.condition.method_value[value_item.key];

                    let valueValid = true;
                    if (value_item.hasOwnProperty('minValue') && (isNaN(parseFloat(value)) || (parseFloat(value) < value_item.minValue)))
                        valueValid = false;
                    if (value_item.hasOwnProperty('maxValue') && (isNaN(parseFloat(value)) || (parseFloat(value) > value_item.maxValue)))
                        valueValid = false;
                    if (value_item.hasOwnProperty('choices') && !Object.values(value_item.choices).includes(value))
                        valueValid = false;
                    if ((this.condition.method_name === 'IS_IN_SET') && (value.value === undefined || value.value === ''))
                        valueValid = false;

                    if (!this.validateField(`method_value_${value_item.key}`, valueValid))
                        methodValueValid = false;
                });

                const propertiesValid = !this.$refs.propertyComponents
                    .map(propertyComponent => propertyComponent.validateProperty())
                    .includes(false);

                let sourcesTargetsValid = true;
                ['sources', 'targets'].forEach(resources_key => {
                    Object.keys(this.condition[resources_key]).forEach(resource_id => {
                        if (!this.validateField(resources_key, this.condition[resources_key][resource_id].length > 0))
                            sourcesTargetsValid = false;

                        this.condition[resources_key][resource_id].forEach(values => {
                            if (values.hasOwnProperty('transformers') && !this.validateField(
                                `${resources_key}_transformers`, !values.transformers.includes('')))
                                sourcesTargetsValid = false;
                        });
                    });
                });

                return methodNameValid && methodValueValid && propertiesValid && sourcesTargetsValid;
            },
            addMatchingField(event) {
                // Obsolete
                if (event) {
                    event.target.blur();
                }

                this.matching_fields_count++;

                let matching_field = {
                    'id': this.matching_fields_count,
                    'value': {
                        'property': [this.match_resource.resource, ''],
                        'transformers': [],
                        'value_type': '',
                        'function_name': '',
                    },
                };

                this.condition.matching_fields.push(matching_field);
            },
            handleMethodIndexChange() {
                this.condition.method_value = {};
                this.method_value_template.items.forEach(value_item => {
                    this.condition.method_value[value_item.key] = value_item.type;
                });
            },
            resetProperty(properties, resource_index, property_index) {
                let property = properties[resource_index].property;
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(properties[resource_index], 'property', new_property);
            },
            searchObjectInArray(haystack, key, value) {
                let result;
                haystack.forEach(item => {
                    if (item[key] === value) {
                        result = item;
                        return false;
                    }
                });

                return result;
            },
        },
        props: ['condition'],
    }
</script>