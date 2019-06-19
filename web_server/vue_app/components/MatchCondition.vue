<template>
    <div class="border border-dark p-3 mb-3">
        <div class="row justify-content-between">
            <div class="col-auto">
                <div class="row">
                    <label class="h4 col-auto align-self-center">Method</label>
                    <div class="col-auto form-group">
                        <v-select v-model="condition.method_name" @input="handleMethodIndexChange">
                            <option disabled selected value="">Select a method</option>
                            <option v-for="(method, name) in matching_methods" :value="name">{{ method.label }}</option>
                        </v-select>
                    </div>
                </div>
            </div>

            <div v-if="typeof condition.method_value === 'object'" class="col-4">
                <div v-if="condition.method_value === Object(condition.method_value)" class="row">
                    <div v-for="(item, index) in condition.method_value" class="col">
                        <div class="form-group">
                            <label>
                                <template v-if="Object.prototype.toString.call(condition.method_value) === '[object Object]'">
                                    {{ searchObjectInArray(method_value_template.items, 'key', index).label }}
                                </template>
                                <template v-else>Value {{ index + 1 }}</template>

                                <input v-if="typeof item === 'number' && (!method_value_template.items || !searchObjectInArray(method_value_template.items, 'key', index).choices)" class="form-control" type="number" step="any" v-model.number="condition.method_value[index]">

                                <select v-if="item.type === 'matching_label'" class="form-control" v-model="condition.method_value[index].value">
                                    <option disabled selected value="">Select a Mapping</option>
                                    <option v-for="match in $root.$children[0].matches" :value="match.id">{{ match.label }}</option>
                                </select>

                                <select v-if="method_value_template.items && searchObjectInArray(method_value_template.items, 'key', index).choices" class="form-control" v-model="condition.method_value[index]">
                                    <option disabled selected value="">Select an option</option>
                                    <option v-for="(choice_value, choice_label) in searchObjectInArray(method_value_template.items, 'key', index).choices" :value="choice_value">{{ choice_label }}</option>
                                </select>
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
                                            <v-select v-model="resource.transformers[index]">
                                                <option value="" selected disabled>Select a function</option>
                                                <option v-for="av_transformer in transformers" :value="av_transformer">{{ av_transformer }}</option>
                                            </v-select>
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
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        computed: {
            method_value_template() {
                return this.matching_methods[this.condition.method_name].value;
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
                        'value': ''
                    },
                    'LL_SOUNDEX': {
                        'label': 'Similar Soundex',
                        'value': {
                            'items': [
                                {
                                    'key': 'threshold',
                                    'label': 'Similarity threshold',
                                    'type': 0.7,
                                    'minValue': 0,
                                    'maxValue': 1,
                                },
                            ]
                        }
                    },
                    'BLOOTHOOFT_REDUCT': {
                        'label': 'Same Bloothooft Reduction',
                        'value': {
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
                                },
                            ]
                        }
                    },
                    'BLOOTHOOFT_REDUCT_APPROX': {
                        'label': 'Similar Bloothooft Reduction',
                        'value': {
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
                                },
                            ]
                        }
                    },
                    'TRIGRAM_DISTANCE': {
                        'label': 'Trigram distance',
                        'value': {
                            'listItems': {
                                'type': 0.30,
                                'minValue': 0,
                                'maxValue': 1,
                            },
                        }
                    },
                    'LEVENSHTEIN': {
                        'label': 'Levenshtein distance',
                        'value': {
                            'listItems': {
                                'type': 1,
                                'minValue': 0,
                            },
                        }
                    },
                    'TIME_DELTA': {
                        'label': 'Time Delta',
                        'value': {
                            'items':[
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
                        }
                    },
                    'SAME_YEAR_MONTH': {
                        'label': 'Same Year/Month',
                        'value': {
                            'items': [
                                {
                                    'key': 'date_part',
                                    'label': 'Same',
                                    'type': '',
                                    'choices': {
                                        'Year': 'year',
                                        'Month': 'month',
                                        'Year and Month': 'year_month',
                                    }
                                }
                            ]
                        }
                    },
                    'DISTANCE_IS_BETWEEN': {
                        'label': 'Distance is between',
                        'value': {
                            'listItems': {
                                'type': 0,
                                'maxItems': 2,
                                'minItems': 2,
                            }
                        }
                    },
                    'IS_IN_SET': {
                        'label': 'Is a Match in Set:',
                        'value': {
                            'listItems': {
                                'type': {
                                    'type': 'matching_label',
                                },
                                'maxItems': 1,
                                'minItems': 1,
                            }
                        }
                    }
                },
                'transformers': ['ecartico_full_name', 'to_date_immutable']
            }
        },
        methods: {
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
                if (typeof this.method_value_template === 'string') {
                    this.condition.method_value = this.method_value_template;
                }
                else if (this.method_value_template.hasOwnProperty('listItems')) {
                    this.condition.method_value = [];
                    for (let i = 0; i < (this.method_value_template.listItems.minItems || 1); i++) {
                        this.condition.method_value.push(this.method_value_template.listItems.type);
                    }
                }
                else {
                    this.condition.method_value = {};
                    this.method_value_template.items.forEach(value_item => {
                        this.condition.method_value[value_item.key] = value_item.type;
                    });
                }
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